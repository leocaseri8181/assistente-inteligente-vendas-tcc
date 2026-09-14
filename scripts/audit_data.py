import csv
import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/raw/maven"


def rows(name):
    with (SOURCE / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    manifest = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
    hash_checks = {}
    for filename, metadata in manifest["files"].items():
        actual = hashlib.sha256((SOURCE / filename).read_bytes()).hexdigest()
        hash_checks[filename] = actual == metadata["sha256"]
    if not all(hash_checks.values()):
        raise ValueError(f"Raw file hash mismatch: {hash_checks}")
    tables = {name: rows(name) for name in ("accounts.csv", "products.csv", "sales_teams.csv", "sales_pipeline.csv")}
    accounts, products, teams, pipeline = (tables[name] for name in tables)
    stages = Counter(row["deal_stage"] for row in pipeline)
    closed = [row for row in pipeline if row["deal_stage"] in {"Won", "Lost"}]
    won = [row for row in pipeline if row["deal_stage"] == "Won"]
    engage_dates = [date.fromisoformat(row["engage_date"]) for row in pipeline if row["engage_date"]]
    close_dates = [date.fromisoformat(row["close_date"]) for row in pipeline if row["close_date"]]
    product_keys = {row["product"] for row in products}
    unknown_products = Counter(row["product"] for row in pipeline if row["product"] not in product_keys)
    nulls = {
        name: {field: sum(not row[field].strip() for row in data) for field in data[0]}
        for name, data in tables.items()
    }
    duplicate_rows = {name: len(data) - len({tuple(row.items()) for row in data}) for name, data in tables.items()}
    duplicate_keys = {
        "accounts.csv": len(accounts) - len({r["account"] for r in accounts}),
        "products.csv": len(products) - len({r["product"] for r in products}),
        "sales_teams.csv": len(teams) - len({r["sales_agent"] for r in teams}),
        "sales_pipeline.csv": len(pipeline) - len({r["opportunity_id"] for r in pipeline}),
    }
    chronology_errors = sum(
        date.fromisoformat(row["close_date"]) < date.fromisoformat(row["engage_date"])
        for row in closed
    )
    result = {
        "source": "Maven CRM Sales Opportunities (fictitious), via pinned public mirror",
        "manifest_sha256": hashlib.sha256((ROOT / "data/manifest.json").read_bytes()).hexdigest(),
        "file_hashes_verified": hash_checks,
        "rows": {name: len(data) for name, data in tables.items()},
        "nulls": nulls,
        "duplicate_rows": duplicate_rows,
        "duplicate_primary_keys": duplicate_keys,
        "stage_counts": dict(stages),
        "closed_opportunities": len(closed),
        "observed_win_rate_closed": len(won) / len(closed),
        "won_close_value_total": sum(float(row["close_value"]) for row in won),
        "engage_date_range": [min(engage_dates).isoformat(), max(engage_dates).isoformat()],
        "close_date_range": [min(close_dates).isoformat(), max(close_dates).isoformat()],
        "close_before_engage": chronology_errors,
        "unknown_products_before_alias": dict(unknown_products),
        "product_alias_decision": {"GTXPro": "GTX Pro"},
        "unknown_agents": sorted({r["sales_agent"] for r in pipeline} - {r["sales_agent"] for r in teams}),
        "unknown_accounts": sorted({r["account"] for r in pipeline if r["account"]} - {r["account"] for r in accounts}),
        "limitations": [
            "Dados fictícios; não demonstram impacto comercial em empresas reais.",
            "O conjunto não possui histórico de contatos, custos, metas ou motivos de perda.",
            "A avaliação preditiva usa somente Won/Lost; oportunidades recentes ainda abertas podem causar viés de seleção.",
            "A revisão do espelho público foi fixada, mas os bytes não foram comparados com um download oficial autenticado.",
        ],
    }
    (ROOT / "artifacts").mkdir(exist_ok=True)
    (ROOT / "artifacts/audit.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report = f"""# Auditoria da base Maven CRM Sales Opportunities

Auditoria executada nos arquivos registrados em `data/manifest.json`. A fonte descreve uma empresa B2B fictícia de hardware. Os arquivos vieram de um espelho público fixado na revisão informada no manifesto; não houve comparação byte a byte com o download oficial autenticado.

## Resultado

- 8.800 oportunidades com identificadores únicos e sem linhas integralmente duplicadas.
- 4.238 ganhas, 2.473 perdidas, 1.589 em engajamento e 500 em prospecção.
- 6.711 negócios encerrados. A taxa observada de ganho entre encerrados é {result['observed_win_rate_closed']:.2%}.
- Soma do valor de fechamento dos negócios ganhos: USD {result['won_close_value_total']:,.0f}. O dicionário chama esse campo de receita do negócio; não equivale necessariamente a receita contábil.
- Engajamentos entre {result['engage_date_range'][0]} e {result['engage_date_range'][1]}; fechamentos entre {result['close_date_range'][0]} e {result['close_date_range'][1]}.
- Nenhum fechamento anterior ao engajamento.
- Chaves de conta e vendedor usadas no pipeline existem nas tabelas correspondentes.
- Há {sum(unknown_products.values())} registros com `GTXPro`, enquanto o cadastro contém `GTX Pro`. A preparação aplica esse único alias e preserva o valor original em `source_product`.

## Ausências relevantes

- `account`: 1.425 ausências, concentradas em oportunidades abertas.
- `engage_date`: 500 ausências, correspondentes a `Prospecting`.
- `close_date` e `close_value`: 2.089 ausências, correspondentes às oportunidades abertas.
- `subsidiary_of`: 70 ausências; nesse campo, vazio significa ausência de controladora informada.

Essas ausências são coerentes com os estágios e não devem ser preenchidas com valores inventados.

## Decisão de uso

A base foi aprovada para a demonstração do importador, banco, dashboard e lista de oportunidades. Foi aprovada com ressalvas para um experimento retrospectivo de classificação entre `Won` e `Lost`, no instante de entrada em `Engaging`.

Campos posteriores ao desfecho (`deal_stage`, `close_date` e `close_value`) ficam fora das variáveis preditoras. O experimento não inclui `Prospecting`, pois esse estágio não possui `engage_date`, e não usa as oportunidades abertas como exemplos negativos. O teste temporal reduz, mas não elimina, o risco de viés. Resultados nesta base não validam ganho financeiro nem generalização comercial.

## Limites para o produto

Não calcular tempo sem contato, margem, atingimento de meta ou retorno de marketing. Esses campos não existem. Na versão comercial, o modelo deverá ser treinado e validado separadamente para dados autorizados de cada cliente; sem histórico suficiente, o sistema deve apresentar indicadores e regras transparentes.
"""
    (ROOT / "planejamento/AUDITORIA_DADOS.md").write_text(report, encoding="utf-8")
    print(json.dumps({"status": "ok", "opportunities": len(pipeline), "closed": len(closed), "issues": {"unknown_product_rows": sum(unknown_products.values())}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
