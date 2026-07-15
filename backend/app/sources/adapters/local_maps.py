"""Tier C adapters — local businesses: OpenStreetMap Overpass (+Nominatim geocode), Yelp."""
from __future__ import annotations

from typing import List

import httpx

from ...config import get_settings
from ..base import Candidate, SourceAdapter

T = 30.0


class OverpassAdapter(SourceAdapter):
    """No key. Geocode city (Nominatim) -> businesses in bbox (Overpass)."""
    name, tier = "overpass", "C"

    def _bbox(self, location: str) -> tuple[float, float, float, float] | None:
        s = get_settings()
        r = httpx.get("https://nominatim.openstreetmap.org/search",
                      params={"q": location, "format": "json", "limit": 1},
                      headers={"User-Agent": s.NOMINATIM_USER_AGENT}, timeout=T)
        r.raise_for_status()
        rows = r.json()
        if not rows:
            return None
        bb = rows[0]["boundingbox"]  # [s, n, w, e]
        return float(bb[0]), float(bb[2]), float(bb[1]), float(bb[3])  # s,w,n,e

    def _search(self, query, *, location, limit) -> List[Candidate]:
        if not location:
            return []
        box = self._bbox(location)
        if not box:
            return []
        s, w, n, e = box
        # match name OR shop/amenity/craft tags against the niche keyword
        kw = query.split()[0] if query else "shop"
        oql = f"""[out:json][timeout:25];
(
  node["name"~"{kw}",i]({s},{w},{n},{e});
  node["shop"~"{kw}",i]({s},{w},{n},{e});
  node["amenity"~"{kw}",i]({s},{w},{n},{e});
  node["craft"~"{kw}",i]({s},{w},{n},{e});
);
out body {min(limit * 3, 60)};"""
        r = httpx.post(get_settings().OVERPASS_URL, data={"data": oql}, timeout=T)
        r.raise_for_status()
        out: List[Candidate] = []
        for el in r.json().get("elements", []):
            tags = el.get("tags", {})
            if not tags.get("name"):
                continue
            contact = tags.get("contact:email") or tags.get("email") or tags.get("phone") or tags.get("contact:phone", "")
            out.append(Candidate(
                title=tags["name"],
                url=tags.get("website") or tags.get("contact:website", ""),
                snippet=", ".join(f"{k}={v}" for k, v in tags.items()
                                  if k in ("shop", "amenity", "craft", "cuisine", "addr:street", "addr:city"))[:300],
                source=self.name, tier=self.tier, kind="company", location=location,
                contact_hint=contact, extra={"osm_id": el.get("id")}))
            if len(out) >= limit:
                break
        return out


class YelpAdapter(SourceAdapter):
    name, tier = "yelp", "C"

    def available(self) -> bool:
        return bool(get_settings().YELP_API_KEY)

    def _search(self, query, *, location, limit) -> List[Candidate]:
        if not location:
            return []
        r = httpx.get("https://api.yelp.com/v3/businesses/search",
                      params={"term": query, "location": location, "limit": min(limit, 20)},
                      headers={"Authorization": f"Bearer {get_settings().YELP_API_KEY}"}, timeout=T)
        r.raise_for_status()
        return [Candidate(title=b.get("name", ""), url=b.get("url", ""),
                          snippet=", ".join(c.get("title", "") for c in b.get("categories", [])),
                          source=self.name, tier=self.tier, kind="company",
                          location=", ".join((b.get("location") or {}).get("display_address", [])),
                          contact_hint=b.get("display_phone", ""),
                          extra={"rating": b.get("rating"), "reviews": b.get("review_count")})
                for b in r.json().get("businesses", [])]
