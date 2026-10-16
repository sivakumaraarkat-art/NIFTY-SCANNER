import sys, os
sys.path.insert(0, os.getcwd())
sys.stdout.reconfigure(encoding='utf-8')
from src.scanners.options_data_provider import get_kite_client
from kiteconnect import KiteConnect

kite = get_kite_client()

# Place a GTT OCO (One Cancels Other) order for Crude Oil Put or Future
# Example template for setting a GTT Stop Loss and Target
try:
    # First search for the instrument token of CRUDEOIL26OCTFUT or the put option
    instruments = kite.instruments("MCX")
    crude_token = None
    for inst in instruments:
        if inst["tradingsymbol"] == "CRUDEOIL26OCTFUT":
            crude_token = inst["instrument_token"]
            break

    print(f"Crude Oct Future Token: {crude_token}")

    # Note: To place GTT via Zerodha Kite Connect API:
    # kite.place_gtt(
    #     trigger_type=kite.GTT_TYPE_OCO,
    #     tradingsymbol="CRUDEOIL26OCTFUT",
    #     exchange="MCX",
    #     trigger_values=[9100.0, 9400.0], # Target and Stoploss triggers
    #     last_price=9246.0,
    #     orders=[...]
    # )
    print("GTT structure ready. Live execution requires explicit user confirmation.")
except Exception as e:
    print("Error:", e)
