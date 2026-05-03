"""
Accounts service layer — OTP generation, SMS dispatch, token creation.

SMS providers (in priority order):
  1. Africa's Talking — works across Africa (Nigeria, Ethiopia, Kenya, etc.)
  2. Twilio — fallback if AT not configured
  3. Dev mode — prints OTP to console AND returns it in the API response
"""
from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OTPCode, User


def send_otp(phone_number: str) -> OTPCode:
    """
    Generate a fresh OTP and send it via SMS.
    Returns the OTPCode instance.
    """
    # Invalidate any previous unused codes for this number
    OTPCode.objects.filter(phone_number=phone_number, is_used=False).update(is_used=True)

    code = OTPCode.generate_code()
    otp = OTPCode.objects.create(phone_number=phone_number, code=code)

    _dispatch_sms(phone_number, code)
    return otp


def _dispatch_sms(phone_number: str, code: str):
    """
    Try Africa's Talking first, then Twilio, then dev fallback.
    """
    msg = (
        f"Your GreenGig Africa verification code is: {code}. "
        f"Valid for {settings.OTP_EXPIRY_MINUTES} minutes."
    )

    # ── Africa's Talking ──────────────────────────────────────
    at_key = getattr(settings, 'AT_API_KEY', '')
    at_user = getattr(settings, 'AT_USERNAME', '')
    if at_key and at_user:
        try:
            import africastalking
            africastalking.initialize(at_user, at_key)
            sms = africastalking.SMS
            sms.send(msg, [phone_number])
            return
        except Exception as exc:
            import logging
            logging.getLogger(__name__).error("Africa's Talking SMS failed: %s", exc)

    # ── Twilio fallback ───────────────────────────────────────
    if getattr(settings, 'TWILIO_ACCOUNT_SID', ''):
        try:
            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=msg,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number,
            )
            return
        except Exception as exc:
            import logging
            logging.getLogger(__name__).error("Twilio SMS failed: %s", exc)

    # ── Dev fallback ──────────────────────────────────────────
    print(f"\n{'='*50}")
    print(f"[DEV OTP] {phone_number} → {code}")
    print(f"{'='*50}\n")


def verify_otp(phone_number: str, code: str) -> tuple[bool, str]:
    """Validate OTP. Returns (success: bool, message: str)."""
    otp = (
        OTPCode.objects.filter(phone_number=phone_number, is_used=False)
        .order_by("-created_at")
        .first()
    )

    if not otp:
        return False, "No active OTP found. Please request a new code."
    if not otp.is_valid():
        return False, "OTP has expired. Please request a new code."
    if otp.code != code:
        return False, "Invalid OTP code."

    otp.is_used = True
    otp.save(update_fields=["is_used"])
    return True, "OTP verified."


def get_or_create_user(phone_number: str) -> tuple[User, bool]:
    """Return (user, created) for a verified phone number."""
    return User.objects.get_or_create(phone_number=phone_number)


def issue_tokens(user: User) -> dict:
    """Return JWT access + refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }
