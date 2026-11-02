# ImmPort skills for Claude

[Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) that teach Claude how to work with [ImmPort](https://www.immport.org), the NIAID immunology data repository. They build on the ImmPort MCP server, which gives Claude access to ImmPort data:
- claude.ai: the hosted connector `https://mcp.immport.org`
- command line: [`immport-mcp`](https://pypi.org/project/immport-mcp/)

| Skill | Use it to |
|---|---|
| [`immport-study-explorer`](plugins/immport/skills/immport-study-explorer/SKILL.md) | Find studies on a topic, compare several studies, see what data each has and its release history |
| [`immport-tab-analysis`](plugins/immport/skills/immport-tab-analysis/SKILL.md) | Load downloaded Tab.zip packages into SQLite and analyse them with joins from the ImmPort data model |

Skills for preparing and validating data submissions will be added here as ImmPort adds submission tools to the MCP server.

## Install

### claude.ai

1. Connect ImmPort: **Settings → Connectors → Add custom connector**, URL `https://mcp.immport.org`, then sign in with your ImmPort account.
2. Download the skill zips from the latest [release](../../releases) (or build them: `python3 scripts/build_skill_zips.py`).
3. Upload each zip in **Settings → Capabilities → Skills**. Organisation admins can provision them for everyone.

### Claude Code

```bash
export IMMPORT_API_KEY=<your key>     # from https://www.immport.org/auth/api/keys (valid 30 days)
claude plugin marketplace add ImmPortDB/immport-skills
claude plugin install immport@immport
```

The `immport` plugin installs both skills and starts the ImmPort MCP server (`uvx immport-mcp`, which needs [uv](https://docs.astral.sh/uv/)) with your `IMMPORT_API_KEY`.

## Try it

- *"Find influenza vaccine studies in older adults in ImmPort and compare their size and available assays."*
- *"Compare SDY180, SDY212 and SDY269 and tell me which has the richest HAI data."*
- *"I downloaded SDY180-DR58_Tab.zip. Load it and show mean HAI titers by arm, strain and day."*

## Layout

```
.claude-plugin/marketplace.json        Claude Code marketplace (lists the plugins)
plugins/immport/
  .claude-plugin/plugin.json           plugin manifest
  .mcp.json                            starts the immport-mcp server
  skills/<skill>/SKILL.md              one folder per skill, with scripts/ and references/ as needed
scripts/build_skill_zips.py            builds dist/<skill>.zip for claude.ai
```

Each skill is a folder with a `SKILL.md`. Its `description` tells Claude when to use the skill. To add a skill, create `plugins/immport/skills/<name>/SKILL.md` and check it with `claude plugin validate --strict plugins/immport`.

## Contributing and support

Issues and pull requests are welcome. For questions about ImmPort data, use the contact form at https://www.immport.org.
