"""Default security response headers."""

SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-site",
    # HSTS should be enabled at the edge/TLS terminator in production;
    # included when behind TLS-terminating proxy that preserves scheme.
    "X-XSS-Protection": "0",
}
