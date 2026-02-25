import base64, hmac, hashlib, sys

def add_padding(s):
    return s + '=' * (-len(s) % 4)

# Token and secret (from your message)
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6dHJ1ZSwiaWF0IjoxNzcxMjQyODI2LCJqdGkiOiIyNmIxNzYxZS1hMmQ3LTQxNmMtYmZkYy1iNzNmNzM2MDI4NGUiLCJ0eXBlIjoiYWNjZXNzIiwic3ViIjp7InVzZXJfaWQiOjUsInJvbGVfbmFtZSI6IlNBTEVTIn0sIm5iZiI6MTc3MTI0MjgyNiwiZXhwIjoxNzcxMjQzNzI2fQ._WpunSFT2hBtc825j_DDjn6YNOoA4L5k2QZ7cpWiq80"
secret = "fallback-secret-key"

try:
    header_payload, sig = token.rsplit('.', 1)
    sig_bytes = base64.urlsafe_b64decode(add_padding(sig))
    expected = hmac.new(secret.encode(), header_payload.encode(), hashlib.sha256).digest()
    if hmac.compare_digest(sig_bytes, expected):
        print("signature OK")
    else:
        print("signature verify failed")
        print("expected (b64url):", base64.urlsafe_b64encode(expected).rstrip(b'=').decode())
        print("actual (b64url):", sig)
except Exception as e:
    print("error:", e)
    sys.exit(1)

sys.exit(0)
