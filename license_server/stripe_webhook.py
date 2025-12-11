"""
Stripe Webhook Handler
"""

import os
import sys
from pathlib import Path
import stripe
from fastapi import Request, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from config import settings
from models import Order, License, EmailLog
from email_sender import EmailSender

# Add parent directory to import license generator
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir / "src"))
from core.license_manager import LicenseGenerator

# Configure Stripe
stripe.api_key = settings.stripe_api_key


class StripeWebhookHandler:
    """Handle Stripe webhook events"""
    
    def __init__(self):
        self.license_gen = LicenseGenerator()
        self.email_sender = EmailSender()
    
    async def verify_webhook(self, request: Request) -> dict:
        """
        Verify Stripe webhook signature
        
        Args:
            request: FastAPI request object
            
        Returns:
            Verified event dict
            
        Raises:
            HTTPException: If verification fails
        """
        try:
            payload = await request.body()
            sig_header = request.headers.get('stripe-signature')
            
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.stripe_webhook_secret
            )
            
            return event
            
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
    
    def handle_payment_succeeded(self, event: dict, db: Session) -> dict:
        """
        Handle successful payment
        
        Args:
            event: Stripe event object
            db: Database session
            
        Returns:
            Result dict
        """
        payment_intent = event['data']['object']
        
        # Extract customer info
        customer_email = payment_intent.get('receipt_email') or \
                        payment_intent.get('metadata', {}).get('customer_email')
        customer_name = payment_intent.get('metadata', {}).get('customer_name', '')
        amount = payment_intent.get('amount', 0) / 100  # Convert from cents
        currency = payment_intent.get('currency', 'hkd').upper()
        payment_intent_id = payment_intent.get('id')
        
        if not customer_email:
            print("❌ No customer email found in payment intent")
            return {"success": False, "error": "No customer email"}
        
        print(f"💳 Payment succeeded: {customer_email} - {currency} {amount}")
        
        # Check if order already exists
        existing_order = db.query(Order).filter(
            Order.stripe_payment_intent_id == payment_intent_id
        ).first()
        
        if existing_order:
            print(f"⚠️  Order already exists: {existing_order.order_number}")
            return {"success": True, "order_id": existing_order.id, "duplicate": True}
        
        # Generate license key
        license_key = self.license_gen.generate(
            license_type=settings.license_type,
            transfers_allowed=settings.license_transfers_allowed
        )
        
        print(f"🔑 Generated license: {license_key}")
        
        # Create order
        order_number = f"CB-{datetime.now().strftime('%Y%m%d')}-{payment_intent_id[:8]}"
        order = Order(
            order_number=order_number,
            amount=amount,
            currency=currency,
            customer_email=customer_email,
            customer_name=customer_name,
            stripe_payment_intent_id=payment_intent_id,
            stripe_customer_id=payment_intent.get('customer'),
            status="completed",
            license_key=license_key,
            completed_at=datetime.now()
        )
        
        db.add(order)
        db.flush()  # Get order ID
        
        # Create license record
        license_record = License(
            license_key=license_key,
            license_type=settings.license_type,
            transfers_remaining=settings.license_transfers_allowed,
            customer_email=customer_email,
            customer_name=customer_name,
            order_id=order.id,
            stripe_payment_id=payment_intent_id,
            status="active"
        )
        
        db.add(license_record)
        
        # Send email
        email_sent = self.email_sender.send_license_email(
            recipient_email=customer_email,
            recipient_name=customer_name or customer_email.split('@')[0],
            license_key=license_key
        )
        
        # Log email
        email_log = EmailLog(
            recipient=customer_email,
            subject="您的 Canto-beats 授權序號",
            status="sent" if email_sent else "failed",
            error_message=None if email_sent else "Email delivery failed",
            license_key=license_key,
            order_id=order.id,
            sent_at=datetime.now() if email_sent else None
        )
        
        db.add(email_log)
        
        # Update order email status
        order.email_sent = email_sent
        
        db.commit()
        
        print(f"✅ Order created: {order_number}")
        print(f"{'✅' if email_sent else '❌'} Email {'sent' if email_sent else 'failed'}: {customer_email}")
        
        return {
            "success": True,
            "order_id": order.id,
            "order_number": order_number,
            "license_key": license_key,
            "email_sent": email_sent
        }
    
    def handle_payment_failed(self, event: dict, db: Session) -> dict:
        """Handle failed payment"""
        payment_intent = event['data']['object']
        
        customer_email = payment_intent.get('receipt_email')
        payment_intent_id = payment_intent.get('id')
        
        print(f"❌ Payment failed: {customer_email or 'Unknown'}")
        
        # Create failed order record
        order = Order(
            order_number=f"CB-FAILED-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            amount=payment_intent.get('amount', 0) / 100,
            currency=payment_intent.get('currency', 'hkd').upper(),
            customer_email=customer_email or 'unknown@unknown.com',
            stripe_payment_intent_id=payment_intent_id,
            status="failed",
            notes=f"Payment failed: {payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')}"
        )
        
        db.add(order)
        db.commit()
        
        return {"success": True, "order_id": order.id, "status": "failed"}


# Global handler instance
webhook_handler = StripeWebhookHandler()
