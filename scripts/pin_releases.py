#!/usr/bin/env python3
"""Pin each release-pinned plugin to its source's latest published release.

An entry is release-pinned when its source carries a `ref` of the form
vMAJOR.MINOR.PATCH. For each one, the script reads the source repository's
latest published release (GitHub's releases/latest, which is never a draft
or a prerelease), checks that the plugin manifest at that tag carries the
tag's version, and moves the ref forward when the release is newer. A ref
never moves backwards. Entries without such a ref follow their source's
default branch and are left alone.

Every entry is checked before anything is written: if one source cannot be
read, or its manifest disagrees with its tag, nothing is written.

Usage: pin_releases.py [MARKETPLACE]   (default .claude-plugin/marketplace.json)

Environment:
  GH_TOKEN        a token that can read every pinned source repository. The
                  workflow's own token reads public repositories only.
  GITHUB_API_URL  the REST API root (default https://api.github.com)

Prints one line per moved pin, "<plugin> <old> -> <new>".
Exit 0: written, or nothing to move. Exit 1: nothing written; the cause is
on stderr.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request

TAG = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def version_key(tag):
    m = TAG.match(tag or "")
    return tuple(int(g) for g in m.groups()) if m else None


def repository(url):
    """owner/repo from a git-subdir or github source's url."""
    for prefix in ("https://github.com/", "git@github.com:"):
        if url.startswith(prefix):
            url = url[len(prefix):]
    url = url.rstrip("/")
    if url.endswith(".git"):
        url = url[: -len(".git")]
    if url.count("/") != 1:
        raise ValueError(f"cannot read owner/repo from source url {url!r}")
    return url


class GitHub:
    def __init__(self, token=None, api=None):
        self.token = token
        self.api = (api or "https://api.github.com").rstrip("/")

    def _get(self, path, accept):
        req = urllib.request.Request(self.api + path, headers={"Accept": accept})
        if self.token:
            req.add_header("Authorization", "Bearer " + self.token)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            hint = ""
            if e.code == 404:
                hint = " (a private repository reads as 404 without a token that can read it: set PLUGIN_SOURCES_TOKEN)"
            raise RuntimeError(f"GET {path}: HTTP {e.code}{hint}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"GET {path}: {e.reason}") from None

    def latest_tag(self, repo):
        data = json.loads(self._get(f"/repos/{repo}/releases/latest", "application/vnd.github+json"))
        return data["tag_name"]

    def manifest_version(self, repo, path, ref):
        manifest = f"{path.strip('/')}/.claude-plugin/plugin.json" if path.strip("/") else ".claude-plugin/plugin.json"
        raw = self._get(f"/repos/{repo}/contents/{manifest}?ref={ref}", "application/vnd.github.raw+json")
        return json.loads(raw).get("version")


def pin(market, github):
    """Move each release-pinned entry of market in place.

    Returns (moves, errors): moves is a list of (plugin, old, new); errors a
    list of messages. Callers write market only when errors is empty.
    """
    moves, errors = [], []
    for entry in market.get("plugins", []):
        source = entry.get("source")
        if not isinstance(source, dict) or version_key(source.get("ref")) is None:
            continue
        name, current = entry.get("name"), source["ref"]
        try:
            repo = repository(source.get("url") or source.get("repo") or "")
            latest = github.latest_tag(repo)
            if version_key(latest) is None:
                errors.append(f"{name}: {repo}'s latest release {latest!r} is not a vMAJOR.MINOR.PATCH tag")
                continue
            if version_key(latest) <= version_key(current):
                continue
            have = github.manifest_version(repo, source.get("path", ""), latest)
            if have != latest[1:]:
                errors.append(f"{name}: {repo} at {latest} carries plugin version {have!r}, not {latest[1:]!r}")
                continue
        except (RuntimeError, ValueError, KeyError) as e:
            errors.append(f"{name}: {e}")
            continue
        source["ref"] = latest
        moves.append((name, current, latest))
    return moves, errors


def main(argv):
    path = argv[1] if len(argv) > 1 else ".claude-plugin/marketplace.json"
    with open(path, encoding="utf-8") as f:
        market = json.load(f)
    github = GitHub(os.environ.get("GH_TOKEN"), os.environ.get("GITHUB_API_URL"))
    moves, errors = pin(market, github)
    if errors:
        for e in errors:
            print(f"pin_releases: {e}", file=sys.stderr)
        print("pin_releases: nothing written", file=sys.stderr)
        return 1
    if moves:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(json.dumps(market, indent=2, ensure_ascii=False) + "\n")
        os.replace(tmp, path)
    for name, old, new in moves:
        print(f"{name} {old} -> {new}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
