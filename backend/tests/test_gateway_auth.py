import httpx
from botocore.credentials import Credentials

from gateway_auth import GatewaySigV4Auth

CREDS = Credentials("AKIDEXAMPLE", "secret", "token")
URL = "https://example-gateway.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"


def _signed(method: str, body: bytes = b"") -> httpx.Request:
    req = httpx.Request(method, URL, content=body, headers={"content-type": "application/json", "mcp-session-id": "s1"})
    flow = GatewaySigV4Auth("us-east-1", credentials=CREDS).auth_flow(req)
    return next(flow)


def test_every_request_gets_its_own_sigv4_signature():
    a = _signed("POST", b'{"jsonrpc":"2.0","id":1,"method":"initialize"}')
    b = _signed("POST", b'{"jsonrpc":"2.0","id":2,"method":"tools/list"}')
    for r in (a, b):
        auth = r.headers["Authorization"]
        assert auth.startswith("AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/")
        assert "/us-east-1/bedrock-agentcore/aws4_request" in auth
        assert "SignedHeaders=content-type;host;x-amz-date;x-amz-security-token" in auth
        assert r.headers["X-Amz-Security-Token"] == "token"
        assert r.headers["mcp-session-id"] == "s1"  # untouched, not signed
    # body is part of the signature, so different payloads give different signatures
    assert a.headers["Authorization"].split("Signature=")[1] != b.headers["Authorization"].split("Signature=")[1]


def test_get_requests_are_signed_too():
    r = _signed("GET")
    assert r.headers["Authorization"].startswith("AWS4-HMAC-SHA256 ")
