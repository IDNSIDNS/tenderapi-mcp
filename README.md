# TenderAPI MCP server

<!-- mcp-name: io.github.IDNSIDNS/tenderapi-mcp -->

Expose TenderAPI (French BOAMP + EU TED public procurement data) as MCP tools for AI agents (Claude Desktop, Cursor, Continue, Zed, etc.).

A thin wrapper over the public REST API at <https://tenderapi.fr>.

Coverage: BOAMP (France) since March 2015, and TED for FR/DE/IT/ES/UK since 2015 (legacy XML format until end 2023, then eForms), refreshed daily.

## Install

Requires Python 3.10+.

From PyPI (once published):

```bash
pip install tenderapi-mcp
```

From source:

```bash
git clone https://github.com/IDNSIDNS/tenderapi-mcp
cd tenderapi-mcp
pip install -e .
```

## Configure

Get a free API key at <https://tenderapi.fr/>.

Set the env var:

```bash
export TENDERAPI_KEY=ta_your_key_here
```

## Use with Claude Desktop

Edit your Claude Desktop config:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

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

Restart Claude Desktop. The `tenderapi` server should appear in the tool picker.

## Use with other MCP clients

Any MCP client supporting stdio transport. The binary `tenderapi-mcp` (installed by pip) is the entry point.

## Tools exposed

| Tool | Tier | Description |
|------|------|-------------|
| `search_tenders` | Free | Search BOAMP + TED tenders with typed filters (CPV, region, budget, deadline, source, etc.) |
| `get_tender` | Free | Fetch a single tender by id |
| `search_awards` | Starter | Search award notices (who won which contract, for how much) |
| `get_award` | Starter | Fetch a single award by id |
| `winner_intel` | Pro | Aggregated winner stats: top companies by CPV / region / year |
| `me` | any | Current key tier, quota remaining, available features |
| `list_profiles`, `get_profile`, `create_profile`, `update_profile`, `delete_profile` | Starter | Manage webhook alert profiles for new-tender matches |
| `upgrade_tier`, `billing_portal` | any | Stripe checkout and billing-management links |

PINs (prior-information notices) are excluded from `search_tenders` by default; pass `include_planning=true` to include them. A `deadline_after`/`deadline_before` filter drops notices with no submission deadline unless `include_null_deadline=true`.

## Tiers

- **Free**: 100 req/day, tenders only
- **Starter** (5 €/mo HT): 1 000 req/day, adds awards + webhooks
- **Pro** (15 €/mo HT): 3 000 req/day, adds winner intelligence

See <https://tenderapi.fr/#pricing>.

## Local development

Override the API base URL via `TENDERAPI_BASE_URL` (default `https://tenderapi.fr`).

## License

MIT, see [LICENSE](LICENSE).
