from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.models.schemas import PermissionLevel
from .base import Tool


def _resolve(path: str) -> Path:
    """Confine all file operations to the configured workspace root."""
    root = settings.workspace_path
    target = (root / path).resolve()

    if root not in target.parents and target != root:
        raise PermissionError(
            f"Path '{path}' escapes the JARVIS workspace sandbox."
        )

    return target


class ListFiles(Tool):
    name = "list_files"
    description = (
        "List files and directories inside the workspace. "
        "Use this to inspect project structure before reading files."
    )
    permission_level = PermissionLevel.READ
    parameters = {
        "path": "string, optional, relative to workspace root, default '.'",
        "recursive": "boolean, optional, default false",
    }

    async def run(
        self,
        path: str = ".",
        recursive: bool = False,
        **_: object,
    ) -> str:
        target = _resolve(path)

        if not target.exists():
            raise FileNotFoundError(f"{path} does not exist")

        if not target.is_dir():
            raise NotADirectoryError(f"{path} is not a directory")

        if recursive:
            entries = sorted(
                target.rglob("*"),
                key=lambda p: str(p.relative_to(target)),
            )
        else:
            entries = sorted(
                target.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )

        if not entries:
            return "Directory is empty."

        lines: list[str] = []

        for entry in entries:
            relative = entry.relative_to(settings.workspace_path)

            if entry.is_dir():
                lines.append(f"[DIR]  {relative}/")
            else:
                lines.append(f"[FILE] {relative}")

        return "\n".join(lines[:1000])


class ReadFile(Tool):
    name = "read_file"
    description = (
        "Read the full contents of a text file inside the workspace."
    )
    permission_level = PermissionLevel.READ
    parameters = {
        "path": "string, relative to workspace root"
    }

    async def run(self, path: str, **_: object) -> str:
        target = _resolve(path)

        if not target.exists():
            raise FileNotFoundError(f"{path} does not exist")

        if not target.is_file():
            raise IsADirectoryError(f"{path} is not a file")

        return target.read_text(errors="replace")


class WriteFile(Tool):
    name = "write_file"
    description = (
        "Create or overwrite a file inside the workspace with given content."
    )
    permission_level = PermissionLevel.SENSITIVE
    parameters = {
        "path": "string",
        "content": "string",
    }

    async def run(
        self,
        path: str,
        content: str,
        **_: object,
    ) -> str:
        target = _resolve(path)

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

        return f"Wrote {len(content)} bytes to {path}"


class EditFile(Tool):
    name = "edit_file"
    description = (
        "Replace an exact substring in a file with new text "
        "(find/replace)."
    )
    permission_level = PermissionLevel.SENSITIVE
    parameters = {
        "path": "string",
        "find": "string",
        "replace": "string",
    }

    async def run(
        self,
        path: str,
        find: str,
        replace: str,
        **_: object,
    ) -> str:
        target = _resolve(path)

        if not target.exists():
            raise FileNotFoundError(f"{path} does not exist")

        text = target.read_text()

        if find not in text:
            raise ValueError(
                "`find` text not found in file — no changes made."
            )

        count = text.count(find)

        target.write_text(text.replace(find, replace))

        return f"Replaced {count} occurrence(s) in {path}"


class SearchFiles(Tool):
    name = "search_files"
    description = (
        "Search for a substring across files in the workspace "
        "(simple grep)."
    )
    permission_level = PermissionLevel.READ
    parameters = {
        "query": "string",
        "glob": "string, optional, default '**/*'",
    }

    async def run(
        self,
        query: str,
        glob: str = "**/*",
        **_: object,
    ) -> str:
        root = settings.workspace_path
        matches: list[str] = []

        for file in root.glob(glob):
            if not file.is_file():
                continue

            try:
                text = file.read_text(errors="ignore")
            except Exception:
                continue

            for line_number, line in enumerate(
                text.splitlines(),
                start=1,
            ):
                if query in line:
                    matches.append(
                        f"{file.relative_to(root)}:"
                        f"{line_number}: "
                        f"{line.strip()}"
                    )

        if not matches:
            return "No matches found."

        return "\n".join(matches[:200])