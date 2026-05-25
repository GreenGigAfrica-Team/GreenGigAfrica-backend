import json
import os
import firebase_admin
from firebase_admin import credentials, auth
from django.conf import settings

if not firebase_admin._apps:
    # Production (Render): load from FIREBASE_CREDENTIALS_JSON env var
    firebase_json = os.environ.get('FIREBASE_CREDENTIALS_JSON', '').strip()
    if firebase_json:
        cred = credentials.Certificate(json.loads(firebase_json))
    else:
        # Local dev: load from file path
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)

    firebase_admin.initialize_app(cred)


def verify_firebase_token(id_token):
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print("Firebase verification error:", e)
        return None
