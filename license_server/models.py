"""
Database models for License Distribution Server
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text
from sqlalchemy.sql import func
from database import Base
from datetime import datetime


class License(Base):
    """License key record"""
    __tablename__ = "licenses"
    
    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String(50), unique=True, index=True, nullable=False)
    license_type = Column(String(20), default="permanent")  # permanent or trial
    transfers_remaining = Column(Integer, default=1)
    
    # Customer info
    customer_email = Column(String(255), nullable=False)
    customer_name = Column(String(255), nullable=True)
    
    # Status
    status = Column(String(20), default="active")  # active, used, expired
    activated_at = Column(DateTime, nullable=True)
    machine_fingerprint = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Link to order
    order_id = Column(Integer, nullable=True)
    stripe_payment_id = Column(String(255), nullable=True)


class Order(Base):
    """Order record"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Order info
    order_number = Column(String(50), unique=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="HKD")
    
    # Customer info
    customer_email = Column(String(255), nullable=False)
    customer_name = Column(String(255), nullable=True)
    
    # Stripe info
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    
    # Status
    status = Column(String(20), default="pending")  # pending, completed, failed
    
    # License
    license_key = Column(String(50), nullable=True)
    email_sent = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)


class EmailLog(Base):
    """Email sending log"""
    __tablename__ = "email_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    recipient = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    
    # Status
    status = Column(String(20), default="pending")  # pending, sent, failed
    error_message = Column(Text, nullable=True)
    
    # Reference
    license_key = Column(String(50), nullable=True)
    order_id = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    sent_at = Column(DateTime, nullable=True)
