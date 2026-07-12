"""SigV4 signing for AgentCore Gateway calls (Gateway authorizerType AWS_IAM).

MCP streamable HTTP sends several POST requests with JSON bodies, and SigV4 covers the method,
URL, body hash and timestamp, so every request is signed when it is sent (not once up front).
"""

import botocore.session
import httpx
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

SERVICE = "bedrock-agentcore"
# Headers that go into the signature; everything else (incl. MCP session headers) is sent unsigned.
_SIGNED_HEADERS = ("host", "content-type")


class GatewaySigV4Auth(httpx.Auth):
    requires_request_body = True

    def __init__(self, region: str, credentials=None):
        self.region = region
        self._credentials = credentials

    def _frozen_credentials(self):
        creds = self._credentials or botocore.session.get_session().get_credentials()
        if creds is None:
            raise RuntimeError("No AWS credentials available to sign Gateway requests")
        # Refreshable role credentials are re-read on every request.
        return creds.get_frozen_credentials() if hasattr(creds, "get_frozen_credentials") else creds

    def auth_flow(self, request: httpx.Request):
        headers = {k: v for k, v in request.headers.items() if k.lower() in _SIGNED_HEADERS}
        aws_request = AWSRequest(method=request.method, url=str(request.url), data=request.content, headers=headers)
        SigV4Auth(self._frozen_credentials(), SERVICE, self.region).add_auth(aws_request)
        for name in ("Authorization", "X-Amz-Date", "X-Amz-Security-Token"):
            if name in aws_request.headers:
                request.headers[name] = aws_request.headers[name]
        yield request
