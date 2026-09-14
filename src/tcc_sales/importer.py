from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from .dataset import DataValidationError, normalize_product, parse_iso_date, parse_number, read_csv


def connect(database: Path) -> sqlite3.Connection:
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA foreign_keys = ON")
    schema = Path(__file__).resolve().parents[2] / "db/schema.sql"
    connection.executescript(schema.read_text(encoding="utf-8"))
    return connection


def dataset_hash(folder: Path) -> str:
    digest = hashlib.sha256()
    for filename in ("accounts.csv", "products.csv", "sales_teams.csv", "sales_pipeline.csv"):
        digest.update(filename.encode())
        digest.update((folder / filename).read_bytes())
    return digest.hexdigest()


def validate(folder: Path) -> dict[str, list[dict[str, object]]]:
    raw_accounts = read_csv(folder, "accounts.csv")
    raw_products = read_csv(folder, "products.csv")
    raw_agents = read_csv(folder, "sales_teams.csv")
    raw_opportunities = read_csv(folder, "sales_pipeline.csv")
    errors: list[str] = []

    def require_unique(rows: list[dict[str, str]], field: str, label: str):
        seen: set[str] = set()
        for number, row in enumerate(rows, start=2):
            value = row[field]
            if not value:
                errors.append(f"{label}, linha {number}, campo {field}: valor obrigatório ausente")
            elif value in seen:
                errors.append(f"{label}, linha {number}, campo {field}: valor duplicado '{value}'")
            seen.add(value)

    require_unique(raw_accounts, "account", "accounts.csv")
    require_unique(raw_products, "product", "products.csv")
    require_unique(raw_agents, "sales_agent", "sales_teams.csv")
    require_unique(raw_opportunities, "opportunity_id", "sales_pipeline.csv")

    accounts: list[dict[str, object]] = []
    for number, row in enumerate(raw_accounts, start=2):
        accounts.append({
            **row,
            "year_established": parse_number(row["year_established"], "year_established", number, errors, integer=True),
            "revenue": parse_number(row["revenue"], "revenue", number, errors),
            "employees": parse_number(row["employees"], "employees", number, errors, integer=True),
        })

    products: list[dict[str, object]] = []
    for number, row in enumerate(raw_products, start=2):
        products.append({**row, "sales_price": parse_number(row["sales_price"], "sales_price", number, errors)})

    account_keys = {str(row["account"]) for row in accounts}
    product_keys = {str(row["product"]) for row in products}
    agent_keys = {row["sales_agent"] for row in raw_agents}
    opportunities: list[dict[str, object]] = []
    for number, row in enumerate(raw_opportunities, start=2):
        stage = row["deal_stage"]
        product = normalize_product(row["product"])
        engage_date = parse_iso_date(row["engage_date"], "engage_date", number, errors)
        close_date = parse_iso_date(row["close_date"], "close_date", number, errors)
        close_value = parse_number(row["close_value"], "close_value", number, errors)
        if stage not in {"Prospecting", "Engaging", "Won", "Lost"}:
            errors.append(f"sales_pipeline.csv, linha {number}, campo deal_stage: estágio inválido '{stage}'")
        if row["sales_agent"] not in agent_keys:
            errors.append(f"sales_pipeline.csv, linha {number}, campo sales_agent: referência desconhecida '{row['sales_agent']}'")
        if product not in product_keys:
            errors.append(f"sales_pipeline.csv, linha {number}, campo product: referência desconhecida '{row['product']}'")
        if row["account"] and row["account"] not in account_keys:
            errors.append(f"sales_pipeline.csv, linha {number}, campo account: referência desconhecida '{row['account']}'")
        if stage == "Prospecting" and any((engage_date, close_date, close_value is not None)):
            errors.append(f"sales_pipeline.csv, linha {number}: Prospecting não deve ter engajamento ou fechamento")
        if stage == "Engaging" and (not engage_date or close_date or close_value is not None):
            errors.append(f"sales_pipeline.csv, linha {number}: Engaging exige engage_date e não deve ter fechamento")
        if stage in {"Won", "Lost"} and (not engage_date or not close_date or close_value is None):
            errors.append(f"sales_pipeline.csv, linha {number}: negócio encerrado exige engage_date, close_date e close_value")
        if engage_date and close_date and close_date < engage_date:
            errors.append(f"sales_pipeline.csv, linha {number}, campo close_date: anterior a engage_date")
        opportunities.append({
            **row,
            "source_product": row["product"],
            "product": product,
            "engage_date": engage_date,
            "close_date": close_date,
            "close_value": close_value,
        })
    if errors:
        raise DataValidationError(errors[:100])
    return {"accounts": accounts, "products": products, "agents": raw_agents, "opportunities": opportunities}


def import_folder(connection: sqlite3.Connection, folder: Path, tenant_id: str = "demo", tenant_name: str = "MavenTech Demo") -> dict[str, object]:
    fingerprint = dataset_hash(folder)
    previous = connection.execute(
        "SELECT row_count FROM import_runs WHERE tenant_id = ? AND dataset_hash = ? AND status = 'succeeded'",
        (tenant_id, fingerprint),
    ).fetchone()
    if previous:
        return {"status": "skipped", "reason": "dataset already imported", "row_count": previous[0], "dataset_hash": fingerprint}
    data = validate(folder)
    with connection:
        connection.execute("INSERT INTO tenants(tenant_id, name) VALUES (?, ?) ON CONFLICT(tenant_id) DO UPDATE SET name=excluded.name", (tenant_id, tenant_name))
        connection.executemany(
            "INSERT INTO accounts VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(tenant_id,account) DO UPDATE SET sector=excluded.sector, year_established=excluded.year_established, revenue_musd=excluded.revenue_musd, employees=excluded.employees, office_location=excluded.office_location, subsidiary_of=excluded.subsidiary_of",
            [(tenant_id, r["account"], r["sector"], r["year_established"], r["revenue"], r["employees"], r["office_location"], r["subsidiary_of"] or None) for r in data["accounts"]],
        )
        connection.executemany(
            "INSERT INTO products VALUES (?,?,?,?) ON CONFLICT(tenant_id,product) DO UPDATE SET series=excluded.series, sales_price=excluded.sales_price",
            [(tenant_id, r["product"], r["series"], r["sales_price"]) for r in data["products"]],
        )
        connection.executemany(
            "INSERT INTO sales_agents VALUES (?,?,?,?) ON CONFLICT(tenant_id,sales_agent) DO UPDATE SET manager=excluded.manager, regional_office=excluded.regional_office",
            [(tenant_id, r["sales_agent"], r["manager"], r["regional_office"]) for r in data["agents"]],
        )
        connection.executemany(
            "INSERT INTO opportunities VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(tenant_id,opportunity_id) DO UPDATE SET sales_agent=excluded.sales_agent, product=excluded.product, source_product=excluded.source_product, account=excluded.account, deal_stage=excluded.deal_stage, engage_date=excluded.engage_date, close_date=excluded.close_date, close_value=excluded.close_value",
            [(tenant_id, r["opportunity_id"], r["sales_agent"], r["product"], r["source_product"], r["account"] or None, r["deal_stage"], r["engage_date"], r["close_date"], r["close_value"]) for r in data["opportunities"]],
        )
        connection.execute(
            "INSERT INTO import_runs(tenant_id,dataset_hash,row_count,status) VALUES (?,?,?,'succeeded')",
            (tenant_id, fingerprint, len(data["opportunities"])),
        )
    return {"status": "imported", "row_count": len(data["opportunities"]), "dataset_hash": fingerprint}
