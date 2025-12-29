"""
FastAPI Main Application for License Distribution Server
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request, Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import uvicorn

from config import settings
from database import get_db, init_db
from models import License, Order, EmailLog
from stripe_webhook import webhook_handler
from email_sender import EmailSender

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir / "src"))
from core.license_manager import LicenseGenerator

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Automated license distribution system for Canto-beats"
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    """Initialize database tables"""
    print("🚀 Starting License Distribution Server...")
    init_db()
    print("✅ Database initialized")


# Health check
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "stripe": "configured" if settings.stripe_api_key else "not configured",
        "email": "configured" if settings.sendgrid_api_key else "not configured"
    }


# Stripe Webhook
@app.post("/webhook/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Stripe webhook events
    
    This endpoint receives payment notifications from Stripe
    """
    try:
        # Verify webhook
        event = await webhook_handler.verify_webhook(request)
        
        event_type = event['type']
        print(f"📬 Received webhook: {event_type}")
        
        # Handle different event types
        if event_type == 'payment_intent.succeeded':
            result = webhook_handler.handle_payment_succeeded(event, db)
            return JSONResponse(content=result)
        
        elif event_type == 'payment_intent.payment_failed':
            result = webhook_handler.handle_payment_failed(event, db)
            return JSONResponse(content=result)
        
        else:
            print(f"ℹ️  Unhandled event type: {event_type}")
            return JSONResponse(content={"received": True})
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Admin authentication
def verify_admin(authorization: Optional[str] = Header(None)):
    """Verify admin credentials"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    # Simple basic auth (in production, use proper JWT tokens)
    try:
        auth_type, credentials = authorization.split(' ')
        if auth_type.lower() != 'basic':
            raise HTTPException(status_code=401, detail="Invalid auth type")
        
        import base64
        decoded = base64.b64decode(credentials).decode('utf-8')
        username, password = decoded.split(':')
        
        if username != settings.admin_username or password != settings.admin_password:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        return True
    except:
        raise HTTPException(status_code=401, detail="Invalid authorization")


# Admin endpoints
@app.get("/admin/licenses")
async def list_licenses(
    db: Session = Depends(get_db),
    admin: bool = Depends(verify_admin),
    skip: int = 0,
    limit: int = 100
):
    """List all licenses (admin only)"""
    licenses = db.query(License).offset(skip).limit(limit).all()
    total = db.query(License).count()
    
    return {
        "total": total,
        "licenses": [
            {
                "id": lic.id,
                "license_key": lic.license_key,
                "customer_email": lic.customer_email,
                "status": lic.status,
                "created_at": lic.created_at.isoformat() if lic.created_at else None,
                "activated_at": lic.activated_at.isoformat() if lic.activated_at else None
            }
            for lic in licenses
        ]
    }


@app.get("/admin/orders")
async def list_orders(
    db: Session = Depends(get_db),
    admin: bool = Depends(verify_admin),
    skip: int = 0,
    limit: int = 100
):
    """List all orders (admin only)"""
    orders = db.query(Order).offset(skip).limit(limit).all()
    total = db.query(Order).count()
    
    return {
        "total": total,
        "orders": [
            {
                "id": order.id,
                "order_number": order.order_number,
                "customer_email": order.customer_email,
                "amount": order.amount,
                "currency": order.currency,
                "status": order.status,
                "license_key": order.license_key,
                "email_sent": order.email_sent,
                "created_at": order.created_at.isoformat() if order.created_at else None
            }
            for order in orders
        ]
    }


@app.post("/admin/generate-license")
async def manual_generate_license(
    customer_email: str,
    customer_name: str = "",
    db: Session = Depends(get_db),
    admin: bool = Depends(verify_admin)
):
    """Manually generate and send license (admin only)"""
    
    # Generate license
    generator = LicenseGenerator()
    license_key = generator.generate(
        license_type=settings.license_type,
        transfers_allowed=settings.license_transfers_allowed
    )
    
    # Create license record
    license_record = License(
        license_key=license_key,
        license_type=settings.license_type,
        transfers_remaining=settings.license_transfers_allowed,
        customer_email=customer_email,
        customer_name=customer_name,
        status="active"
    )
    
    db.add(license_record)
    db.commit()
    
    # Send email
    email_sender = EmailSender()
    email_sent = email_sender.send_license_email(
        recipient_email=customer_email,
        recipient_name=customer_name or customer_email.split('@')[0],
        license_key=license_key
    )
    
    # Log email
    email_log = EmailLog(
        recipient=customer_email,
        subject="您的 Canto-beats 授權序號",
        status="sent" if email_sent else "failed",
        license_key=license_key,
        sent_at=None
    )
    db.add(email_log)
    db.commit()
    
    return {
        "success": True,
        "license_key": license_key,
        "email_sent": email_sent
    }


@app.get("/admin/stats")
async def get_stats(
    db: Session = Depends(get_db),
    admin: bool = Depends(verify_admin)
):
    """Get system statistics (admin only)"""
    
    total_licenses = db.query(License).count()
    active_licenses = db.query(License).filter(License.status == "active").count()
    used_licenses = db.query(License).filter(License.status == "used").count()
    
    total_orders = db.query(Order).count()
    completed_orders = db.query(Order).filter(Order.status == "completed").count()
    failed_orders = db.query(Order).filter(Order.status == "failed").count()
    
    total_emails = db.query(EmailLog).count()
    sent_emails = db.query(EmailLog).filter(EmailLog.status == "sent").count()
    
    return {
        "licenses": {
            "total": total_licenses,
            "active": active_licenses,
            "used": used_licenses
        },
        "orders": {
            "total": total_orders,
            "completed": completed_orders,
            "failed": failed_orders
        },
        "emails": {
            "total": total_emails,
            "sent": sent_emails,
            "failed": total_emails - sent_emails
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
