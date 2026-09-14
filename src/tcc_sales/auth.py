from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx2


class AuthServiceError(RuntimeError):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(message)


@dataclass(frozen=True)
class SupabaseAuthClient:
    url: str
    publishable_key: str
    timeout_seconds: float = 10.0

    def _request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        headers = {"apikey": self.publishable_key, "Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            with httpx2.Client(base_url=self.url, timeout=self.timeout_seconds, headers=headers) as client:
                response = client.request(method, path, json=json, params=params)
        except httpx2.RequestError as error:
            raise AuthServiceError(
                503,
                "O servidor local não conseguiu acessar o Supabase. Verifique a conexão e tente novamente.",
            ) from error

        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if response.status_code >= 400:
            message = _safe_auth_message(response.status_code, payload)
            raise AuthServiceError(response.status_code, message)
        return payload

    def signup(self, email: str, password: str, company_name: str) -> dict[str, Any]:
        result = self._request(
            "POST",
            "/auth/v1/signup",
            json={"email": email, "password": password, "data": {"company_name": company_name}},
        )
        return _as_dict(result)

    def login(self, email: str, password: str) -> dict[str, Any]:
        result = self._request(
            "POST",
            "/auth/v1/token",
            params={"grant_type": "password"},
            json={"email": email, "password": password},
        )
        return _as_dict(result)

    def user(self, access_token: str) -> dict[str, Any]:
        return _as_dict(self._request("GET", "/auth/v1/user", token=access_token))

    def refresh(self, refresh_token: str) -> dict[str, Any]:
        return _as_dict(
            self._request(
                "POST",
                "/auth/v1/token",
                params={"grant_type": "refresh_token"},
                json={"refresh_token": refresh_token},
            )
        )

    def memberships(self, access_token: str) -> list[dict[str, Any]]:
        result = self._request(
            "GET",
            "/rest/v1/organization_members",
            token=access_token,
            params={
                "select": "organization_id,role,organizations(id,name,slug)",
                "order": "created_at.asc",
                "limit": "10",
            },
        )
        return result if isinstance(result, list) else []

    def rpc(self, access_token: str, function_name: str, parameters: dict[str, Any]) -> dict[str, Any]:
        result = self._request(
            "POST",
            f"/rest/v1/rpc/{function_name}",
            token=access_token,
            json=parameters,
        )
        return _as_dict(result)

    def logout(self, access_token: str) -> None:
        self._request("POST", "/auth/v1/logout", token=access_token)


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_auth_message(status_code: int, payload: object) -> str:
    data = payload if isinstance(payload, dict) else {}
    code = str(data.get("error_code") or data.get("code") or "")
    if code == "invalid_credentials" or (status_code == 401 and code != "email_not_confirmed"):
        return "E-mail ou senha inválidos, ou e-mail ainda não confirmado."
    if code in {"user_already_exists", "email_exists"}:
        return "Não foi possível concluir o cadastro. Tente entrar ou recuperar o acesso."
    if code in {"email_address_invalid", "validation_failed"}:
        return "Informe um endereço de e-mail válido."
    if code in {"email_not_confirmed"}:
        return "Confirme o e-mail recebido antes de entrar."
    if code == "over_email_send_rate_limit":
        return (
            "O limite de e-mails de confirmação do projeto foi atingido. "
            "Aguarde cerca de uma hora antes de tentar novamente."
        )
    if code == "over_request_rate_limit":
        return "Muitas solicitações deste dispositivo. Aguarde alguns minutos e tente novamente."
    if status_code == 429:
        return "O Supabase aplicou um limite temporário. Aguarde antes de tentar novamente."
    if status_code >= 500:
        return "Serviço de autenticação temporariamente indisponível."
    message = data.get("msg") or data.get("message") or data.get("error_description")
    return str(message) if message else "Não foi possível concluir a autenticação."
