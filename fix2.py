from pathlib import Path
for name in ["src/scanners/run_options_intraday_scan_powerful_sl.py", "src/scanners/run_btst_options_scan_powerful_sl.py"]:
    text = Path(name).read_text('utf-8')
    text = text.replace('            print(f"\n📰 [NEWS INTEGRATION]', '            print(f"\n📰 [NEWS INTEGRATION]')
    text = text.replace('            print("\n⚠️  [NEWS INTEGRATION]', '            print("\n⚠️  [NEWS INTEGRATION]')
    Path(name).write_text(text, 'utf-8')
