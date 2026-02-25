import base64, hmac, hashlib, sys

def add_padding(s):
    return s + '=' * (-len(s) % 4)

# Token from user's curl
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6dHJ1ZSwiaWF0IjoxNzcxMjQ1MTA5LCJqdGkiOiI3MDBhY2NkZi1hYWYxLTQ1ZDEtYmYyMy03NGU5MjhjYWVmZmUiLCJ0eXBlIjoiYWNjZXNzIiwic3ViIjo1LCJuYmYiOjE3NzEyNDUxMDksImV4cCI6MTc3MTI0NjAwOSwicm9sZV9uYW1lIjoiU0FMRVMifQ.3InzcjYrhurS2VV3BgunKiYDclGJg4AnFPzk3G-Sbbk"
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
