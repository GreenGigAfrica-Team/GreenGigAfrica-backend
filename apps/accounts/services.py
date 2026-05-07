from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from .models import OTPCode, User


def send_otp(phone_number: str) -> OTPCode:
    """Generate OTP and attempt SMS delivery. Returns the OTPCode instance."""
    OTPCode.objects.filter(phone_number=phone_number, is_used=False).update(is_used=True)
    code = OTPCode.generate_code()
    otp = OTPCode.objects.create(phone_number=phone_number, code=code)
    _dispatch_sms(phone_number, code)
    return otp


def _dispatch_sms(phone_number: str, code: str):
    msg = f'Your GreenGig Africa code is: {code}. Valid for {settings.OTP_EXPIRY_MINUTES} minutes.'

    # Try Twilio if configured
    sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    if sid:
        try:
            from twilio.rest import Client
            client = Client(sid, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(body=msg, from_=settings.TWILIO_PHONE_NUMBER, to=phone_number)
            return
        except Exception as e:
            import logging
            logging.getLogger(__name__).error('Twilio failed: %s', e)

    # Dev fallback — print to console
    print(f'\n{"="*50}')
    print(f'[DEV OTP] {phone_number} → {code}')
    print(f'{"="*50}\n')


def verify_otp(phone_number: str, code: str) -> tuple[bool, str]:
    otp = (
        OTPCode.objects
        .filter(phone_number=phone_number, is_used=False)
        .order_by('-created_at')
        .first()
    )
    if not otp:
        return False, 'No active OTP found. Please request a new code.'
    if not otp.is_valid():
        return False, 'OTP has expired. Please request a new code.'
    if otp.code != code:
        return False, 'Invalid OTP code.'
    otp.is_used = True
    otp.save(update_fields=['is_used'])
    return True, 'OTP verified.'


def get_or_create_user(phone_number: str) -> tuple[User, bool]:
    return User.objects.get_or_create(phone_number=phone_number)


def issue_tokens(user: User) -> dict:
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}
