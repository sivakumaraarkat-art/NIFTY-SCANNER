from kiteconnect.exceptions import TokenException

from zerodha_market_data.zerodha_connection import verify_connection


class DummyKite:
    def profile(self):
        raise TokenException("Incorrect `api_key` or `access_token`.", code=401)


def test_verify_connection_surfaces_actionable_message_for_expired_token():
    try:
        verify_connection(DummyKite())
        assert False, "Expected verify_connection to raise RuntimeError"
    except RuntimeError as exc:
        message = str(exc)
        assert "Zerodha access token is invalid or expired" in message
        assert "ZERODHA_ACCESS_TOKEN_FILE" in message
        assert "kite_auth_flow.py" in message
