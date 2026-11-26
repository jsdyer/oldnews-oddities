"""Private LOC collector header; never shipped to the browser or forwarded."""
import os
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

class LOCRequestError(RuntimeError):
    """A deliberately sanitized collector error."""

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise LOCRequestError('LOC redirected the request; no private header was forwarded.')

_OPENER = build_opener(NoRedirect())

def read_loc(url, *, timeout, limit, default_agent):
    # Fixed providers only: a private exemption must never reach mirrors, HTTP,
    # arbitrary ports, lookalike hosts or another destination through a redirect.
    parsed = urlsplit(url)
    try:
        allowed = parsed.scheme == 'https' and parsed.hostname in ('loc.gov', 'www.loc.gov') and parsed.port in (None, 443) and not parsed.username and not parsed.password and not parsed.fragment
    except ValueError:
        allowed = False
    if not allowed:
        raise LOCRequestError('LOC collector rejected a non-approved destination.')
    secret = os.environ.get('LOC_USER_AGENT', '').strip()
    if secret and (len(secret) > 512 or any(ord(c) < 32 or ord(c) > 126 for c in secret) or secret.lower().startswith('user-agent:') or secret.startswith(('"', "'"))):
        raise LOCRequestError('LOC_USER_AGENT must contain only the supplied single-line header value, without quotes or a prefix.')
    request = Request(url, headers={'User-Agent': secret or default_agent, 'Accept': 'application/json'})
    try:
        with _OPENER.open(request, timeout=timeout) as response:
            raw = response.read(limit + 1)
    except LOCRequestError:
        raise
    except HTTPError as exc:
        code = exc.code if isinstance(exc.code, int) else 'unknown'
        raise LOCRequestError(f'LOC request failed (HTTP {code}); previous capture retained.') from None
    except (URLError, OSError, TimeoutError, ValueError):
        raise LOCRequestError('LOC request failed (network/transport); previous capture retained.') from None
    if len(raw) > limit:
        raise LOCRequestError('LOC response exceeded the collection size limit.')
    # An upstream error/response can echo a request header. Refuse publication,
    # including an echoed token without its email prefix, before normalization.
    private_values = {secret, secret.rsplit(' ', 1)[-1]} if secret else set()
    try:
        decoded = json.dumps(json.loads(raw), ensure_ascii=False).encode('utf-8')
    except (ValueError, UnicodeError, TypeError):
        raise LOCRequestError('LOC did not return valid JSON; previous capture retained.') from None
    if any(value and (value.encode('ascii') in raw or value.encode('ascii') in decoded) for value in private_values):
        raise LOCRequestError('LOC response echoed a private header; response discarded.')
    return raw
