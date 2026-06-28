"""TenderAPI MCP server: exposes BOAMP + TED procurement data as MCP tools.

Thin wrapper over the public REST API at https://tenderapi.fr.

Config (env vars):
  TENDERAPI_KEY       (required) obtain at https://tenderapi.fr/
  TENDERAPI_BASE_URL  (optional) default https://tenderapi.fr
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from . import __version__

BASE_URL = os.getenv("TENDERAPI_BASE_URL", "https://tenderapi.fr").rstrip("/")
API_KEY = os.getenv("TENDERAPI_KEY", "")
TIMEOUT = float(os.getenv("TENDERAPI_TIMEOUT", "30"))

mcp = FastMCP("tenderapi")


def _headers() -> dict[str, str]:
    if not API_KEY:
        raise RuntimeError(
            "TENDERAPI_KEY env var is not set. Get a free key at https://tenderapi.fr/"
        )
    return {"X-API-Key": API_KEY, "User-Agent": f"tenderapi-mcp/{__version__}"}


def _drop_none(params: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in params.items() if v is not None}


async def _request(
    method: str,
    path: str,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.request(
            method,
            f"{BASE_URL}{path}",
            params=params or None,
            json=json_body,
            headers=_headers(),
        )
    if r.status_code >= 400:
        raise RuntimeError(f"TenderAPI {r.status_code} on {method} {path}: {r.text[:400]}")
    if r.status_code == 204 or not r.content:
        return {"ok": True}
    return r.json()


async def _get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await _request("GET", path, params=params)


# ──────────────────────────────────────────────────────────────────────────────
# Search
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool()
async def search_tenders(
    cpv: str | None = None,
    cpv_family: str | None = None,
    descripteur: str | None = None,
    keyword: str | None = None,
    region: str | None = None,
    department: str | None = None,
    country: str | None = None,
    source: str | None = None,
    include_planning: bool = False,
    status: str | None = None,
    procedure_type: str | None = None,
    contract_type: str | None = None,
    buyer_siret: str | None = None,
    buyer_keyword: str | None = None,
    budget_min: float | None = None,
    budget_max: float | None = None,
    include_null_budget: bool = False,
    deadline_after: str | None = None,
    deadline_before: str | None = None,
    include_null_deadline: bool = False,
    published_after: str | None = None,
    published_before: str | None = None,
    page: int = 1,
    page_size: int = 20,
    limit: int | None = None,
) -> dict[str, Any]:
    """Search public procurement tenders from BOAMP (France) and TED (EU).

    Returns a paginated list of tender notices matching the filters.

    Args:
        cpv: Exact CPV code (e.g. "72000000" for IT services).
        cpv_family: 2-digit CPV family prefix (e.g. "72" matches all IT-services CPVs).
        descripteur: BOAMP business descripteur(s), comma-separated (e.g. "couverture" or "etude,btp"). Case-insensitive substring match; targets MAPA notices that carry no CPV code.
        keyword: Full-text search across title and description (accent-insensitive). Words are combined with AND — every word must appear in the SAME notice, so a long space-separated list (e.g. "bathymetric hydrographic survey lidar coastal") almost always returns zero results. For a broad topic search, join synonyms with the OR operator instead, e.g. keyword=bathymétrie OR hydrographie OR lidar OR dredging. TED notices are indexed in their publication language (FR/DE/ES/IT/EN), so include each concept in the relevant languages joined by OR. Comma- or pipe-separated lists are NOT parsed as OR.
        region: French region slug, lowercase (e.g. "occitanie", "ile-de-france", "bretagne").
        department: French department code (e.g. "75", "2A", "974").
        country: ISO 3166-1 alpha-2 country code (e.g. "FR", "DE"). Alpha-3 (e.g. "FRA") also accepted for supported countries. Defaults to FR for BOAMP.
        source: "boamp" (France) or "ted" (FR/DE/IT/ES/UK). Omit to include both.
        include_planning: When True, include TED prior-information notices (PINs) that announce upcoming procurements. Excluded by default (not yet biddable, no deadline).
        status: "open" | "closed" | "awarded" | "cancelled".
        procedure_type: Procurement procedure (e.g. "open", "restricted", "negotiated").
        contract_type: "works" | "supplies" | "services".
        buyer_siret: Exact SIRET of the French contracting authority (14 digits).
        buyer_keyword: Partial match on buyer name.
        budget_min: Minimum estimated budget, EUR.
        budget_max: Maximum estimated budget, EUR.
        include_null_budget: When True, keep tenders with no budget through budget_min/budget_max filters. Excluded by default (budget is sparse).
        deadline_after: ISO date (YYYY-MM-DD); submission deadline after this date.
        deadline_before: ISO date; submission deadline before this date.
        include_null_deadline: When True, keep tenders with no submission deadline through deadline_after/deadline_before filters. Excluded by default (many TED notices carry no parsed deadline).
        published_after: ISO date; published after this date.
        published_before: ISO date; published before this date.
        page: 1-indexed page number.
        page_size: Results per page. Max depends on tier: 20 (free), 50 (Starter/Pro).
        limit: Alternative to page_size, hard cap on results (server-defined max).

    Returns a dict with keys: total, page, page_size, results (list of tenders).
    """
    params = _drop_none({
        "cpv": cpv, "cpv_family": cpv_family, "descripteur": descripteur, "keyword": keyword,
        "region": region, "department": department, "country": country,
        "source": source, "status": status, "include_planning": include_planning,
        "procedure_type": procedure_type, "contract_type": contract_type,
        "buyer_siret": buyer_siret, "buyer_keyword": buyer_keyword,
        "budget_min": budget_min, "budget_max": budget_max,
        "include_null_budget": include_null_budget,
        "deadline_after": deadline_after, "deadline_before": deadline_before,
        "include_null_deadline": include_null_deadline,
        "published_after": published_after, "published_before": published_before,
        "page": page, "page_size": page_size, "limit": limit,
    })
    return await _get("/tenders", params)


@mcp.tool()
async def get_tender(tender_id: str) -> dict[str, Any]:
    """Fetch the full record of a single tender by its ID.

    Use this after `search_tenders` to get the complete details (description,
    documents, contact info, raw fields) of a specific notice.
    """
    return await _get(f"/tenders/{tender_id}")


@mcp.tool()
async def search_awards(
    cpv: str | None = None,
    cpv_family: str | None = None,
    descripteur: str | None = None,
    region: str | None = None,
    department: str | None = None,
    country: str | None = None,
    source: str | None = None,
    outcome: str | None = None,
    winner_name: str | None = None,
    winner_siret: str | None = None,
    buyer_siret: str | None = None,
    buyer_keyword: str | None = None,
    keyword: str | None = None,
    amount_min: float | None = None,
    amount_max: float | None = None,
    awarded_after: str | None = None,
    awarded_before: str | None = None,
    has_parent_tender: bool | None = None,
    published_after: str | None = None,
    published_before: str | None = None,
    page: int = 1,
    page_size: int = 20,
    limit: int | None = None,
) -> dict[str, Any]:
    """Search award notices: who won which public contract, for how much.

    Requires Starter tier or above. If the call returns 402/403, suggest the
    user upgrade via `upgrade_tier`.

    Args:
        cpv: Exact CPV code.
        cpv_family: 2-digit CPV family prefix.
        descripteur: BOAMP business descripteur(s), comma-separated; substring match for notices without a CPV code.
        region: French region slug.
        department: French department code.
        country: ISO 3166-1 alpha-2 country code (e.g. "FR", "DE"); alpha-3 also accepted for supported countries.
        source: "boamp" or "ted".
        outcome: Filter by award result: "awarded" | "cancelled" (comma-separated list accepted, e.g. "awarded,cancelled").
        winner_name: Partial match on winning company name.
        winner_siret: Exact winner SIRET (14 digits).
        buyer_siret: Exact buyer SIRET.
        buyer_keyword: Partial match on buyer name.
        keyword: Full-text search across the award notice text (accent-insensitive). Words are combined with AND — every word must appear in the same notice. Join synonyms with the OR operator for a broad search, e.g. keyword=dragage OR dredging OR draguage. Comma- or pipe-separated lists are NOT parsed as OR.
        amount_min: Minimum contract amount, EUR.
        amount_max: Maximum contract amount, EUR.
        awarded_after: ISO date; award date after this.
        awarded_before: ISO date; award date before this.
        has_parent_tender: Filter by linkage to the originating tender (AO). True = only awards linked to their tender; False = only standalone awards (negotiated/direct procedures with no published prior notice). Omit for all.
        published_after: ISO date.
        published_before: ISO date.
        page / page_size / limit: Pagination.
    """
    params = _drop_none({
        "cpv": cpv, "cpv_family": cpv_family, "descripteur": descripteur,
        "region": region, "department": department, "country": country,
        "source": source, "outcome": outcome,
        "winner_name": winner_name, "winner_siret": winner_siret,
        "buyer_siret": buyer_siret, "buyer_keyword": buyer_keyword, "keyword": keyword,
        "amount_min": amount_min, "amount_max": amount_max,
        "awarded_after": awarded_after, "awarded_before": awarded_before,
        "has_parent_tender": has_parent_tender,
        "published_after": published_after, "published_before": published_before,
        "page": page, "page_size": page_size, "limit": limit,
    })
    return await _get("/awards", params)


@mcp.tool()
async def get_award(award_id: str) -> dict[str, Any]:
    """Fetch the full record of a single award notice by its ID.

    Requires Starter tier or above.
    """
    return await _get(f"/awards/{award_id}")


@mcp.tool()
async def winner_intel(
    cpv: str | None = None,
    cpv_family: str | None = None,
    region: str | None = None,
    country: str | None = None,
    year: int | None = None,
    winner_siret: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Aggregated winner statistics: top companies by contract count and total amount.

    Requires Pro tier. Use for competitive intelligence: "which companies win
    IT contracts in Occitanie in 2025?" or "what has SIRET 12345678901234 won
    across all sectors?".

    Args:
        cpv: CPV code filter.
        cpv_family: 2-digit CPV family prefix filter.
        region: Region slug.
        country: ISO 3166-1 alpha-2 country code (e.g. "FR", "DE"); alpha-3 also accepted for supported countries.
        year: Integer year filter (e.g. 2025).
        winner_siret: Pin to a single company.
        limit: Top N results (default 10, max 50).
    """
    params = _drop_none({
        "cpv": cpv, "cpv_family": cpv_family, "region": region, "country": country,
        "year": year, "winner_siret": winner_siret, "limit": limit,
    })
    return await _get("/awards/winner-intel", params)


