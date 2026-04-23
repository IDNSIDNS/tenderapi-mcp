"""TenderAPI MCP server — exposes BOAMP + TED procurement data as MCP tools.

Thin wrapper over the public REST API at https://tenderapi.fr.

Config (env vars):
  TENDERAPI_KEY       — required, obtain at https://tenderapi.fr/
  TENDERAPI_BASE_URL  — optional, default https://tenderapi.fr
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

BASE_URL = os.getenv("TENDERAPI_BASE_URL", "https://tenderapi.fr").rstrip("/")
API_KEY = os.getenv("TENDERAPI_KEY", "")
TIMEOUT = float(os.getenv("TENDERAPI_TIMEOUT", "30"))

mcp = FastMCP("tenderapi")


def _headers() -> dict[str, str]:
    if not API_KEY:
        raise RuntimeError(
            "TENDERAPI_KEY env var is not set. Get a free key at https://tenderapi.fr/"
        )
    return {"X-API-Key": API_KEY, "User-Agent": "tenderapi-mcp/0.1"}


def _drop_none(params: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in params.items() if v is not None}


async def _get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(f"{BASE_URL}{path}", params=params or {}, headers=_headers())
    if r.status_code >= 400:
        raise RuntimeError(f"TenderAPI {r.status_code}: {r.text[:400]}")
    return r.json()


@mcp.tool()
async def search_tenders(
    cpv: str | None = None,
    region: str | None = None,
    budget_min: float | None = None,
    budget_max: float | None = None,
    deadline_after: str | None = None,
    source: str | None = None,
    status: str | None = None,
    buyer_siret: str | None = None,
    country: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """Search public procurement tenders from BOAMP (France) and TED (EU).

    Returns a paginated list of tender notices matching the filters.

    Args:
        cpv: CPV classification code (e.g. "72000000" for IT services).
        region: French region slug, lowercase (e.g. "occitanie", "ile-de-france", "bretagne").
        budget_min: Minimum estimated budget, EUR.
        budget_max: Maximum estimated budget, EUR.
        deadline_after: ISO date (YYYY-MM-DD); only tenders with submission deadline after this date.
        source: "boamp" (France) or "ted" (EU-wide). Omit to include both.
        status: "open" | "closed" | "awarded".
        buyer_siret: Exact SIRET of the French contracting authority (14 digits).
        country: ISO 3-letter country code (default FR).
        page: 1-indexed page number.
        page_size: Results per page, 1-100.

    Returns a dict with keys: total, page, page_size, results (list of tenders).
    """
    params = _drop_none({
        "cpv": cpv, "region": region,
        "budget_min": budget_min, "budget_max": budget_max,
        "deadline_after": deadline_after, "source": source, "status": status,
        "buyer_siret": buyer_siret, "country": country,
        "page": page, "page_size": page_size,
    })
    return await _get("/tenders", params)


@mcp.tool()
async def search_awards(
    cpv: str | None = None,
    region: str | None = None,
    winner_name: str | None = None,
    winner_siret: str | None = None,
    awarded_after: str | None = None,
    amount_min: float | None = None,
    source: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """Search award notices — who won which public contract, for how much.

    Requires Starter tier or above.

    Args:
        cpv: CPV code filter.
        region: Region slug.
        winner_name: Partial match on the winning company name.
        winner_siret: Exact SIRET match (14 digits).
        awarded_after: ISO date; awards with an award date after this.
        amount_min: Minimum contract amount, EUR.
        source: "boamp" or "ted".
        page / page_size: Pagination.
    """
    params = _drop_none({
        "cpv": cpv, "region": region,
        "winner_name": winner_name, "winner_siret": winner_siret,
        "awarded_after": awarded_after, "amount_min": amount_min,
        "source": source, "page": page, "page_size": page_size,
    })
    return await _get("/awards", params)


@mcp.tool()
async def winner_intel(
    cpv: str | None = None,
    region: str | None = None,
    year: int | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Aggregated winner statistics — top companies by contract count and total amount.

    Requires Pro tier. Use for competitive intelligence: "which companies win
    IT contracts in Occitanie in 2025?".

    Args:
        cpv: CPV code filter.
        region: Region slug.
        year: Integer year filter (e.g. 2025).
        limit: Top N results (default 10, max 50).
    """
    params = _drop_none({"cpv": cpv, "region": region, "year": year, "limit": limit})
    return await _get("/awards/winner-intel", params)


@mcp.tool()
async def me() -> dict[str, Any]:
    """Return the authenticated key's tier, quota remaining, and available features.

    Useful for the agent to check quota before launching many calls or to pick
    a tier-appropriate strategy.
    """
    return await _get("/me")


def main() -> None:
    """CLI entry point — starts the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
