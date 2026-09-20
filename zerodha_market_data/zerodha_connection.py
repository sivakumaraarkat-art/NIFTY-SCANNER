from kiteconnect import KiteConnect
from kiteconnect.exceptions import TokenException

from .shared_token_reader import read_shared_access_token


def create_zerodha_client(settings):
    if not settings.zerodha_api_key:
        raise ValueError("ZERODHA_API_KEY is missing in .env")
    kite = KiteConnect(api_key=settings.zerodha_api_key)
    kite.set_access_token(read_shared_access_token(settings.access_token_file))
    return kite


def verify_connection(kite):
    try:
        return kite.profile()
    except TokenException as exc:
        raise RuntimeError(
            "Zerodha access token is invalid or expired. "
            "Regenerate the session token and refresh the token file used by "
            "ZERODHA_ACCESS_TOKEN_FILE (for example via kite_auth_flow.py)."
        ) from exc
