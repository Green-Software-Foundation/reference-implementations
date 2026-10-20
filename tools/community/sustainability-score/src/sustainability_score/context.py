"""RepoContext: a cheap, read-only view of a repository on disk."""
from __future__ import annotations

import os
from functools import lru_cache

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist",
             "build", ".mypy_cache", ".pytest_cache", "vendor", ".terraform"}


class RepoContext:
    def __init__(self, root: str):
        self.root = os.path.abspath(root)
        self._files: list[str] = []
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                full = os.path.join(dirpath, fn)
                self._files.append(os.path.relpath(full, self.root))

    @property
    def files(self) -> list[str]:
        return self._files

    def glob(self, *suffixes: str) -> list[str]:
        s = tuple(suffixes)
        return [f for f in self._files if f.endswith(s)]

    def basename_matches(self, *names: str) -> list[str]:
        want = {n.lower() for n in names}
        return [f for f in self._files if os.path.basename(f).lower() in want]

    def has(self, *names: str) -> bool:
        return bool(self.basename_matches(*names))

    @lru_cache(maxsize=512)
    def read(self, relpath: str) -> str:
        try:
            with open(os.path.join(self.root, relpath), "r",
                      encoding="utf-8", errors="ignore") as fh:
                return fh.read()
        except (OSError, UnicodeError):
            return ""

    def find_lines(self, relpath: str, needle: str) -> list[int]:
        return [i + 1 for i, line in enumerate(self.read(relpath).splitlines())
                if needle in line]
