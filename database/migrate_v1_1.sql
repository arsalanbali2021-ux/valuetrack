-- Upgrade an existing ValueTrack database to v1.1 (IRDAI catalogue).
-- Run this ONCE on a database that was created before v1.1.
-- Fresh installs don't need it: schema.sql already includes these changes.

USE valuetrack;

-- Link a plan to its IRDAI-registered product
ALTER TABLE insurance
    ADD COLUMN irdai_uin VARCHAR(60) DEFAULT NULL AFTER monthly_premium,
    ADD INDEX idx_insurance_uin (irdai_uin);

-- IRDAI product register (imported from the admin panel)
CREATE TABLE IF NOT EXISTS irdai_products (
    product_id     INT PRIMARY KEY AUTO_INCREMENT,
    uin            VARCHAR(60)  NOT NULL UNIQUE,
    insurer_name   VARCHAR(200) NOT NULL,
    product_name   VARCHAR(255) NOT NULL,
    product_type   VARCHAR(60),
    financial_year VARCHAR(20),
    approval_date  DATE,
    is_archived    TINYINT(1)   DEFAULT 0,
    imported_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_irdai_insurer (insurer_name)
) ENGINE=InnoDB;
