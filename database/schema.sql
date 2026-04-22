-- ValueTrack Database Schema (MySQL 8+)

CREATE DATABASE IF NOT EXISTS valuetrack -- New Database is created 
  CHARACTER SET utf8mb4 -- supports 4 byte characters 
  COLLATE utf8mb4_unicode_ci; -- string comparison and sorting happens(a and A are treated as equal)

USE valuetrack; -- selects the database 

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id       INT PRIMARY KEY AUTO_INCREMENT,
    name          VARCHAR(120)  NOT NULL,
    email         VARCHAR(255)  NOT NULL UNIQUE,
    password_hash VARCHAR(255)  NOT NULL,
    role          ENUM('user','admin') NOT NULL DEFAULT 'user', -- enum restricts values to a fixed set (user,admin)
    monthly_budget DECIMAL(12,2) DEFAULT 0.00, -- spending limit shown on expenses page and dashboard
    created_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Key-value store for scoring weights these values are used in calculations 
CREATE TABLE IF NOT EXISTS system_settings (
    setting_id    INT PRIMARY KEY AUTO_INCREMENT, -- genrates next id automatically
    setting_key   VARCHAR(100) NOT NULL UNIQUE,
    setting_value VARCHAR(100) NOT NULL,
    updated_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Expense categories (admin-managed)
CREATE TABLE IF NOT EXISTS expense_categories (
    category_id   INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(80) NOT NULL UNIQUE,
    icon          VARCHAR(50) DEFAULT 'category', -- stores icon or icon name
    created_at    TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Loans
CREATE TABLE IF NOT EXISTS loans (
    loan_id             INT PRIMARY KEY AUTO_INCREMENT,
    user_id             INT            NOT NULL,
    principal           DECIMAL(12,2)  NOT NULL CHECK (principal > 0),  -- check make sures that contraints stay valid 
    annual_interest_rate DECIMAL(6,4)  NOT NULL CHECK (annual_interest_rate >= 0),
    tenure_months       INT            NOT NULL CHECK (tenure_months > 0),
    start_date          DATE           NOT NULL,
    created_at          TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_loans_user_id (user_id), -- index to speed up searches 
    CONSTRAINT fk_loans_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE  -- if parent user is deleted all the loans are deleted
) ENGINE=InnoDB;

-- EMI schedule also called amortization schedule   one loan can have multiple emi records which can lead to repeating and violating 1nf
CREATE TABLE IF NOT EXISTS emi_schedule (
    emi_id              INT PRIMARY KEY AUTO_INCREMENT,
    loan_id             INT            NOT NULL,
    month_no            INT            NOT NULL,
    emi_amount          DECIMAL(12,2)  NOT NULL,

    
    principal_component DECIMAL(12,2)  NOT NULL,  -- (12,2 means minimum and maximum value it can hold )
    interest_component  DECIMAL(12,2)  NOT NULL,
    remaining_balance   DECIMAL(12,2)  NOT NULL,
    due_date            DATE           NOT NULL,
    UNIQUE KEY uq_emi_loan_month (loan_id, month_no),
    INDEX idx_emi_loan_id (loan_id),
    CONSTRAINT fk_emi_loan FOREIGN KEY (loan_id) REFERENCES loans(loan_id) ON DELETE CASCADE
) ENGINE=InnoDB; -- if loan table is deleted emi schedule also gets deleted

-- Expenses not in 3nf categories table is stored in plain text instead of referencing which causes redundancy 
CREATE TABLE IF NOT EXISTS expenses (
    expense_id   INT PRIMARY KEY AUTO_INCREMENT,
    user_id      INT            NOT NULL,
    category     VARCHAR(80)    NOT NULL,
    amount       DECIMAL(12,2)  NOT NULL CHECK (amount > 0),
    expense_date DATE           NOT NULL,
    description  TEXT,
    is_fixed     TINYINT(1)     DEFAULT 0, -- 1 for recurring costs like rent
    created_at   TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_expenses_user_date (user_id, expense_date),
    CONSTRAINT fk_expenses_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Insurance plans (master list)
CREATE TABLE IF NOT EXISTS insurance (
    insurance_id         INT PRIMARY KEY AUTO_INCREMENT,
    plan_name            VARCHAR(150)   NOT NULL,
    plan_type            VARCHAR(150)   NOT NULL,
    min_age              TINYINT        NOT NULL,
    max_age              TINYINT        NOT NULL,
    coverage_amount      DECIMAL(12,2)  NOT NULL,
    has_critical_illness TINYINT(1)     DEFAULT 0,
    has_maternity        TINYINT(1)     DEFAULT 0,
    has_accident         TINYINT(1)     DEFAULT 0,
    co_pay_percentage    INT            DEFAULT 0,
    monthly_premium      DECIMAL(12,2)  NOT NULL,
    created_at           TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_insurance_coverage (coverage_amount)
) ENGINE=InnoDB;

-- Insurance request (user submits matching query) 
CREATE TABLE IF NOT EXISTS insurance_request (
    request_id               INT PRIMARY KEY AUTO_INCREMENT,
    user_id                  INT            NOT NULL,
    age                      TINYINT        NOT NULL,
    needs_critical_illness   TINYINT(1)     NOT NULL DEFAULT 0,
    needs_maternity          TINYINT(1)     NOT NULL DEFAULT 0,
    needs_accident           TINYINT(1)     NOT NULL DEFAULT 0,
    monthly_budget           DECIMAL(12,2)  NOT NULL,
    created_at               TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_insreq_user_id (user_id),
    CONSTRAINT fk_insreq_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Insurance result (ranked matches) 
CREATE TABLE IF NOT EXISTS insurance_result (
    result_id     INT PRIMARY KEY AUTO_INCREMENT,
    request_id    INT            NOT NULL,
    insurance_id  INT            NOT NULL,
    rank_score    DECIMAL(6,4)   NOT NULL, 
    rank_position INT            NOT NULL, 
    created_at    TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_insres_request_id  (request_id),
    INDEX idx_insres_insurance_id (insurance_id),
    CONSTRAINT fk_insres_request FOREIGN KEY (request_id) REFERENCES insurance_request(request_id) ON DELETE CASCADE,
    CONSTRAINT fk_insres_insurance FOREIGN KEY (insurance_id) REFERENCES insurance(insurance_id) ON DELETE CASCADE
) ENGINE=InnoDB;



-- default assigns automatic value if no value is given
-- update timestamp automaytically updates timestamp whenever there is modification
-- text is used for description and longer strings 
-- innodb is a storage engine that supports forign key, and is used for relational projects 
-- index speeds up seraching and sorting
-- unique key make sures that the combbination of two columns cannot reoeat 
-- multiple tables were created to reduce redundancy using normalization
-- decimal provides exact precision needed for expense related solutios
-- the database is mostly in 3nf
-- delete cascade prevents orphan records 


