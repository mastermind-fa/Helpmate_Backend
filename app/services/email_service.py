import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from sqlalchemy.orm import Session
from app.models.user import PasswordReset, EmailVerificationToken, User
from app.models.worker import Worker
from app.models.order import Order
from app.core.config import settings
import uuid

class EmailService:
    def __init__(self):
        self.mail_config = ConnectionConfig(
            MAIL_USERNAME=settings.smtp_username,
            MAIL_PASSWORD=settings.smtp_password,
            MAIL_FROM=settings.smtp_username,
            MAIL_PORT=settings.smtp_port or 587,
            MAIL_SERVER=settings.smtp_server or "smtp.gmail.com",
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        self.fastmail = FastMail(self.mail_config)

    def generate_reset_code(self) -> str:
        """Generate a 6-digit reset code"""
        return str(secrets.randbelow(1000000)).zfill(6)

    def create_reset_record(self, db: Session, email: str, user_type: str) -> PasswordReset:
        """Create a password reset record in the database"""
        # Delete any existing unused reset records for this email
        db.query(PasswordReset).filter(
            PasswordReset.email == email,
            PasswordReset.user_type == user_type,
            PasswordReset.is_used == False
        ).delete()
        
        # Create new reset record
        reset_code = self.generate_reset_code()
        expires_at = datetime.utcnow() + timedelta(minutes=15)  # 15 minutes expiry
        
        reset_record = PasswordReset(
            email=email,
            reset_code=reset_code,
            user_type=user_type,
            expires_at=expires_at
        )
        
        db.add(reset_record)
        db.commit()
        db.refresh(reset_record)
        
        return reset_record

    async def send_reset_email(self, email: str, reset_code: str, user_type: str):
        """Send password reset email"""
        subject = f"Password Reset Code - {settings.app_name}"
        
        html_content = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #1565C0; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0;">{settings.app_name}</h1>
                </div>
                <div style="background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px;">
                    <h2 style="color: #333; margin-bottom: 20px;">Password Reset Request</h2>
                    <p style="color: #666; line-height: 1.6;">
                        You have requested to reset your password for your {user_type} account.
                    </p>
                    <div style="background-color: #e3f2fd; border: 2px solid #1565C0; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                        <h3 style="color: #1565C0; margin: 0 0 10px 0;">Your Reset Code</h3>
                        <div style="font-size: 32px; font-weight: bold; color: #1565C0; letter-spacing: 5px; font-family: 'Courier New', monospace;">
                            {reset_code}
                        </div>
                    </div>
                    <p style="color: #666; line-height: 1.6;">
                        <strong>Important:</strong>
                    </p>
                    <ul style="color: #666; line-height: 1.6;">
                        <li>This code will expire in 15 minutes</li>
                        <li>If you didn't request this reset, please ignore this email</li>
                        <li>Never share this code with anyone</li>
                    </ul>
                    <p style="color: #666; line-height: 1.6;">
                        If you have any questions, please contact our support team.
                    </p>
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #999;">
                        <p>© 2025 {settings.app_name}. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            body=html_content,
            subtype="html"
        )
        
        try:
            await self.fastmail.send_message(message)
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def verify_reset_code(self, db: Session, email: str, reset_code: str, user_type: str) -> Optional[PasswordReset]:
        """Verify if the reset code is valid and not expired"""
        reset_record = db.query(PasswordReset).filter(
            PasswordReset.email == email,
            PasswordReset.reset_code == reset_code,
            PasswordReset.user_type == user_type,
            PasswordReset.is_used == False,
            PasswordReset.expires_at > datetime.utcnow()
        ).first()
        
        return reset_record

    def mark_reset_code_used(self, db: Session, reset_record: PasswordReset):
        """Mark a reset code as used"""
        reset_record.is_used = True
        db.commit()

    # --- Email Verification ---
    def create_verification_token(self, db: Session, user_id: int, user_type: str) -> EmailVerificationToken:
        # Remove any unused tokens for this user
        db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user_id,
            EmailVerificationToken.user_type == user_type,
            EmailVerificationToken.is_used == False
        ).delete()
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=24)
        record = EmailVerificationToken(
            user_id=user_id,
            user_type=user_type,
            token=token,
            expires_at=expires_at
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    async def send_verification_email(self, email: str, token: str, user_type: str):
        subject = f"Verify Your Email - {settings.app_name}"
        verify_url = f"{settings.base_url}/api/v1/auth/verify-email?token={token}"
        html_content = f"""
        <html><body>
        <div style='font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;'>
            <div style='background-color: #1565C0; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;'>
                <h1 style='margin: 0;'>{settings.app_name}</h1>
            </div>
            <div style='background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px;'>
                <h2 style='color: #333; margin-bottom: 20px;'>Verify Your Email</h2>
                <p style='color: #666; line-height: 1.6;'>
                    Thank you for registering as a {user_type}. Please verify your email address by clicking the button below:
                </p>
                <div style='text-align: center; margin: 30px 0;'>
                    <a href='{verify_url}' style='background-color: #1565C0; color: white; padding: 16px 32px; border-radius: 8px; text-decoration: none; font-size: 18px; font-weight: bold;'>Verify Email</a>
                </div>
                <p style='color: #666; line-height: 1.6;'>
                    If you did not create this account, you can ignore this email.
                </p>
                <div style='margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #999;'>
                    <p>© 2025 {settings.app_name}. All rights reserved.</p>
                </div>
            </div>
        </div>
        </body></html>
        """
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            body=html_content,
            subtype="html"
        )
        try:
            await self.fastmail.send_message(message)
            return True
        except Exception as e:
            print(f"Error sending verification email: {e}")
            return False

    def verify_email_token(self, db: Session, token: str, user_type: str) -> Optional[EmailVerificationToken]:
        record = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.token == token,
            EmailVerificationToken.user_type == user_type,
            EmailVerificationToken.is_used == False,
            EmailVerificationToken.expires_at > datetime.utcnow()
        ).first()
        return record

    def mark_verification_token_used(self, db: Session, record: EmailVerificationToken):
        record.is_used = True
        db.commit()

    # --- Order Notification Emails ---
    async def send_order_booked_email(self, user: User, worker: Worker, order: Order):
        subject = f"Order Booked - {settings.app_name}"
        html_content = f"""
        <html><body>
        <div style='font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;'>
            <div style='background-color: #1565C0; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;'>
                <h1 style='margin: 0;'>{settings.app_name}</h1>
            </div>
            <div style='background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px;'>
                <h2 style='color: #333; margin-bottom: 20px;'>Order Booked</h2>
                <p style='color: #666; line-height: 1.6;'>
                    An order has been booked.<br><br>
                    <b>Order ID:</b> {order.id}<br>
                    <b>Description:</b> {order.description}<br>
                    <b>Scheduled Date:</b> {order.scheduled_date}<br>
                    <b>Total Amount:</b> ${order.total_amount}<br>
                </p>
                <div style='margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #999;'>
                    <p>© 2025 {settings.app_name}. All rights reserved.</p>
                </div>
            </div>
        </div>
        </body></html>
        """
        for email in [user.email, worker.email]:
            message = MessageSchema(
                subject=subject,
                recipients=[email],
                body=html_content,
                subtype="html"
            )
            try:
                await self.fastmail.send_message(message)
            except Exception as e:
                print(f"Error sending order booked email to {email}: {e}")

    async def send_order_completed_email(self, user: User, worker: Worker, order: Order):
        subject = f"Order Completed - {settings.app_name}"
        html_content = f"""
        <html><body>
        <div style='font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;'>
            <div style='background-color: #1565C0; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;'>
                <h1 style='margin: 0;'>{settings.app_name}</h1>
            </div>
            <div style='background-color: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px;'>
                <h2 style='color: #333; margin-bottom: 20px;'>Order Completed</h2>
                <p style='color: #666; line-height: 1.6;'>
                    Your order has been marked as completed.<br><br>
                    <b>Order ID:</b> {order.id}<br>
                    <b>Description:</b> {order.description}<br>
                    <b>Completed Date:</b> {order.completed_date}<br>
                    <b>Total Amount:</b> ${order.total_amount}<br>
                </p>
                <div style='margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #999;'>
                    <p>© 2025 {settings.app_name}. All rights reserved.</p>
                </div>
            </div>
        </div>
        </body></html>
        """
        for email in [user.email, worker.email]:
            message = MessageSchema(
                subject=subject,
                recipients=[email],
                body=html_content,
                subtype="html"
            )
            try:
                await self.fastmail.send_message(message)
            except Exception as e:
                print(f"Error sending order completed email to {email}: {e}")

# Global email service instance
email_service = EmailService() 