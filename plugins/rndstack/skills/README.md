# Add workflows

This directory is a scaffold; it contains no executable skills yet.
Before testing the plugin, add at least one workflow at
`skills/<skill-name>/SKILL.md` with YAML frontmatter and instructions:

```markdown
---
name: hello
description: Greet the user when they ask to try the Rndstack plugin.
---

Greet the user briefly and confirm that the Rndstack starter skill is available.
```

Use a specific description explaining when to invoke each skill. Replace the
greeting example with the workflow you want the plugin to provide.

Portable plugins discover workflows from the `skills/` directory automatically.
