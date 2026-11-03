from starlette.responses import PlainTextResponse


class ProductionHTTPSMiddleware:
    """Require HTTPS at the trusted reverse proxy for every non-health HTTP request.

    The production Nginx configuration overwrites X-Forwarded-Proto with its
    actual TLS scheme. Backend containers are not host-published; never trust
    this header if the API is exposed directly to an untrusted network.
    """

    def __init__(self, app, *, enabled: bool):
        self.app = app
        self.enabled = enabled

    async def __call__(self, scope, receive, send):
        if self.enabled and scope["type"] == "http" and scope.get("path") != "/health":
            headers = {key.lower(): value for key, value in scope.get("headers", [])}
            forwarded_proto = headers.get(b"x-forwarded-proto", b"").decode("latin-1").lower()
            if forwarded_proto != "https":
                response = PlainTextResponse("HTTPS is required.", status_code=400)
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)
