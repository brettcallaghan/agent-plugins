import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pin_releases  # noqa: E402

MARKETPLACE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".claude-plugin", "marketplace.json")


def market(ref="v0.3.0"):
    return {
        "name": "m",
        "plugins": [
            {"name": "follows", "source": {"source": "git-subdir", "url": "o/follows", "path": "plugin"}},
            {"name": "pinned", "source": {"source": "git-subdir", "url": "o/pinned", "path": "plugin", "ref": ref}},
        ],
    }


class FakeGitHub:
    def __init__(self, latest, manifest=None, fail=None):
        self.latest, self.manifest, self.fail = latest, manifest, fail
        self.asked = []

    def latest_tag(self, repo):
        self.asked.append(repo)
        if self.fail:
            raise RuntimeError(self.fail)
        return self.latest

    def manifest_version(self, repo, path, ref):
        return self.manifest if self.manifest is not None else ref[1:]


class PinTest(unittest.TestCase):
    def test_moves_a_pin_to_a_newer_release(self):
        m = market()
        moves, errors = pin_releases.pin(m, FakeGitHub("v0.4.0"))
        self.assertEqual(errors, [])
        self.assertEqual(moves, [("pinned", "v0.3.0", "v0.4.0")])
        self.assertEqual(m["plugins"][1]["source"]["ref"], "v0.4.0")

    def test_changes_nothing_else(self):
        m = market()
        want = copy.deepcopy(m)
        want["plugins"][1]["source"]["ref"] = "v0.4.0"
        pin_releases.pin(m, FakeGitHub("v0.4.0"))
        self.assertEqual(m, want)

    def test_leaves_entries_without_a_version_ref_alone(self):
        gh = FakeGitHub("v9.0.0")
        pin_releases.pin(market(), gh)
        self.assertEqual(gh.asked, ["o/pinned"])

    def test_never_moves_backwards_or_sideways(self):
        for latest in ("v0.3.0", "v0.2.9"):
            m = market()
            moves, errors = pin_releases.pin(m, FakeGitHub(latest))
            self.assertEqual((moves, errors), ([], []))
            self.assertEqual(m["plugins"][1]["source"]["ref"], "v0.3.0")

    def test_compares_versions_numerically(self):
        moves, _ = pin_releases.pin(market("v0.9.0"), FakeGitHub("v0.10.0"))
        self.assertEqual(moves, [("pinned", "v0.9.0", "v0.10.0")])

    def test_refuses_a_tag_whose_manifest_disagrees(self):
        m = market()
        moves, errors = pin_releases.pin(m, FakeGitHub("v0.4.0", manifest="0.3.0"))
        self.assertEqual(moves, [])
        self.assertIn("carries plugin version '0.3.0'", errors[0])
        self.assertEqual(m["plugins"][1]["source"]["ref"], "v0.3.0")

    def test_refuses_a_latest_release_that_is_not_a_version_tag(self):
        _, errors = pin_releases.pin(market(), FakeGitHub("nightly"))
        self.assertIn("not a vMAJOR.MINOR.PATCH tag", errors[0])

    def test_reports_an_unreadable_source(self):
        _, errors = pin_releases.pin(market(), FakeGitHub(None, fail="GET x: HTTP 404"))
        self.assertEqual(errors, ["pinned: GET x: HTTP 404"])


class RepositoryTest(unittest.TestCase):
    def test_forms(self):
        for url in ("o/r", "https://github.com/o/r", "https://github.com/o/r.git", "git@github.com:o/r.git"):
            self.assertEqual(pin_releases.repository(url), "o/r", url)

    def test_rejects_other_shapes(self):
        with self.assertRaises(ValueError):
            pin_releases.repository("https://example.com/a/b/c")


class MarketplaceTest(unittest.TestCase):
    def test_release_is_pinned_to_a_version_tag(self):
        with open(MARKETPLACE, encoding="utf-8") as f:
            m = json.load(f)
        refs = {p["name"]: p["source"].get("ref") for p in m["plugins"]}
        self.assertIsNotNone(pin_releases.version_key(refs["release"]))


class MainTest(unittest.TestCase):
    def test_writes_nothing_when_a_source_fails(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "marketplace.json")
            with open(path, "w") as f:
                json.dump(market(), f)
            before = open(path).read()
            env = dict(os.environ, GITHUB_API_URL="http://127.0.0.1:9", GH_TOKEN="")
            r = subprocess.run([sys.executable, pin_releases.__file__, path], env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 1, r.stderr)
            self.assertIn("nothing written", r.stderr)
            self.assertEqual(open(path).read(), before)


if __name__ == "__main__":
    unittest.main()
