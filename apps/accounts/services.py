from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from .models import OTPCode, User
import logging

logger = logging.getLogger(__name__)


def send_otp(phone_number: str) -> OTPCode:
    """Generate OTP and send via SMS. Returns the OTPCode instance."""
    OTPCode.objects.filter(phone_number=phone_number, is_used=False).update(is_used=True)
    code = OTPCode.generate_code()
    otp = OTPCode.objects.create(phone_number=phone_number, code=code)
    _dispatch_sms(phone_number, code)
    return otp


def _dispatch_sms(phone_number: str, code: str):
    msg = f'Your GreenGig Africa code is: {code}. Valid for {settings.OTP_EXPIRY_MINUTES} minutes.'

    # ── Termii ────────────────────────────────────────────────
    termii_key = getattr(settings, 'TERMII_API_KEY', '').strip()
    if termii_key:
        try:
            import requests as req
            response = req.post('https://api.termii.com/api/sms/send', json={
                'to': phone_number,
                'from': 'N-Alert',
                'sms': msg,
                'type': 'plain',
                'channel': 'dnd',
                'api_key': termii_key,
            })
            data = response.json()
            print(f'[SMS] Termii response: {response.status_code} — {data}')
            if response.status_code == 200:
                return
            else:
                print(f'[SMS ERROR] Termii failed: {data}')
        except Exception as e:
            print(f'[SMS ERROR] Termii exception: {e}')

    # ── Africa's Talking ──────────────────────────────────────
    at_key = getattr(settings, 'AT_API_KEY', '').strip()
    at_user = getattr(settings, 'AT_USERNAME', '').strip()
    if at_key and at_user:
        try:
            import africastalking
            africastalking.initialize(at_user, at_key)
            sms = africastalking.SMS
            response = sms.send(msg, [phone_number])
            logger.info('Africa\'s Talking SMS sent: %s', response)
            print(f'[SMS] Sent via Africa\'s Talking to {phone_number}')
            return
        except Exception as e:
            logger.error('Africa\'s Talking SMS failed: %s', e)
            print(f'[SMS ERROR] Africa\'s Talking failed: {e}')

    # ── Twilio fallback ───────────────────────────────────────
    twilio_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '').strip()
    if twilio_sid:
        try:
            from twilio.rest import Client
            client = Client(twilio_sid, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(body=msg, from_=settings.TWILIO_PHONE_NUMBER, to=phone_number)
            print(f'[SMS] Sent via Twilio to {phone_number}')
            return
        except Exception as e:
            logger.error('Twilio SMS failed: %s', e)
            print(f'[SMS ERROR] Twilio failed: {e}')

    # ── Dev fallback — always print to logs ──────────────────
    print(f'\n{"="*50}')
    print(f'[OTP] {phone_number} → {code}')
    print(f'{"="*50}\n')
    logger.warning('No SMS provider configured. OTP for %s: %s', phone_number, code)


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
