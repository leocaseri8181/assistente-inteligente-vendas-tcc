from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

PRODUCT_ALIASES = {"GTXPro": "GTX Pro"}

REQUIRED_COLUMNS = {
    "accounts.csv": ("account", "sector", "year_established", "revenue", "employees", "office_location", "subsidiary_of"),
    "products.csv": ("product", "series", "sales_price"),
    "sales_teams.csv": ("sales_agent", "manager", "regional_office"),
    "sales_pipeline.csv": ("opportunity_id", "sales_agent", "product", "account", "deal_stage", "engage_date", "close_date", "close_value"),
}


class DataValidationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("\n".join(errors))


def read_csv(folder: Path, filename: str) -> list[dict[str, str]]:
    path = folder / filename
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        actual = tuple(reader.fieldnames or ())
        expected = REQUIRED_COLUMNS[filename]
        if actual != expected:
            raise DataValidationError([f"{filename}: cabeçalho esperado {expected}; recebido {actual}"])
        return [{key: (value or "").strip() for key, value in row.items()} for row in reader]


def parse_iso_date(value: str, field: str, row_number: int, errors: list[str]) -> str | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        errors.append(f"linha {row_number}, campo {field}: data inválida '{value}' (esperado AAAA-MM-DD)")
        return None


def parse_number(value: str, field: str, row_number: int, errors: list[str], *, integer: bool = False) -> float | int | None:
    if not value:
        return None
    try:
        return int(value) if integer else float(value)
    except ValueError:
        errors.append(f"linha {row_number}, campo {field}: número inválido '{value}'")
        return None


def normalize_product(value: str) -> str:
    return PRODUCT_ALIASES.get(value, value)