# ──────────────────────────────────────────────────────────────────────────────
# Account / quota
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool()
async def me() -> dict[str, Any]:
    """Return the authenticated key's tier, quota, and available features.

    Useful for the agent to check quota before launching many calls or to pick
    a tier-appropriate strategy. Response includes `tier`, `quota_day_limit`,
    `quota_remaining_today`, `requests_today`, `requests_month`, `features`.
    """
    return await _get("/me")


# ──────────────────────────────────────────────────────────────────────────────
# Matching profiles (email & webhook alerts)
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool()
async def list_profiles() -> dict[str, Any]:
    """List the matching profiles owned by the authenticated key.

    A profile = a saved filter + a delivery channel. New tenders matching the
    profile's criteria are delivered automatically, either as a daily EMAIL
    digest (channel="email") or pushed to a WEBHOOK (channel="webhook").
    """
    return await _get("/profiles")


@mcp.tool()
async def get_profile(profile_id: int) -> dict[str, Any]:
    """Fetch a single matching profile by its integer ID."""
    return await _get(f"/profiles/{profile_id}")


@mcp.tool()
async def create_profile(
    name: str,
    channel: str | None = None,
    webhook_url: str | None = None,
    email_to: str | None = None,
    siret: str | None = None,
    keywords: list[str] | None = None,
    cpv_codes: list[str] | None = None,
    regions: list[str] | None = None,
    departments: list[str] | None = None,
    descripteur_keywords: list[str] | None = None,
    budget_min: float | None = None,
    budget_max: float | None = None,
    match_cpv_family: bool | None = None,
    match_descripteur: bool | None = None,
    active: bool | None = None,
) -> dict[str, Any]:
    """Create a matching profile. New tenders matching the filters are delivered
    automatically as a daily EMAIL digest (channel="email") or pushed to a
    WEBHOOK (channel="webhook").

    At least one filter (keywords, cpv_codes, regions, departments, siret,
    descripteur_keywords, or a budget range) should be set, otherwise the
    profile matches everything.

    Args:
        name: Human-readable label.
        channel: "email" for a daily email digest, or "webhook" for HTTP push.
            Defaults to "webhook" server-side if omitted.
        webhook_url: HTTPS endpoint that will receive POST notifications (for channel="webhook").
        email_to: Recipient address for the daily digest (for channel="email").
        siret: Restrict to a specific buyer.
        keywords: List of substrings matched against title/description.
        cpv_codes: List of exact CPV codes.
        regions: List of French region slugs.
        departments: List of French department codes.
        descripteur_keywords: List of BOAMP business descripteurs (max 20); requires match_descripteur=True. Targets MAPA notices that carry no CPV code.
        budget_min / budget_max: Budget window in EUR.
        match_cpv_family: If true, `cpv_codes` are treated as 2-digit family
            prefixes (e.g. "72" matches every CPV starting with 72).
        match_descripteur: If true, enable matching on `descripteur_keywords` (default false).
        active: Whether the profile is active (default true). Set false to pause webhook deliveries without deleting it.
    """
    body = _drop_none({
        "name": name, "channel": channel, "webhook_url": webhook_url,
        "email_to": email_to, "siret": siret,
        "keywords": keywords, "cpv_codes": cpv_codes,
        "regions": regions, "departments": departments,
        "descripteur_keywords": descripteur_keywords,
        "budget_min": budget_min, "budget_max": budget_max,
        "match_cpv_family": match_cpv_family, "match_descripteur": match_descripteur,
        "active": active,
    })
    return await _request("POST", "/profiles", json_body=body)


