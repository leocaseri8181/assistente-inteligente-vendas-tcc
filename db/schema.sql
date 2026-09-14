PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tenants (
    tenant_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS accounts (
    tenant_id TEXT NOT NULL,
    account TEXT NOT NULL,
    sector TEXT NOT NULL,
    year_established INTEGER NOT NULL,
    revenue_musd REAL NOT NULL,
    employees INTEGER NOT NULL,
    office_location TEXT NOT NULL,
    subsidiary_of TEXT,
    PRIMARY KEY (tenant_id, account),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS products (
    tenant_id TEXT NOT NULL,
    product TEXT NOT NULL,
    series TEXT NOT NULL,
    sales_price REAL NOT NULL,
    PRIMARY KEY (tenant_id, product),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sales_agents (
    tenant_id TEXT NOT NULL,
    sales_agent TEXT NOT NULL,
    manager TEXT NOT NULL,
    regional_office TEXT NOT NULL,
    PRIMARY KEY (tenant_id, sales_agent),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS opportunities (
    tenant_id TEXT NOT NULL,
    opportunity_id TEXT NOT NULL,
    sales_agent TEXT NOT NULL,
    product TEXT NOT NULL,
    source_product TEXT NOT NULL,
    account TEXT,
    deal_stage TEXT NOT NULL CHECK (deal_stage IN ('Prospecting', 'Engaging', 'Won', 'Lost')),
    engage_date TEXT,
    close_date TEXT,
    close_value REAL,
    PRIMARY KEY (tenant_id, opportunity_id),
    FOREIGN KEY (tenant_id, sales_agent) REFERENCES sales_agents(tenant_id, sales_agent),
    FOREIGN KEY (tenant_id, product) REFERENCES products(tenant_id, product),
    FOREIGN KEY (tenant_id, account) REFERENCES accounts(tenant_id, account)
);

CREATE INDEX IF NOT EXISTS idx_opportunities_tenant_stage ON opportunities(tenant_id, deal_stage);
CREATE INDEX IF NOT EXISTS idx_opportunities_tenant_engage ON opportunities(tenant_id, engage_date);

CREATE TABLE IF NOT EXISTS import_runs (
    import_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    dataset_hash TEXT NOT NULL,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    row_count INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('succeeded', 'failed')),
    UNIQUE (tenant_id, dataset_hash, status),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
);

