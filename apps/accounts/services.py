from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from .models import OTPCode, User
import logging

logger = logging.getLogger(__name__)

# ── Rate limiting constants ───────────────────────────────────────────────────
OTP_RATE_LIMIT      = 3    # max OTP requests per window
OTP_RATE_WINDOW     = 600  # window in seconds (10 minutes)


def check_otp_rate_limit(phone_number: str) -> tuple[bool, int]:
    """
    Returns (allowed, seconds_until_reset).
    Tracks how many OTP requests a phone number has made in the last 10 minutes.
    Uses Django's cache (LocMemCache in dev, Redis in prod).
    """
    cache_key = f'otp_rate:{phone_number}'
    count = cache.get(cache_key, 0)

    if count >= OTP_RATE_LIMIT:
        # get remaining TTL so we can tell the user when to retry
        ttl = cache.ttl(cache_key) if hasattr(cache, 'ttl') else OTP_RATE_WINDOW
        return False, ttl or OTP_RATE_WINDOW

    # increment — set with full window TTL on first request, preserve TTL after
    if count == 0:
        cache.set(cache_key, 1, timeout=OTP_RATE_WINDOW)
    else:
        cache.set(cache_key, count + 1, timeout=OTP_RATE_WINDOW)

    return True, 0


def send_otp(phone_number: str) -> OTPCode:
    """
    Generate OTP, invalidate old ones, send via SMS.
    Raises ValueError if rate limit is exceeded.
    Returns the OTPCode instance.
    """
    allowed, wait = check_otp_rate_limit(phone_number)
    if not allowed:
        minutes = max(1, round(wait / 60))
        raise ValueError(
            f'Too many OTP requests. Please wait {minutes} minute(s) before trying again.'
        )

    # Invalidate any previous unused OTPs for this number
    OTPCode.objects.filter(phone_number=phone_number, is_used=False).update(is_used=True)

    code = OTPCode.generate_code()
    otp = OTPCode.objects.create(phone_number=phone_number, code=code)
    _dispatch_sms(phone_number, code)
    return otp


def _dispatch_sms(phone_number: str, code: str):
    print(f'\n[SMS DISPATCH] phone={phone_number} code={code}')

    # ── Dev mode: skip all providers, log code immediately ────────────────────
    if getattr(settings, 'DEV_MODE', False):
        print(f'\n{"=" * 50}')
        print(f'[DEV OTP]  {phone_number}  →  {code}')
        print(f'{"=" * 50}\n')
        logger.info('DEV_MODE on. OTP for %s: %s', phone_number, code)
        return

    msg = (
        f'Your GreenGig Africa verification code is: {code}. '
        f'Valid for {settings.OTP_EXPIRY_MINUTES} minutes. Do not share this code.'
    )

    # ── Termii ────────────────────────────────────────────────────────────────
    termii_key = getattr(settings, 'TERMII_API_KEY', '').strip()
    if termii_key:
        if _send_termii(phone_number, msg, termii_key):
            return

    # ── Africa's Talking ──────────────────────────────────────────────────────
    at_key  = getattr(settings, 'AT_API_KEY', '').strip()
    at_user = getattr(settings, 'AT_USERNAME', '').strip()
    if at_key and at_user:
        if _send_africastalking(phone_number, msg, at_user, at_key):
            return

    # ── Twilio ────────────────────────────────────────────────────────────────
    twilio_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '').strip()
    if twilio_sid:
        if _send_twilio(phone_number, msg):
            return

    # ── Dev fallback (no provider configured) ─────────────────────────────────
    print(f'\n{"=" * 50}')
    print(f'[DEV OTP]  {phone_number}  →  {code}')
    print(f'{"=" * 50}\n')
    logger.warning('No SMS provider configured. OTP for %s: %s', phone_number, code)


def _send_termii(phone_number: str, msg: str, api_key: str) -> bool:
    import requests as req

    print(f'[Termii] Trying token API for {phone_number} ...')
    try:
        resp = req.post(
            'https://api.termii.com/api/sms/otp/send',
            json={
                'api_key': api_key,
                'message_type': 'NUMERIC',
                'to': phone_number,
                'from': 'N-Alert',
                'channel': 'generic',
                'pin_attempts': 3,
                'pin_time_to_live': settings.OTP_EXPIRY_MINUTES,
                'pin_length': settings.OTP_LENGTH,
                'pin_placeholder': '< 1234 >',
                'message_text': (
                    f'Your GreenGig Africa code is < 1234 >. '
                    f'Valid for {settings.OTP_EXPIRY_MINUTES} minutes. Do not share.'
                ),
                'pin_type': 'NUMERIC',
            },
            timeout=15,
        )
        data = resp.json()
        logger.info('[Termii token] %s → %s', resp.status_code, data)
        if resp.status_code == 200 and data.get('pinId'):
            print(f'[SMS] Sent via Termii token API to {phone_number}')
            return True
        logger.warning('[Termii token] Failed: %s', data)
    except Exception as exc:
        logger.error('[Termii token] Exception: %s', exc)

    # fallback to generic SMS
    sender_id  = getattr(settings, 'TERMII_SENDER_ID', 'GreenGig')
    is_nigerian = phone_number.startswith('+234') or phone_number.startswith('234')
    channels   = ['generic', 'dnd'] if is_nigerian else ['generic']

    for channel in channels:
        try:
            resp = req.post(
                'https://api.termii.com/api/sms/send',
                json={
                    'to': phone_number, 'from': sender_id,
                    'sms': msg, 'type': 'plain',
                    'channel': channel, 'api_key': api_key,
                },
                timeout=15,
            )
            data = resp.json()
            logger.info('[Termii %s] %s → %s', channel, resp.status_code, data)
            if resp.status_code == 200 and (
                data.get('code') == 'ok'
                or data.get('message_id')
                or 'successfully' in str(data.get('message', '')).lower()
            ):
                print(f'[SMS] Sent via Termii ({channel}) to {phone_number}')
                return True
            logger.warning('[Termii %s] Failed: %s', channel, data)
        except Exception as exc:
            logger.error('[Termii %s] Exception: %s', channel, exc)

    logger.error('[Termii] All methods failed for %s', phone_number)
    return False


def _send_africastalking(phone_number: str, msg: str, username: str, api_key: str) -> bool:
    try:
        import africastalking
        africastalking.initialize(username, api_key)
        response = africastalking.SMS.send(msg, [phone_number])
        logger.info("[Africa's Talking] %s", response)
        print(f"[SMS] Sent via Africa's Talking to {phone_number}")
        return True
    except Exception as exc:
        logger.error("[Africa's Talking] Exception: %s", exc)
        return False


def _send_twilio(phone_number: str, msg: str) -> bool:
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=msg,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number,
        )
        print(f'[SMS] Sent via Twilio to {phone_number}')
        return True
    except Exception as exc:
        logger.error('[Twilio] Exception: %s', exc)
        return False


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
