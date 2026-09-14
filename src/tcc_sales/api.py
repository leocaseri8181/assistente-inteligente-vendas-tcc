from __future__ import annotations

import os
import sqlite3
import tempfile
from contextlib import closing
from datetime import date
from pathlib import Path
from typing import Annotated, Any, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Query, Request, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .auth import AuthServiceError, SupabaseAuthClient
from .dataset import DataValidationError
from .importer import dataset_hash, import_folder, validate
from .metrics import filter_options, monthly_trend, open_opportunities, product_breakdown, summary, tenant_exists

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
UPLOAD_FIELDS = {
    "accounts.csv": "accounts",
    "products.csv": "products",
    "sales_teams.csv": "sales_teams",
    "sales_pipeline.csv": "sales_pipeline",
}
ACCESS_COOKIE = "tcc_access_token"
REFRESH_COOKIE = "tcc_refresh_token"

load_dotenv(ROOT / ".env")


class PeriodParams(BaseModel):
    model_config = {"extra": "forbid"}
    tenant_id: str = Field("demo", min_length=1, max_length=64)
    date_from: date | None = None
    date_to: date | None = None


class OpportunityParams(BaseModel):
    model_config = {"extra": "forbid"}
    tenant_id: str = Field("demo", min_length=1, max_length=64)
    stage: Literal["Engaging", "Prospecting"] | None = None
    product: str | None = Field(None, max_length=100)
    manager: str | None = Field(None, max_length=100)
    agent: str | None = Field(None, max_length=100)
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class LoginPayload(BaseModel):
    model_config = {"extra": "forbid"}
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: str = Field(min_length=8, max_length=128)


class SignupPayload(LoginPayload):
    company_name: str = Field(min_length=2, max_length=120)


