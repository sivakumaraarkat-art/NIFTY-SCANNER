import pandas as pd

from stock_universe.nse_stock_universe import _keep_stock_candidates


def test_removes_nav_products_but_keeps_company_shares():
    instruments = pd.DataFrame(
        {
            "tradingsymbol": [
                "AB10BKINAV",
                "ABSLLQINAV",
                "ABSMSCINAV",
                "RELIANCE",
            ],
            "name": [
                "NAV PRODUCT",
                "NAV PRODUCT",
                "NAV PRODUCT",
                "RELIANCE INDUSTRIES LIMITED",
            ],
        }
    )

    result = _keep_stock_candidates(instruments)

    assert result["tradingsymbol"].tolist() == ["RELIANCE"]
