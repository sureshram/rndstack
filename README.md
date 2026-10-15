# Rndstack plugins

Local plugin scaffolds and a repo marketplace for ChatGPT and Codex.

```text
.agents/plugins/marketplace.json       Repo marketplace catalog
plugins/rndstack/plugin.json          Portable plugin manifest
plugins/rndstack/skills/README.md      Instructions for adding workflows
```

The starter package is named `rndstack`, version `0.1.0`. It uses the portable
Agent Plugins manifest with OpenAI display metadata. Add skills or an MCP
server before testing it; the scaffold currently provides no tools or workflows.

## Develop and test

1. Add a workflow at `plugins/rndstack/skills/<skill-name>/SKILL.md` using the
   example in [the skills guide](plugins/rndstack/skills/README.md).
2. Update the manifest description and display metadata to describe that workflow.
3. Restart the ChatGPT desktop app, open the Plugins Directory, select
   **Rndstack Local Plugins**, and install **Rndstack**.
4. Start a new chat and test the workflow.

If you manage marketplace sources through the Codex CLI, run this from the
repository root:

```sh
codex plugin marketplace add .
codex plugin marketplace list
```

The catalog makes the package discoverable; it does not install, enable, or
publish it by itself. After editing a locally installed plugin, refresh its
installed copy and restart the desktop app before testing again.

## Add another plugin

Copy `plugins/rndstack/` to `plugins/<new-name>/`, then update its manifest
`name`, description, and display metadata. Use a unique lowercase kebab-case
name. Add a corresponding object to the marketplace's `plugins` array:

```json
{
  "name": "new-plugin",
  "source": {
    "source": "local",
    "path": "./plugins/new-plugin"
  },
  "policy": {
    "installation": "AVAILABLE",
    "authentication": "ON_INSTALL"
  },
  "category": "Productivity"
}
```

Marketplace source paths resolve from the repository root. Plugin resource
paths resolve from the plugin root. Keep paths inside their respective roots.

Add an optional root `mcp.json` when you have an MCP server to bundle; use the
Agent Plugins MCP schema and declare the server transport type. Add registered
app mappings, hooks, or assets only when the plugin needs them.

See the [official packaging documentation](https://developers.openai.com/plugins/build/plugins)
for manifest formats, marketplace setup, and optional components.
