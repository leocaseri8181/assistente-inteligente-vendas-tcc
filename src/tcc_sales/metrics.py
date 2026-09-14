from __future__ import annotations

import sqlite3
from datetime import date


def _period_clause(date_from: str | None, date_to: str | None, column: str = "close_date") -> tuple[str, list[str]]:
    clauses: list[str] = []
    values: list[str] = []
    if date_from:
        clauses.append(f"{column} >= ?")
        values.append(date.fromisoformat(date_from).isoformat())
    if date_to:
        clauses.append(f"{column} <= ?")
        values.append(date.fromisoformat(date_to).isoformat())
    if date_from and date_to and date_from > date_to:
        raise ValueError("date_from must not be after date_to")
    return (" AND " + " AND ".join(clauses) if clauses else "", values)


def tenant_exists(connection: sqlite3.Connection, tenant_id: str) -> bool:
    return connection.execute("SELECT 1 FROM tenants WHERE tenant_id = ?", (tenant_id,)).fetchone() is not None


def summary(connection: sqlite3.Connection, tenant_id: str, date_from: str | None = None, date_to: str | None = None) -> dict[str, object]:
    period_sql, period_values = _period_clause(date_from, date_to)
    available = connection.execute(
        "SELECT MIN(close_date), MAX(close_date), MAX(close_date) FROM opportunities WHERE tenant_id=? AND close_date IS NOT NULL",
        (tenant_id,),
    ).fetchone()
    selected_from = date_from or available[0]
    selected_to = date_to or available[1]
    stage_counts = dict(connection.execute(
        "SELECT deal_stage, COUNT(*) FROM opportunities WHERE tenant_id=? GROUP BY deal_stage",
        (tenant_id,),
    ))
    row = connection.execute(
        f"""
        SELECT
            SUM(CASE WHEN deal_stage='Won' THEN 1 ELSE 0 END) AS won_count,
            SUM(CASE WHEN deal_stage='Lost' THEN 1 ELSE 0 END) AS lost_count,
            SUM(CASE WHEN deal_stage='Won' THEN close_value ELSE 0 END) AS won_value,
            AVG(CASE WHEN deal_stage='Won' THEN close_value END) AS average_won_value,
            AVG(julianday(close_date) - julianday(engage_date)) AS average_cycle_days
        FROM opportunities
        WHERE tenant_id=? AND deal_stage IN ('Won','Lost'){period_sql}
        """,
        [tenant_id, *period_values],
    ).fetchone()
    won_count = int(row[0] or 0)
    lost_count = int(row[1] or 0)
    closed_count = won_count + lost_count
    return {
        "tenant_id": tenant_id,
        "snapshot_date": available[2],
        "period": {"date_from": selected_from, "date_to": selected_to, "basis": "close_date"},
        "pipeline_snapshot": {
            "total": sum(stage_counts.values()),
            "prospecting": stage_counts.get("Prospecting", 0),
            "engaging": stage_counts.get("Engaging", 0),
            "won": stage_counts.get("Won", 0),
            "lost": stage_counts.get("Lost", 0),
        },
        "closed_period": {
            "closed_count": closed_count,
            "won_count": won_count,
            "lost_count": lost_count,
            "win_rate": won_count / closed_count if closed_count else None,
            "won_value": float(row[2] or 0),
            "average_won_value": float(row[3]) if row[3] is not None else None,
            "average_cycle_days": float(row[4]) if row[4] is not None else None,
        },
        "definitions": {
            "win_rate": "Won / (Won + Lost); open opportunities are excluded.",
            "won_value": "Sum of close_value for Won deals; not necessarily accounting revenue.",
            "average_cycle_days": "Average calendar days from engage_date to close_date among closed deals.",
            "pipeline_snapshot": "Current recorded stages at the dataset snapshot; historical stage movements are unavailable.",
        },
    }


def monthly_trend(connection: sqlite3.Connection, tenant_id: str, date_from: str | None = None, date_to: str | None = None) -> list[dict[str, object]]:
    period_sql, period_values = _period_clause(date_from, date_to)
    rows = connection.execute(
        f"""
        SELECT strftime('%Y-%m', close_date) AS month,
               SUM(deal_stage='Won') AS won_count,
               SUM(deal_stage='Lost') AS lost_count,
               SUM(CASE WHEN deal_stage='Won' THEN close_value ELSE 0 END) AS won_value
        FROM opportunities
        WHERE tenant_id=? AND deal_stage IN ('Won','Lost'){period_sql}
        GROUP BY month ORDER BY month
        """,
        [tenant_id, *period_values],
    ).fetchall()
    return [{"month": row[0], "won_count": row[1], "lost_count": row[2], "won_value": float(row[3] or 0)} for row in rows]


