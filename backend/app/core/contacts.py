"""Contact extraction + verification (the outreach waterfall).

- pull emails / phones / socials from a company's pages (root + /contact + /about)
- guess a pattern email when a person name + domain are known
- verify the best email via Reoon / MillionVerifier free tiers (if keys present)
Everything is best-effort and never raises. vibe 13/17 (PII handled carefully).
"""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import httpx

from ..config import get_settings
from .security import safe_fetch_text

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d[\d\-\s().]{7,}\d)")
SOCIAL_HOSTS = ("linkedin.com", "instagram.com", "facebook.com", "twitter.com", "x.com", "wa.me")
# junk emails we never want to pitch
_BAD_EMAIL = ("example.com", "sentry.io", "wixpress.com", ".png", ".jpg", ".gif", "@2x", "u003e")
CONTACT_PATHS = ("", "/contact", "/contact-us", "/contacts", "/about", "/about-us")


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().lstrip("www.")
    except Exception:  # noqa: BLE001
        return ""


def _clean_emails(text: str, domain: str) -> list[str]:
    found = []
    for e in EMAIL_RE.findall(text):
        el = e.lower()
        if any(b in el for b in _BAD_EMAIL):
            continue
        found.append(el)
    # prefer emails on the company's own domain, then role inboxes, then rest
    def rank(e: str) -> tuple:
        role = any(e.startswith(p) for p in ("contact@", "info@", "hello@", "sales@", "admin@"))
        return (0 if domain and domain in e else 1, 0 if role else 1)
    uniq = sorted(dict.fromkeys(found), key=rank)
    return uniq[:5]


def scrape_contacts(url: str) -> dict:
    """Visit root + a few contact pages; collect emails/phones/socials."""
    out: dict = {"emails": [], "phones": [], "socials": []}
    if not url:
        return out
    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    domain = _domain(url)
    ua = get_settings().NOMINATIM_USER_AGENT
    seen_pages, emails, phones, socials = set(), [], [], []
    for path in CONTACT_PATHS:
        page = urljoin(base + "/", path.lstrip("/")) if path else url
        if page in seen_pages:
            continue
        seen_pages.add(page)
        try:
            html = safe_fetch_text(page, ua)
        except Exception:  # noqa: BLE001 — page missing / blocked / SSRF: skip
            continue
        # mailto: and tel: links are the cleanest signal
        emails += [m.lower() for m in re.findall(r"mailto:([^\"'?>\s]+)", html)]
        phones += re.findall(r"tel:([+\d\-\s().]{7,})", html)
        for m in re.findall(r'href=["\']?(https?://[^"\'>\s]+)', html):
            if any(h in m.lower() for h in SOCIAL_HOSTS):
                socials.append(m)
        text = re.sub(r"<[^>]+>", " ", html)
        emails += _clean_emails(text, domain)
        phones += [p.strip() for p in PHONE_RE.findall(text)]
    out["emails"] = _clean_emails(" ".join(dict.fromkeys(emails)), domain)
    out["phones"] = list(dict.fromkeys(p.strip() for p in phones if len(re.sub(r"\D", "", p)) >= 8))[:3]
    out["socials"] = list(dict.fromkeys(socials))[:4]
    return out


def guess_email(person: str, domain: str) -> str:
    """first@domain / first.last@domain — only when we know a real name + domain."""
    if not (person and domain):
        return ""
    parts = re.sub(r"[^a-z ]", "", person.lower()).split()
    if not parts:
        return ""
    first = parts[0]
    return f"{first}@{domain}" if len(parts) == 1 else f"{first}.{parts[-1]}@{domain}"


def verify_email(email: str) -> str:
    """-> 'valid' | 'risky' | 'invalid' | 'unverified'. Uses Reoon then MillionVerifier."""
    if not email:
        return "unverified"
    s = get_settings()
    try:
        if s.REOON_API_KEY:
            r = httpx.get("https://emailverifier.reoon.com/api/v1/verify",
                          params={"email": email, "key": s.REOON_API_KEY, "mode": "quick"}, timeout=15)
            st = str(r.json().get("status", "")).lower()
            return {"valid": "valid", "safe": "valid", "invalid": "invalid",
                    "disposable": "risky", "spamtrap": "invalid", "unknown": "risky",
                    "catch_all": "risky"}.get(st, "risky")
    except Exception:  # noqa: BLE001
        pass
    try:
        if s.MILLIONVERIFIER_API_KEY:
            r = httpx.get("https://api.millionverifier.com/api/v3/",
                          params={"api": s.MILLIONVERIFIER_API_KEY, "email": email}, timeout=15)
            res = str(r.json().get("result", "")).lower()
            return {"ok": "valid", "catch_all": "risky", "unknown": "risky",
                    "invalid": "invalid", "disposable": "risky"}.get(res, "risky")
    except Exception:  # noqa: BLE001
        pass
    return "unverified"


def best_contact(url: str, person: str, inline_hint: str = "") -> dict:
    """Full waterfall -> {email, email_status, phone, socials, all_emails}."""
    domain = _domain(url)
    scraped = scrape_contacts(url)
    emails = list(scraped["emails"])
    phones = list(scraped["phones"])
    # inline hint from the source (e.g. OSM tag)
    if inline_hint:
        m = EMAIL_RE.search(inline_hint)
        if m:
            emails.insert(0, m.group(0).lower())
        elif re.sub(r"\D", "", inline_hint):
            phones.insert(0, inline_hint)
    email = emails[0] if emails else guess_email(person, domain)
    guessed = bool(email) and email not in emails
    status = verify_email(email) if email else "unverified"
    if guessed and status == "unverified":
        status = "guessed"
    return {"email": email, "email_status": status,
            "phone": phones[0] if phones else "",
            "socials": scraped["socials"], "all_emails": emails[:5]}
