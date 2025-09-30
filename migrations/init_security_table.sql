-- Create securities table with all 22 columns from MVP
CREATE TABLE IF NOT EXISTS securities (
    id SERIAL PRIMARY KEY,
    company_code VARCHAR(50),
    company_name VARCHAR(500),
    prowess_company_code VARCHAR(50),
    cin_code VARCHAR(50),
    isin_code VARCHAR(50) UNIQUE,
    nse_symbol VARCHAR(50),
    bse_scrip_code VARCHAR(50),
    industry_group VARCHAR(200),
    main_product_service_group VARCHAR(200),
    company_website_address TEXT,
    registered_office_pincode VARCHAR(10),
    date_1 DATE,
    shares_outstanding_1 BIGINT,
    market_capitalisation_1 DECIMAL(20,2),
    face_value_1 DECIMAL(10,2),
    shares_traded_1 BIGINT,
    beta DECIMAL(10,6),
    date_2 DATE,
    shares_outstanding_2 BIGINT,
    market_capitalisation_2 DECIMAL(20,2),
    face_value_2 DECIMAL(10,2),
    shares_traded_2 BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_securities_isin ON securities(isin_code);
CREATE INDEX IF NOT EXISTS idx_securities_nse ON securities(nse_symbol);
CREATE INDEX IF NOT EXISTS idx_securities_bse ON securities(bse_scrip_code);
CREATE INDEX IF NOT EXISTS idx_securities_company_name ON securities(company_name);
CREATE INDEX IF NOT EXISTS idx_securities_industry ON securities(industry_group);
CREATE INDEX IF NOT EXISTS idx_securities_prowess_code ON securities(prowess_company_code);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_securities_updated_at 
    BEFORE UPDATE ON securities 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
