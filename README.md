# agent-plugins

Brett Callaghan's Claude Code plugin marketplace, named `brettcallaghan`.
It holds no plugin code: each entry points at the repository that develops
the plugin.

| Plugin | Source | Served at |
|---|---|---|
| `specs` | [brettcallaghan/specs](https://github.com/brettcallaghan/specs) `plugin/` | its default branch |
| `release` | [brettcallaghan/release](https://github.com/brettcallaghan/release) `plugin/` | its latest published release tag |

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

## Release pins

An entry whose source `ref` is a `vMAJOR.MINOR.PATCH` tag is release-pinned:
installed copies get the plugin exactly as that release published it, which
for `release` means the skills that match the CLI version the plugin
provisions. The source repository does not write here. The
[pin releases](.github/workflows/pin-releases.yml) workflow runs hourly,
reads each release-pinned source's latest published release, checks that
the plugin manifest at that tag carries the tag's version, and commits the
moved ref to `main`. Run it by hand from the Actions tab to pick up a
release at once.

While a source repository is private, the workflow needs the
`PLUGIN_SOURCES_TOKEN` secret: a fine-grained token with **Contents: read**
on each private source. Without it the run fails, naming the 404, and no
pin moves.

`scripts/pin_releases.py` is the whole of that logic; its tests run in
[checks](.github/workflows/checks.yml) with `claude plugin validate . --strict`.

## Adding a plugin

Add an entry to `.claude-plugin/marketplace.json` whose source is the
plugin's repository and directory. Give it a `ref` of its latest release tag
to have the workflow keep it pinned; leave `ref` out to serve the default
branch.