@mcp.tool()
async def update_profile(
    profile_id: int,
    name: str | None = None,
    channel: str | None = None,
    webhook_url: str | None = None,
    email_to: str | None = None,
    siret: str | None = None,
    keywords: list[str] | None = None,
    cpv_codes: list[str] | None = None,
    regions: list[str] | None = None,
    departments: list[str] | None = None,
    descripteur_keywords: list[str] | None = None,
    budget_min: float | None = None,
    budget_max: float | None = None,
    match_cpv_family: bool | None = None,
    match_descripteur: bool | None = None,
    active: bool | None = None,
) -> dict[str, Any]:
    """Replace a profile's filters and webhook. Only non-None fields are sent;
    fields left as None keep their current value on the server.

    `descripteur_keywords` (with `match_descripteur=True`) matches MAPA notices
    that carry no CPV code. `active=False` pauses webhook deliveries without
    deleting the profile.
    """
    body = _drop_none({
        "name": name, "channel": channel, "webhook_url": webhook_url,
        "email_to": email_to, "siret": siret,
        "keywords": keywords, "cpv_codes": cpv_codes,
        "regions": regions, "departments": departments,
        "descripteur_keywords": descripteur_keywords,
        "budget_min": budget_min, "budget_max": budget_max,
        "match_cpv_family": match_cpv_family, "match_descripteur": match_descripteur,
        "active": active,
    })
    return await _request("PUT", f"/profiles/{profile_id}", json_body=body)


