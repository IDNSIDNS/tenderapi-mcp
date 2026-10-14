# TenderAPI MCP server

<!-- mcp-name: io.github.IDNSIDNS/tenderapi-mcp -->

Expose TenderAPI (French BOAMP + EU TED public procurement data) as MCP tools for AI agents (Claude Desktop, Cursor, Continue, Zed, etc.).

A thin wrapper over the public REST API at <https://tenderapi.fr>.

Coverage: BOAMP (France) since March 2015, and TED for FR/DE/IT/ES/UK since 2015 (legacy XML format until end 2023, then eForms), refreshed daily.

## Two ways to use it

### 1. Hosted server — no install, no key

The fastest way to try it. Point any MCP client at the hosted endpoint:

```
https://tenderapi.fr/mcp
```

Claude Desktop / Claude Code:

```json
{
  "mcpServers": {
    "tenderapi": {
      "type": "streamable-http",
      "url": "https://tenderapi.fr/mcp"
    }
  }
}
```

Exposes `search_tenders` and `get_tender`. **Anonymous, free, limited to 30 tool calls per day per IP.** No account, nothing to install.

Awards, winner intelligence and alert profiles are not available anonymously — they need a key, see below.

### 2. Local server (pip) — full toolset

Requires Python 3.10+ and a free API key.

```bash
pip install tenderapi-mcp
```

Get a free key at <https://tenderapi.fr/> (includes one weekly email watch), then:

```json
{
  "mcpServers": {
    "tenderapi": {
      "command": "tenderapi-mcp",
      "env": {
        "TENDERAPI_KEY": "ta_your_key_here"
      }
    }
  }
}
```

Claude Desktop config location:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

Restart the client. The `tenderapi` server should appear in the tool picker.

From source instead of PyPI:

```bash
git clone https://github.com/IDNSIDNS/tenderapi-mcp
cd tenderapi-mcp
pip install -e .
```

Any MCP client supporting stdio transport works. The `tenderapi-mcp` binary installed by pip is the entry point.

## Tools exposed

| Tool | Tier | Hosted (keyless) | Description |
|------|------|------------------|-------------|
| `search_tenders` | Free | ✅ | Search BOAMP + TED tenders with typed filters (CPV, region, budget, deadline, source, etc.) |
| `get_tender` | Free | ✅ | Fetch a single tender by id |
| `search_awards` | Pro | — | Search award notices (who won which contract, for how much) |
| `get_award` | Pro | — | Fetch a single award by id |
| `winner_intel` | Pro | — | Aggregated winner stats: top companies by CPV / region / year |
| `me` | any | — | Current key tier, quota remaining, available features |
| `list_profiles`, `get_profile`, `create_profile`, `update_profile`, `delete_profile` | Free (1, weekly email) / Pro | — | Manage alert profiles for new-tender matches: weekly email on a free key; daily email digest, Teams card or webhook on Pro |
| `upgrade_tier`, `billing_portal` | any | — | Stripe checkout and billing-management links |

PINs (prior-information notices) are excluded from `search_tenders` by default; pass `include_planning=true` to include them. A `deadline_after`/`deadline_before` filter drops notices with no submission deadline unless `include_null_deadline=true`.

## Tiers

- **Hosted, keyless**: 30 tool calls/day per IP, tenders only
- **Free key**: tenders, 1 alert profile (email digest every Monday, to the account address)
- **Pro** (15 €/month): adds awards and winner intelligence, up to 10 alert profiles delivered every morning (email digest, Teams or webhook)

Request limits only protect the service (free: 1 000/day and 30/min; Pro: 1 500/day and 120/min); paginated lists stop at row 1 000.

Prices are final — no VAT is charged (art. 293 B French tax code). See <https://tenderapi.fr/#pricing>.

## Local development

Override the API base URL via `TENDERAPI_BASE_URL` (default `https://tenderapi.fr`).

## Requirements

Pinned to the `mcp` 1.x line: version 2.0.0 removed `mcp.server.fastmcp`, which this
server is built on. Migration to the 2.x API is tracked separately.

## License

MIT, see [LICENSE](LICENSE).