def product_breakdown(connection: sqlite3.Connection, tenant_id: str, date_from: str | None = None, date_to: str | None = None) -> list[dict[str, object]]:
    period_sql, period_values = _period_clause(date_from, date_to, "o.close_date")
    rows = connection.execute(
        f"""
        SELECT o.product,
               SUM(o.deal_stage='Won') AS won_count,
               SUM(o.deal_stage='Lost') AS lost_count,
               SUM(CASE WHEN o.deal_stage='Won' THEN o.close_value ELSE 0 END) AS won_value,
               p.sales_price
        FROM opportunities o
        JOIN products p ON p.tenant_id=o.tenant_id AND p.product=o.product
        WHERE o.tenant_id=? AND o.deal_stage IN ('Won','Lost'){period_sql}
        GROUP BY o.product, p.sales_price ORDER BY won_value DESC, o.product
        """,
        [tenant_id, *period_values],
    ).fetchall()
    result = []
    for row in rows:
        closed = row[1] + row[2]
        result.append({
            "product": row[0], "won_count": row[1], "lost_count": row[2], "closed_count": closed,
            "win_rate": row[1] / closed if closed else None, "won_value": float(row[3] or 0), "sales_price": float(row[4]),
        })
    return result


def filter_options(connection: sqlite3.Connection, tenant_id: str) -> dict[str, list[str]]:
    def values(query):
        return [row[0] for row in connection.execute(query, (tenant_id,)).fetchall()]
    return {
        "products": values("SELECT product FROM products WHERE tenant_id=? ORDER BY product"),
        "managers": values("SELECT DISTINCT manager FROM sales_agents WHERE tenant_id=? ORDER BY manager"),
        "agents": values("SELECT sales_agent FROM sales_agents WHERE tenant_id=? ORDER BY sales_agent"),
        "stages": ["Engaging", "Prospecting"],
    }


def open_opportunities(
    connection: sqlite3.Connection,
    tenant_id: str,
    *,
    stage: str | None = None,
    product: str | None = None,
    manager: str | None = None,
    agent: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, object]:
    snapshot = connection.execute(
        "SELECT MAX(close_date) FROM opportunities WHERE tenant_id=? AND close_date IS NOT NULL", (tenant_id,)
    ).fetchone()[0]
    clauses = ["o.tenant_id=?", "o.deal_stage IN ('Engaging','Prospecting')"]
    values: list[object] = [tenant_id]
    for column, value in (("o.deal_stage", stage), ("o.product", product), ("a.manager", manager), ("o.sales_agent", agent)):
        if value:
            clauses.append(f"{column}=?")
            values.append(value)
    where = " AND ".join(clauses)
    total = connection.execute(
        f"SELECT COUNT(*) FROM opportunities o JOIN sales_agents a ON a.tenant_id=o.tenant_id AND a.sales_agent=o.sales_agent WHERE {where}", values
    ).fetchone()[0]
    rows = connection.execute(
        f"""
        SELECT o.opportunity_id, o.deal_stage, o.account, o.product, o.sales_agent, a.manager,
               a.regional_office, o.engage_date,
               CASE WHEN o.engage_date IS NULL THEN NULL ELSE CAST(julianday(?) - julianday(o.engage_date) AS INTEGER) END AS days_open,
               CASE
                 WHEN o.deal_stage='Engaging' AND julianday(?) - julianday(o.engage_date) >= 90 THEN 3
                 WHEN o.deal_stage='Engaging' AND julianday(?) - julianday(o.engage_date) >= 45 THEN 2
                 WHEN o.deal_stage='Prospecting' AND o.account IS NULL THEN 2
                 ELSE 1 END AS priority_order
        FROM opportunities o
        JOIN sales_agents a ON a.tenant_id=o.tenant_id AND a.sales_agent=o.sales_agent
        WHERE {where}
        ORDER BY priority_order DESC, COALESCE(days_open, -1) DESC, o.opportunity_id
        LIMIT ? OFFSET ?
        """,
        [snapshot, snapshot, snapshot, *values, limit, offset],
    ).fetchall()
    items = []
    for row in rows:
        days_open = row[8]
        priority = row[9]
        if row[1] == "Prospecting" and row[2] is None:
            reason = "Prospecção sem conta informada"
        elif row[1] == "Prospecting":
            reason = "Aguardando início de engajamento"
        else:
            reason = f"Em engajamento há {days_open} dias desde {row[7]}"
        items.append({
            "opportunity_id": row[0], "stage": row[1], "account": row[2], "product": row[3], "sales_agent": row[4],
            "manager": row[5], "regional_office": row[6], "engage_date": row[7], "days_since_engagement": days_open,
            "review_level": {3: "review_now", 2: "attention", 1: "routine"}[priority], "review_reason": reason,
        })
    return {
        "snapshot_date": snapshot,
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items,
        "ranking_definition": "Transparent review rule based on recorded stage, missing account, and days since engagement; it is not an ML probability or time since last contact.",
    }