@mcp.tool()
async def delete_profile(profile_id: int) -> dict[str, Any]:
    """Delete a matching profile. Stops all future webhook deliveries for it."""
    return await _request("DELETE", f"/profiles/{profile_id}")


# ──────────────────────────────────────────────────────────────────────────────
# Billing (tier upgrade & subscription management)
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool()
async def upgrade_tier(
    tier: str,
    success_url: str | None = None,
    cancel_url: str | None = None,
) -> dict[str, Any]:
    """Start a Stripe Checkout session to upgrade the authenticated key to a
    higher tier ("starter" or "pro").

    IMPORTANT: this does NOT charge anything by itself. It returns a
    `checkout_url` that the agent MUST present to the human user. Payment
    requires the user's card on Stripe's hosted page. Once paid, the key is
    automatically upgraded.

    Use this when a tool call fails with 402/403 because the feature is gated
    (e.g. `search_awards` and `winner_intel` need Starter+ / Pro).

    Args:
        tier: "starter" or "pro".
        success_url: Where Stripe redirects after successful payment.
        cancel_url: Where Stripe redirects if the user cancels.

    Returns: {"checkout_url": "...", "session_id": "..."}
    """
    body = _drop_none({"tier": tier, "success_url": success_url, "cancel_url": cancel_url})
    return await _request("POST", "/billing/checkout", json_body=body)


@mcp.tool()
async def billing_portal(return_url: str | None = None) -> dict[str, Any]:
    """Return a Stripe Customer Portal URL for the authenticated key.

    The user can manage their subscription, update payment method, download
    invoices, or cancel. Present this URL to the human user; the agent
    cannot interact with the portal directly.
    """
    return await _request("POST", "/billing/portal", params=_drop_none({"return_url": return_url}))


def main() -> None:
    """CLI entry point that starts the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
