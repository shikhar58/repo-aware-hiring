"""Shared helpers: where things live in single-repo mode and in a multi-repo workspace.

Single-repo mode (unchanged from earlier versions):
    <repo>/hiring/_repo/inventory.json, codebase-map.md, decisions.json
    <repo>/hiring/<role>/...

Workspace mode (a separate, private folder; nothing is written into the repos):
    <ws>/workspace.json             repos, tiers, roles
    <ws>/decisions.json             workspace-level decisions (setup, tiers, ownership)
    <ws>/repos/<name>/              clones of repos added by URL (local paths are referenced, not copied)
    <ws>/maps/<name>/               inventory.json + codebase-map.md (primary) or service-card.md (supporting)
    <ws>/system/                    system-graph.json, system-graph.md (generated), system-map.md (written)
    <ws>/roles/<role>/              focus.md, decisions.json and the same files as hiring/<role>/
Standard library only.
"""
import datetime as dt
import json
import re
from pathlib import Path

WS_FILE = "workspace.json"
TIERS = ("primary", "supporting", "ignored")
SLUG = re.compile(r"^[a-z0-9][a-z0-9._-]{0,62}$")


def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def slug(text):
    s = re.sub(r"[^a-z0-9._-]+", "-", text.lower()).strip("-.")
    return s[:63] or "repo"


def find_workspace(start):
    """Walk up from start looking for workspace.json. Returns the workspace folder or None."""
    p = Path(start).resolve()
    for d in [p] + list(p.parents):
        if (d / WS_FILE).is_file():
            return d
    return None


def load(ws):
    return json.loads((Path(ws) / WS_FILE).read_text(encoding="utf-8"))


def save(ws, data):
    path = Path(ws) / WS_FILE
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def repo_path(ws, repo):
    """Absolute path of a workspace repo's checkout."""
    if repo.get("kind") == "clone":
        return (Path(ws) / "repos" / repo["name"]).resolve()
    return Path(repo["path"]).expanduser().resolve()


def map_dir(ws, name):
    return Path(ws) / "maps" / name


def map_file(ws, repo):
    """Primary repos need a full map; supporting repos a service card."""
    d = map_dir(ws, repo["name"])
    return d / ("codebase-map.md" if repo.get("tier") == "primary" else "service-card.md")


def active_repos(data):
    return [r for r in data.get("repos", []) if r.get("tier") != "ignored"]


class Context:
    """Where a skill should read and write, whichever mode we are in."""

    def __init__(self, target, role=None):
        target = Path(target).resolve()
        self.ws = find_workspace(target)
        if self.ws:
            self.mode = "workspace"
            self.data = load(self.ws)
            self.base = self.ws
            self.role_dir = (self.ws / "roles" / role) if role else None
            self.shared_decisions = self.ws / "decisions.json"
        else:
            self.mode = "single"
            self.data = None
            repo = target
            # accept a path inside hiring/ too
            for d in [target] + list(target.parents):
                if d.name == "hiring":
                    repo = d.parent
                    break
            self.repo = repo
            self.base = repo / "hiring"
            self.role_dir = (self.base / role) if role else None
            self.shared_decisions = self.base / "_repo" / "decisions.json"

    def maps(self):
        """[(repo_name, repo_path, map_path, level)] for every repo whose map must exist."""
        if self.mode == "single":
            return [(self.repo.name, self.repo, self.base / "_repo" / "codebase-map.md", "full")]
        out = []
        for r in active_repos(self.data):
            out.append((r["name"], repo_path(self.ws, r), map_file(self.ws, r),
                        "full" if r.get("tier") == "primary" else "card"))
        return out

    def map_paths(self):
        return [m[2] for m in self.maps()]

    def repo_names(self):
        if self.mode == "single":
            return [self.repo.name]
        return [r["name"] for r in active_repos(self.data)]