def create_app(
    database_path: Path | None = None,
    *,
    auth_client: Any | None = None,
    auth_required: bool | None = None,
    data_backend: str | None = None,
) -> FastAPI:
    selected_database = Path(database_path or os.getenv("TCC_DATABASE", ROOT / "data/tcc.sqlite3"))
    app = FastAPI(title="Assistente de Análise Comercial", version="0.1.0")
    app.state.database_path = selected_database
    if auth_client is None and database_path is None:
        supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
        publishable_key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
        if supabase_url and publishable_key:
            auth_client = SupabaseAuthClient(supabase_url, publishable_key)
    app.state.auth_client = auth_client
    app.state.auth_required = bool(auth_client) if auth_required is None else auth_required
    app.state.data_backend = data_backend or (os.getenv("TCC_DATA_BACKEND", "sqlite") if database_path is None else "sqlite")
    if app.state.data_backend not in {"sqlite", "supabase"}:
        raise ValueError("TCC_DATA_BACKEND must be 'sqlite' or 'supabase'")
    if app.state.data_backend == "supabase" and not app.state.auth_client:
        raise ValueError("Supabase data backend requires an authentication client")
    app.mount("/assets", StaticFiles(directory=WEB), name="assets")

    def connection():
        db = sqlite3.connect(app.state.database_path)
        db.execute("PRAGMA foreign_keys = ON")
        return db

    def require_tenant(db, tenant_id):
        if not tenant_exists(db, tenant_id):
            raise HTTPException(status_code=404, detail="Empresa não encontrada")

    def require_user(request: Request) -> dict[str, Any] | None:
        if not app.state.auth_required:
            return None
        access_token = request.cookies.get(ACCESS_COOKIE)
        if not access_token:
            raise HTTPException(status_code=401, detail="Entre para acessar o painel.")
        try:
            return app.state.auth_client.user(access_token)
        except AuthServiceError as error:
            status_code = 503 if error.status_code >= 500 else 401
            raise HTTPException(status_code=status_code, detail=str(error)) from error

    def require_admin(request: Request) -> dict[str, Any] | None:
        context = require_membership(request)
        if context is None:
            return None
        if context["membership"].get("role") not in {"owner", "admin"}:
            raise HTTPException(status_code=403, detail="Somente responsáveis da empresa podem importar dados.")
        return context

    def require_membership(request: Request) -> dict[str, Any] | None:
        user = require_user(request)
        if user is None:
            return None
        access_token = request.cookies.get(ACCESS_COOKIE, "")
        try:
            memberships = app.state.auth_client.memberships(access_token)
        except AuthServiceError as error:
            raise HTTPException(status_code=error.status_code, detail=str(error)) from error
        if not memberships:
            raise HTTPException(status_code=403, detail="Sua conta ainda não está associada a uma empresa.")
        return {"user": user, "membership": memberships[0], "access_token": access_token}

    def sales_analytics(request: Request, date_from: date | None, date_to: date | None) -> dict[str, Any]:
        context = require_membership(request)
        assert context is not None
        try:
            return app.state.auth_client.rpc(
                context["access_token"],
                "sales_analytics",
                {
                    "p_organization_id": context["membership"]["organization_id"],
                    "p_date_from": _date(date_from),
                    "p_date_to": _date(date_to),
                },
            )
        except AuthServiceError as error:
            raise HTTPException(status_code=error.status_code, detail=str(error)) from error

    def session_payload(access_token: str) -> dict[str, Any]:
        user = app.state.auth_client.user(access_token)
        memberships = app.state.auth_client.memberships(access_token)
        primary = memberships[0] if memberships else None
        return {
            "auth_enabled": True,
            "authenticated": True,
            "data_backend": app.state.data_backend,
            "user": {"id": user.get("id"), "email": user.get("email")},
            "membership": primary,
        }

    def set_session_cookies(response: Response, result: dict[str, Any], request: Request) -> None:
        access_token = str(result.get("access_token") or "")
        refresh_token = str(result.get("refresh_token") or "")
        if not access_token or not refresh_token:
            return
        secure = request.url.scheme == "https" or os.getenv("TCC_SECURE_COOKIES") == "1"
        response.set_cookie(
            ACCESS_COOKIE, access_token, httponly=True, secure=secure, samesite="lax", path="/",
            max_age=int(result.get("expires_in") or 3600),
        )
        response.set_cookie(
            REFRESH_COOKIE, refresh_token, httponly=True, secure=secure, samesite="lax", path="/",
            max_age=60 * 60 * 24 * 30,
        )

    def clear_session_cookies(response: Response) -> None:
        response.delete_cookie(ACCESS_COOKIE, path="/")
        response.delete_cookie(REFRESH_COOKIE, path="/")

    @app.get("/", include_in_schema=False)
    def dashboard():
        return FileResponse(WEB / "index.html")

    @app.get("/api/auth/session")
    def auth_session(request: Request):
        if not app.state.auth_required:
            return {
                "auth_enabled": False,
                "authenticated": True,
                "mode": "local_demo",
                "data_backend": app.state.data_backend,
            }
        access_token = request.cookies.get(ACCESS_COOKIE)
        if not access_token:
            return {
                "auth_enabled": True,
                "authenticated": False,
                "data_backend": app.state.data_backend,
            }
        try:
            return session_payload(access_token)
        except AuthServiceError as error:
            refresh_token = request.cookies.get(REFRESH_COOKIE)
            if refresh_token and error.status_code < 500:
                try:
                    refreshed = app.state.auth_client.refresh(refresh_token)
                    payload = session_payload(str(refreshed.get("access_token") or ""))
                    response = JSONResponse(payload)
                    set_session_cookies(response, refreshed, request)
                    return response
                except AuthServiceError:
                    pass
            response = JSONResponse({
                "auth_enabled": True,
                "authenticated": False,
                "data_backend": app.state.data_backend,
            })
            clear_session_cookies(response)
            return response

    @app.post("/api/auth/signup")
    def auth_signup(payload: SignupPayload, request: Request):
        if not app.state.auth_client:
            raise HTTPException(status_code=503, detail="Autenticação ainda não configurada.")
        try:
            result = app.state.auth_client.signup(payload.email, payload.password, payload.company_name)
        except AuthServiceError as error:
            raise HTTPException(status_code=error.status_code, detail=str(error)) from error
        if not result.get("access_token"):
            return {"authenticated": False, "confirmation_required": True}
        response = JSONResponse({"authenticated": True})
        set_session_cookies(response, result, request)
        return response

    @app.post("/api/auth/login")
    def auth_login(payload: LoginPayload, request: Request):
        if not app.state.auth_client:
            raise HTTPException(status_code=503, detail="Autenticação ainda não configurada.")
        try:
            result = app.state.auth_client.login(payload.email, payload.password)
        except AuthServiceError as error:
            raise HTTPException(status_code=error.status_code, detail=str(error)) from error
        response = JSONResponse({"authenticated": True})
        set_session_cookies(response, result, request)
        return response

    @app.post("/api/auth/logout")
    def auth_logout(request: Request):
        access_token = request.cookies.get(ACCESS_COOKIE)
        if access_token and app.state.auth_client:
            try:
                app.state.auth_client.logout(access_token)
            except AuthServiceError:
                pass
        response = JSONResponse({"authenticated": False})
        clear_session_cookies(response)
        return response

    @app.get("/api/health")
    def health():
        try:
            with closing(connection()) as db:
                db.execute("SELECT 1").fetchone()
            return {"status": "ok"}
        except sqlite3.Error as error:
            raise HTTPException(status_code=503, detail="Banco indisponível") from error

    @app.get("/api/summary")
    def get_summary(request: Request, params: Annotated[PeriodParams, Query()]):
        if app.state.data_backend == "supabase":
            return sales_analytics(request, params.date_from, params.date_to).get("summary", {})
        require_user(request)
        with closing(connection()) as db:
            require_tenant(db, params.tenant_id)
            try:
                return summary(db, params.tenant_id, _date(params.date_from), _date(params.date_to))
            except ValueError as error:
                raise HTTPException(status_code=422, detail=str(error)) from error

    @app.get("/api/trends")
    def get_trends(request: Request, params: Annotated[PeriodParams, Query()]):
        if app.state.data_backend == "supabase":
            return sales_analytics(request, params.date_from, params.date_to).get("trends", [])
        require_user(request)
        with closing(connection()) as db:
            require_tenant(db, params.tenant_id)
            return monthly_trend(db, params.tenant_id, _date(params.date_from), _date(params.date_to))

    @app.get("/api/products")
    def get_products(request: Request, params: Annotated[PeriodParams, Query()]):
        if app.state.data_backend == "supabase":
            return sales_analytics(request, params.date_from, params.date_to).get("products", [])
        require_user(request)
        with closing(connection()) as db:
            require_tenant(db, params.tenant_id)
            return product_breakdown(db, params.tenant_id, _date(params.date_from), _date(params.date_to))

    @app.get("/api/options")
    def get_options(request: Request, tenant_id: Annotated[str, Query(min_length=1, max_length=64)] = "demo"):
        if app.state.data_backend == "supabase":
            return sales_analytics(request, None, None).get("options", {})
        require_user(request)
        with closing(connection()) as db:
            require_tenant(db, tenant_id)
            return filter_options(db, tenant_id)

    @app.get("/api/opportunities")
    def get_opportunities(request: Request, params: Annotated[OpportunityParams, Query()]):
        if app.state.data_backend == "supabase":
            context = require_membership(request)
            assert context is not None
            try:
                return app.state.auth_client.rpc(
                    context["access_token"],
                    "sales_open_opportunities",
                    {
                        "p_organization_id": context["membership"]["organization_id"],
                        "p_stage": params.stage,
                        "p_product": params.product,
                        "p_manager": params.manager,
                        "p_agent": params.agent,
                        "p_limit": params.limit,
                        "p_offset": params.offset,
                    },
                )
            except AuthServiceError as error:
                raise HTTPException(status_code=error.status_code, detail=str(error)) from error
        require_user(request)
        with closing(connection()) as db:
            require_tenant(db, params.tenant_id)
            return open_opportunities(
                db, params.tenant_id, stage=params.stage, product=params.product, manager=params.manager,
                agent=params.agent, limit=params.limit, offset=params.offset,
            )

    @app.post("/api/imports")
    async def import_csv_files(
        request: Request,
        accounts: Annotated[UploadFile, File(description="Cadastro de contas em CSV")],
        products: Annotated[UploadFile, File(description="Cadastro de produtos em CSV")],
        sales_teams: Annotated[UploadFile, File(description="Equipe comercial em CSV")],
        sales_pipeline: Annotated[UploadFile, File(description="Oportunidades em CSV")],
        tenant_id: Annotated[str, Form(min_length=1, max_length=64)] = "demo",
        tenant_name: Annotated[str, Form(min_length=1, max_length=120)] = "Empresa demonstrativa",
    ):
        admin_context = require_admin(request)
        uploads = {
            "accounts.csv": accounts,
            "products.csv": products,
            "sales_teams.csv": sales_teams,
            "sales_pipeline.csv": sales_pipeline,
        }
        received: list[dict[str, object]] = []
        try:
            with tempfile.TemporaryDirectory(prefix="tcc-sales-import-") as temporary:
                folder = Path(temporary)
                for expected_name, upload in uploads.items():
                    original_name = Path(upload.filename or "").name
                    if Path(original_name).suffix.casefold() != ".csv":
                        raise HTTPException(status_code=415, detail=f"{expected_name}: selecione um arquivo .csv")
                    content = await upload.read(MAX_UPLOAD_BYTES + 1)
                    if not content:
                        raise HTTPException(status_code=422, detail=f"{expected_name}: arquivo vazio")
                    if len(content) > MAX_UPLOAD_BYTES:
                        raise HTTPException(status_code=413, detail=f"{expected_name}: limite de 10 MB excedido")
                    if b"\x00" in content[:4096]:
                        raise HTTPException(status_code=422, detail=f"{expected_name}: conteúdo não parece ser CSV textual")
                    (folder / expected_name).write_bytes(content)
                    received.append({"field": UPLOAD_FIELDS[expected_name], "filename": original_name, "bytes": len(content)})

                if app.state.data_backend == "supabase":
                    assert admin_context is not None
                    normalized = validate(folder)
                    try:
                        result = app.state.auth_client.rpc(
                            admin_context["access_token"],
                            "import_sales_dataset",
                            {
                                "p_organization_id": admin_context["membership"]["organization_id"],
                                "p_dataset_hash": dataset_hash(folder),
                                "p_payload": _json_ready(normalized),
                            },
                        )
                    except AuthServiceError as error:
                        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
                else:
                    with closing(connection()) as db:
                        result = import_folder(db, folder, tenant_id=tenant_id, tenant_name=tenant_name)
                return {**result, "files": received}
        except DataValidationError as error:
            raise HTTPException(
                status_code=422,
                detail={"message": "Os arquivos não passaram pela validação.", "errors": error.errors},
            ) from error
        except UnicodeDecodeError as error:
            raise HTTPException(status_code=422, detail="Os CSVs devem usar codificação UTF-8.") from error
        except sqlite3.Error as error:
            raise HTTPException(status_code=503, detail="Não foi possível registrar o lote no banco.") from error
        finally:
            for upload in uploads.values():
                await upload.close()

    return app


def _date(value: date | None) -> str | None:
    return value.isoformat() if value else None


def _json_ready(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


app = create_app()
