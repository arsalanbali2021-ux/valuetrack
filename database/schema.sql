-- ============================================================
-- ValueTrack – Smart Financial & Insurance Management System
-- Database Schema (MySQL 8+)
-- ============================================================

CREATE DATABASE IF NOT EXISTS valuetrack
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE valuetrack;

-- -----------------------------------------------------------
-- 1. users
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id       INT PRIMARY KEY AUTO_INCREMENT,
    name          VARCHAR(120)  NOT NULL,
    email         VARCHAR(255)  NOT NULL UNIQUE,
    password_hash VARCHAR(255)  NOT NULL,
    created_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- -----------------------------------------------------------
-- 2. loans
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS loans (
    loan_id             INT PRIMARY KEY AUTO_INCREMENT,
    user_id             INT            NOT NULL,
    principal           DECIMAL(12,2)  NOT NULL CHECK (principal > 0),
    annual_interest_rate DECIMAL(6,4)  NOT NULL CHECK (annual_interest_rate >= 0),
    tenure_months       INT            NOT NULL CHECK (tenure_months > 0),
    start_date          DATE           NOT NULL,
    created_at          TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_loans_user_id (user_id),

    CONSTRAINT fk_loans_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------------
-- 3. emi_schedule  (weak entity of loans)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS emi_schedule (
    emi_id              INT PRIMARY KEY AUTO_INCREMENT,
    loan_id             INT            NOT NULL,
    month_no            INT            NOT NULL,
    emi_amount          DECIMAL(12,2)  NOT NULL,
    principal_component DECIMAL(12,2)  NOT NULL,
    interest_component  DECIMAL(12,2)  NOT NULL,
    remaining_balance   DECIMAL(12,2)  NOT NULL,
    due_date            DATE           NOT NULL,

    UNIQUE KEY uq_emi_loan_month (loan_id, month_no),
    INDEX idx_emi_loan_id (loan_id),

    CONSTRAINT fk_emi_loan
        FOREIGN KEY (loan_id) REFERENCES loans(loan_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------------
-- 4. expenses
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS expenses (
    expense_id   INT PRIMARY KEY AUTO_INCREMENT,
    user_id      INT            NOT NULL,
    category     VARCHAR(80)    NOT NULL,
    amount       DECIMAL(12,2)  NOT NULL CHECK (amount > 0),
    expense_date DATE           NOT NULL,
    description  TEXT,
    created_at   TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_expenses_user_date (user_id, expense_date),

    CONSTRAINT fk_expenses_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------------
-- 5. insurance  (master policy list)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS insurance (
    insurance_id         INT PRIMARY KEY AUTO_INCREMENT,
    provider_name        VARCHAR(150)   NOT NULL,
    plan_name            VARCHAR(150)   NOT NULL,
    min_age              TINYINT        NOT NULL,
    max_age              TINYINT        NOT NULL,
    premium              DECIMAL(12,2)  NOT NULL,
    coverage_amount      DECIMAL(12,2)  NOT NULL,
    pre_existing_allowed TINYINT(1)     DEFAULT 0,
    room_rent_limit      DECIMAL(12,2)  DEFAULT NULL,
    created_at           TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_insurance_coverage (coverage_amount),
    INDEX idx_insurance_premium  (premium)
) ENGINE=InnoDB;

-- -----------------------------------------------------------
-- 6. insurance_request
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS insurance_request (
    request_id             INT PRIMARY KEY AUTO_INCREMENT,
    user_id                INT            NOT NULL,
    age                    TINYINT        NOT NULL,
    pre_existing_condition TINYINT(1)     NOT NULL DEFAULT 0,
    annual_budget          DECIMAL(12,2)  NOT NULL,
    created_at             TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_insreq_user_id (user_id),

    CONSTRAINT fk_insreq_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------------
-- 7. insurance_result  (ranked results)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS insurance_result (
    result_id     INT PRIMARY KEY AUTO_INCREMENT,
    request_id    INT            NOT NULL,
    insurance_id  INT            NOT NULL,
    rank_score    DECIMAL(6,4)   NOT NULL,
    rank_position INT            NOT NULL,
    created_at    TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_insres_request_id  (request_id),
    INDEX idx_insres_insurance_id (insurance_id),

    CONSTRAINT fk_insres_request
        FOREIGN KEY (request_id) REFERENCES insurance_request(request_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_insres_insurance
        FOREIGN KEY (insurance_id) REFERENCES insurance(insurance_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;
