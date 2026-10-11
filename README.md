# agent-plugins

Brett Callaghan's Claude Code plugin marketplace, named `brettcallaghan`.
It holds no plugin code: each entry points at the repository that develops
the plugin.

| Plugin | Source | Served at |
|---|---|---|
| `specs` | [brettcallaghan/specs](https://github.com/brettcallaghan/specs) `plugin/` | its default branch |
| `release` | [brettcallaghan/release](https://github.com/brettcallaghan/release) `plugin/` | its `stable` branch: the latest published release |

`release` depends on `specs`; installing it installs both.

## Install

In a Claude Code session:

```
/plugin marketplace add brettcallaghan/agent-plugins
/plugin install release@brettcallaghan
```

To enable a plugin for every session in a repository, add this to the
repository's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "brettcallaghan": {
      "source": { "source": "github", "repo": "brettcallaghan/agent-plugins" }
    }
  },
  "enabledPlugins": {
    "release@brettcallaghan": true
  }
}
```

Cloud sessions on claude.ai load the plugins synced to the account rather
than the repository's settings; add the plugin there once.

## Serving the latest release

An entry whose source `ref` is `stable` serves the plugin's latest published
release. The plugin's repository moves its `stable` branch to each release's
tag when its publish workflow finishes, so installed copies get the plugin
exactly as that release published it, which for `release` means the skills
that match the CLI version the plugin provisions. Nothing here changes per
release, and Claude Code picks up the new version on its next marketplace
update because the plugin manifest's version changed.

## Adding a plugin

Add an entry to `.claude-plugin/marketplace.json` whose source is the
plugin's repository and directory. Give it `"ref": "stable"` when the
repository's publish workflow moves a `stable` branch to each release;
leave `ref` out to serve the default branch.
