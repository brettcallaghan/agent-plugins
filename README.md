# agent-plugins

| Plugin | Source | Served at |
|---|---|---|
| `specs` | [brettcallaghan/specs](https://github.com/brettcallaghan/specs) | `release/v0`: its latest 0.x release |
| `release` | [brettcallaghan/release](https://github.com/brettcallaghan/release) | `release/v0`: its latest 0.x release |

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

An entry whose source `ref` is `release/vN` serves the plugin's latest
published N.x release. The plugin's repository fast-forwards that branch to
each release of the major when its publish workflow finishes, so installed copies get the plugin
exactly as that release published it, which for `release` means the skills
that match the CLI version the plugin provisions. Nothing here changes per
release, and Claude Code picks up the new version on its next marketplace
update because the plugin manifest's version changed. A new major does
not reach installs until its entry's `ref` here moves to `release/vN+1`,
a deliberate edit.

## Adding a plugin

Add an entry to `.claude-plugin/marketplace.json` whose source is the
plugin's repository and directory. Give it `"ref": "release/vN"` for the
current major when the repository's publish workflow moves `release/vN` to
each release; leave `ref` out to serve the default branch.
