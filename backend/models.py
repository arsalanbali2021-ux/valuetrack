"""
ValueTrack — SQLAlchemy ORM Models
Maps all 7 database tables to Python classes.
"""
from sqlalchemy import (
    Column, Integer, String, Text, Date, TIMESTAMP, DECIMAL,
    SmallInteger, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db import Base


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    loans = relationship('Loan', back_populates='user', cascade='all, delete-orphan')
    expenses = relationship('Expense', back_populates='user', cascade='all, delete-orphan')
    insurance_requests = relationship('InsuranceRequest', back_populates='user', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'created_at': str(self.created_at) if self.created_at else None
        }


class Loan(Base):
    __tablename__ = 'loans'

    loan_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    principal = Column(DECIMAL(12, 2), nullable=False)
    annual_interest_rate = Column(DECIMAL(6, 4), nullable=False)
    tenure_months = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    user = relationship('User', back_populates='loans')
    emi_rows = relationship('EMISchedule', back_populates='loan', cascade='all, delete-orphan',
                            order_by='EMISchedule.month_no')

    def to_dict(self):
        return {
            'loan_id': self.loan_id,
            'user_id': self.user_id,
            'principal': float(self.principal),
            'annual_interest_rate': float(self.annual_interest_rate),
            'tenure_months': self.tenure_months,
            'start_date': str(self.start_date),
            'created_at': str(self.created_at) if self.created_at else None
        }


class EMISchedule(Base):
    __tablename__ = 'emi_schedule'
    __table_args__ = (
        UniqueConstraint('loan_id', 'month_no', name='uq_emi_loan_month'),
    )

    emi_id = Column(Integer, primary_key=True, autoincrement=True)
    loan_id = Column(Integer, ForeignKey('loans.loan_id', ondelete='CASCADE'), nullable=False, index=True)
    month_no = Column(Integer, nullable=False)
    emi_amount = Column(DECIMAL(12, 2), nullable=False)
    principal_component = Column(DECIMAL(12, 2), nullable=False)
    interest_component = Column(DECIMAL(12, 2), nullable=False)
    remaining_balance = Column(DECIMAL(12, 2), nullable=False)
    due_date = Column(Date, nullable=False)

    # Relationships
    loan = relationship('Loan', back_populates='emi_rows')

    def to_dict(self):
        return {
            'emi_id': self.emi_id,
            'loan_id': self.loan_id,
            'month_no': self.month_no,
            'emi_amount': float(self.emi_amount),
            'principal_component': float(self.principal_component),
            'interest_component': float(self.interest_component),
            'remaining_balance': float(self.remaining_balance),
            'due_date': str(self.due_date)
        }


class Expense(Base):
    __tablename__ = 'expenses'

    expense_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    category = Column(String(80), nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)
    expense_date = Column(Date, nullable=False)
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index('idx_expenses_user_date', 'user_id', 'expense_date'),
    )

    # Relationships
    user = relationship('User', back_populates='expenses')

    def to_dict(self):
        return {
            'expense_id': self.expense_id,
            'user_id': self.user_id,
            'category': self.category,
            'amount': float(self.amount),
            'expense_date': str(self.expense_date),
            'description': self.description,
            'created_at': str(self.created_at) if self.created_at else None
        }


class Insurance(Base):
    __tablename__ = 'insurance'

    insurance_id = Column(Integer, primary_key=True, autoincrement=True)
    provider_name = Column(String(150), nullable=False)
    plan_name = Column(String(150), nullable=False)
    min_age = Column(SmallInteger, nullable=False)
    max_age = Column(SmallInteger, nullable=False)
    premium = Column(DECIMAL(12, 2), nullable=False)
    coverage_amount = Column(DECIMAL(12, 2), nullable=False)
    pre_existing_allowed = Column(SmallInteger, default=0)
    room_rent_limit = Column(DECIMAL(12, 2), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    def to_dict(self):
        return {
            'insurance_id': self.insurance_id,
            'provider_name': self.provider_name,
            'plan_name': self.plan_name,
            'min_age': self.min_age,
            'max_age': self.max_age,
            'premium': float(self.premium),
            'coverage_amount': float(self.coverage_amount),
            'pre_existing_allowed': bool(self.pre_existing_allowed),
            'room_rent_limit': float(self.room_rent_limit) if self.room_rent_limit else None,
            'created_at': str(self.created_at) if self.created_at else None
        }


class InsuranceRequest(Base):
    __tablename__ = 'insurance_request'

    request_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    age = Column(SmallInteger, nullable=False)
    pre_existing_condition = Column(SmallInteger, nullable=False, default=0)
    annual_budget = Column(DECIMAL(12, 2), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    user = relationship('User', back_populates='insurance_requests')
    results = relationship('InsuranceResult', back_populates='request', cascade='all, delete-orphan',
                           order_by='InsuranceResult.rank_position')

    def to_dict(self):
        return {
            'request_id': self.request_id,
            'user_id': self.user_id,
            'age': self.age,
            'pre_existing_condition': bool(self.pre_existing_condition),
            'annual_budget': float(self.annual_budget),
            'created_at': str(self.created_at) if self.created_at else None
        }


class InsuranceResult(Base):
    __tablename__ = 'insurance_result'

    result_id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(Integer, ForeignKey('insurance_request.request_id', ondelete='CASCADE'),
                        nullable=False, index=True)
    insurance_id = Column(Integer, ForeignKey('insurance.insurance_id', ondelete='CASCADE'),
                          nullable=False, index=True)
    rank_score = Column(DECIMAL(6, 4), nullable=False)
    rank_position = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    request = relationship('InsuranceRequest', back_populates='results')
    insurance = relationship('Insurance')

    def to_dict(self):
        return {
            'result_id': self.result_id,
            'request_id': self.request_id,
            'insurance_id': self.insurance_id,
            'rank_score': float(self.rank_score),
            'rank_position': self.rank_position,
            'created_at': str(self.created_at) if self.created_at else None
        }
