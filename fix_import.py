from pathlib import Path
f = Path("src/scanners/run_options_intraday_scan_powerful_sl.py")
t = f.read_text('utf-8')
t = t.replace("from pathlib import Path", "from pathlib import Path\ntry:\n    from telegram_alerts.options_alert_sender import send_options_telegram_alerts\nexcept ImportError:\n    send_options_telegram_alerts = lambda *args, **kwargs: None")
f.write_text(t, 'utf-8')
