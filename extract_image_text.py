"""
extract_image_text.py
Extracts text from diwali_pick.png using Windows native OCR or pytesseract/easyocr.
"""
import sys
import os
from pathlib import Path

IMG_PATH = Path("diwali_pick.png").resolve()

def try_pytesseract():
    try:
        from PIL import Image
        import pytesseract
        text = pytesseract.image_to_string(Image.open(IMG_PATH))
        if text.strip():
            print("=== OCR EXTRACTED TEXT (pytesseract) ===")
            print(text)
            return True
    except Exception as e:
        pass
    return False

def try_easyocr():
    try:
        import easyocr
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(str(IMG_PATH))
        if results:
            print("=== OCR EXTRACTED TEXT (easyocr) ===")
            for bbox, text, prob in results:
                print(f"[{prob:.2f}] {text}")
            return True
    except Exception as e:
        pass
    return False

def try_windows_ocr_ps():
    import subprocess
    ps_cmd = f"""
    Add-Type -AssemblyName System.Drawing
    [Windows.Media.Ocr.OcrEngine, Windows.Foundation.UniversalApiContract, ContentType = WindowsRuntime] | Out-Null
    [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation.UniversalApiContract, ContentType = WindowsRuntime] | Out-Null
    [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime] | Out-Null

    $file = [Windows.Storage.StorageFile]::GetFileFromPathAsync("{str(IMG_PATH)}").GetAwaiter().GetResult()
    $stream = $file.OpenAsync([Windows.Storage.FileAccessMode]::Read).GetAwaiter().GetResult()
    $decoder = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream).GetAwaiter().GetResult()
    $bitmap = $decoder.GetSoftwareBitmapAsync().GetAwaiter().GetResult()
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
    $result = $engine.RecognizeAsync($bitmap).GetAwaiter().GetResult()
    $result.Lines | ForEach-Object {{ $_.Text }}
    """
    try:
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
        if res.stdout.strip():
            print("=== OCR EXTRACTED TEXT (Windows Native OCR) ===")
            print(res.stdout.strip())
            return True
        else:
            if res.stderr:
                print(f"PS Error: {res.stderr}")
    except Exception as e:
        print(f"Subprocess error: {e}")
    return False

def main():
    if not IMG_PATH.exists():
        print(f"File not found: {IMG_PATH}")
        return

    print(f"Reading image: {IMG_PATH}")
    if try_pytesseract():
        return
    if try_easyocr():
        return
    if try_windows_ocr_ps():
        return
    print("Could not extract text using automated OCR.")

if __name__ == "__main__":
    main()
