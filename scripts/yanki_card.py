#!/usr/bin/env python3
"""Discover Yanki folders and safely create one-card-per-file Markdown notes."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any


class YankiError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise YankiError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise YankiError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise YankiError(f"Expected a JSON object in {path}")
    return value


def has_yanki(vault: Path) -> bool:
    base = vault / ".obsidian" / "plugins" / "yanki"
    return (base / "manifest.json").is_file() and (base / "data.json").is_file()


def resolve_vault(value: str | None) -> Path:
    if value:
        vault = Path(value).expanduser().resolve()
        if not (vault / ".obsidian").is_dir():
            raise YankiError(f"Not an Obsidian vault: {vault}")
        if not has_yanki(vault):
            raise YankiError(f"Yanki is not installed or configured in: {vault}")
        return vault

    current = Path.cwd().resolve()
    if (current / ".obsidian").is_dir():
        if not has_yanki(current):
            raise YankiError(f"Current Obsidian vault is not Yanki-enabled: {current}")
        return current
    raise YankiError(
        "The current working directory is not an Obsidian vault root. Open the agent at the "
        "Yanki-enabled vault root or pass an explicit --vault path."
    )


def load_yanki(vault: Path) -> tuple[dict[str, Any], dict[str, Any], list[Path]]:
    base = vault / ".obsidian" / "plugins" / "yanki"
    manifest = read_json(base / "manifest.json")
    settings = read_json(base / "data.json")
    if manifest.get("id") != "yanki":
        raise YankiError(f"Unexpected plugin manifest at {base}")
    raw_folders = settings.get("folders", [])
    if not isinstance(raw_folders, list):
        raise YankiError("Yanki setting 'folders' must be a list")
    folders: list[Path] = []
    for raw in raw_folders:
        if not isinstance(raw, str) or not raw.strip():
            continue
        folder = vault if raw.strip() == "/" else safe_vault_path(vault, raw)
        if folder not in folders:
            folders.append(folder)
    if not folders:
        raise YankiError("Yanki has no watched flashcard folders configured")
    return manifest, settings, folders


def safe_vault_path(vault: Path, value: str | Path) -> Path:
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = vault / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(vault)
    except ValueError as exc:
        raise YankiError(f"Path is outside the vault: {candidate}") from exc
    return candidate


def rel(vault: Path, path: Path) -> str:
    relative = path.relative_to(vault).as_posix()
    return "/" if relative == "." else relative


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def deck_directories(watched: list[Path]) -> list[Path]:
    result: list[Path] = []
    for root in watched:
        if not root.is_dir():
            continue
        result.append(root)
        result.extend(
            sorted(
                (
                    path
                    for path in root.rglob("*")
                    if path.is_dir() and ".obsidian" not in path.relative_to(root).parts
                ),
                key=str,
            )
        )
    return list(dict.fromkeys(result))


def inspect_payload(vault: Path) -> dict[str, Any]:
    manifest, settings, watched = load_yanki(vault)
    raw_sync = settings.get("sync", {})
    sync = raw_sync if isinstance(raw_sync, dict) else {}
    raw_filenames = settings.get("manageFilenames", {})
    filenames = raw_filenames if isinstance(raw_filenames, dict) else {}

    auto_sync_enabled = sync.get("autoSyncEnabled")
    if not isinstance(auto_sync_enabled, bool):
        auto_sync_enabled = None
    push_to_anki_web = sync.get("pushToAnkiWeb")
    if not isinstance(push_to_anki_web, bool):
        push_to_anki_web = None
    media_mode = sync.get("mediaMode")
    if media_mode not in {"all", "local", "off", "remote"}:
        media_mode = None
    auto_rename_trigger = filenames.get("autoRenameTrigger")
    if auto_rename_trigger not in {"before-sync", "file-changed", "off"}:
        auto_rename_trigger = None
    filename_mode = filenames.get("mode")
    if filename_mode not in {"prompt", "response"}:
        filename_mode = None
    max_length = filenames.get("maxLength")
    if not isinstance(max_length, int) or isinstance(max_length, bool) or max_length <= 0:
        max_length = None

    folders = []
    for folder in deck_directories(watched):
        folders.append(
            {
                "path": rel(vault, folder),
                "direct_card_count": len(list(folder.glob("*.md"))),
            }
        )
    missing = [rel(vault, folder) for folder in watched if not folder.is_dir()]
    return {
        "vault": str(vault),
        "vault_name": vault.name,
        "yanki_version": manifest.get("version"),
        "watched_folders": [rel(vault, folder) for folder in watched],
        "ignore_folder_notes": bool(settings.get("ignoreFolderNotes", True)),
        "sync": {
            "auto_sync_enabled": auto_sync_enabled,
            "media_mode": media_mode,
            "push_to_anki_web": push_to_anki_web,
        },
        "filename_management": {
            "auto_rename_trigger": auto_rename_trigger,
            "max_length": max_length,
            "mode": filename_mode,
        },
        "deck_folders": folders,
        "missing_watched_folders": missing,
    }


def resolve_folder(
    vault: Path,
    watched: list[Path],
    value: str | None,
    create: bool,
    dry_run: bool = False,
) -> Path:
    existing = deck_directories(watched)
    if not value:
        if len(existing) == 1:
            return existing[0]
        choices = "\n".join(f"  - {rel(vault, path)}" for path in existing)
        raise YankiError(f"Choose a target folder with --folder. Available folders:\n{choices}")

    raw = Path(value).expanduser()
    if value.strip() == "/":
        exact = vault
    elif not raw.is_absolute():
        exact = safe_vault_path(vault, raw)
        if not exact.exists() and len(raw.parts) == 1:
            matches = [
                path
                for path in existing
                if path.name.casefold() == value.casefold()
                or rel(vault, path).casefold() == value.casefold()
            ]
            if len(matches) == 1:
                exact = matches[0]
            elif len(matches) > 1:
                choices = "\n".join(f"  - {rel(vault, path)}" for path in matches)
                raise YankiError(f"Folder name is ambiguous; use a vault-relative path:\n{choices}")
    else:
        exact = safe_vault_path(vault, raw)

    if not any(is_within(exact, root) for root in watched):
        choices = ", ".join(rel(vault, root) for root in watched)
        raise YankiError(f"Target is outside Yanki watched folders ({choices}): {exact}")
    if exact.exists() and not exact.is_dir():
        raise YankiError(f"Target is not a directory: {exact}")
    if not exact.exists():
        if not create:
            raise YankiError(f"Target folder does not exist: {exact}; pass --create-folder to create it")
        if not dry_run:
            exact.mkdir(parents=True, exist_ok=False)
    return exact


def strip_frontmatter(text: str) -> str:
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        return normalized.strip()
    end = normalized.find("\n---\n", 4)
    if end < 0:
        return normalized.strip()
    return normalized[end + 5 :].strip()


def yaml_tags(tags: list[str]) -> str:
    cleaned = [tag.strip() for tag in tags if isinstance(tag, str) and tag.strip()]
    if not cleaned:
        return ""
    lines = ["---", "tags:"]
    lines.extend(f"  - {json.dumps(tag, ensure_ascii=False)}" for tag in cleaned)
    lines.extend(["---", ""])
    return "\n".join(lines) + "\n"


def render_card(spec: dict[str, Any]) -> str:
    card_type = str(spec.get("type", "basic")).strip().lower()
    front = str(spec.get("front", "")).strip()
    back = str(spec.get("back", "")).strip()
    extra = str(spec.get("extra", "")).strip()
    raw_tags = spec.get("tags", [])
    tags = [raw_tags] if isinstance(raw_tags, str) else raw_tags
    if not isinstance(tags, list):
        raise YankiError("'tags' must be a string or list of strings")
    if not front:
        raise YankiError("Card 'front' must not be empty")

    if card_type == "basic":
        body = front
        if back:
            body += f"\n\n---\n\n{back}"
    elif card_type == "reversed":
        if not back:
            raise YankiError("A reversed card requires 'back'")
        body = f"{front}\n\n---\n\n---\n\n{back}"
        if extra:
            body += f"\n\n---\n\n{extra}"
    elif card_type == "type-answer":
        if not back:
            raise YankiError("A type-answer card requires 'back'")
        if "\n" in back:
            raise YankiError("A type-answer response must be a single line")
        body = f"{front}\n\n_{back}_"
    elif card_type == "cloze":
        clozes = re.findall(r"~~(.*?)~~", front, flags=re.DOTALL)
        if not clozes:
            raise YankiError("A cloze card requires at least one ~~cloze deletion~~ in 'front'")
        if any("\n" in cloze or "\r" in cloze for cloze in clozes):
            raise YankiError("Yanki cloze deletions cannot span multiple lines or block elements")
        body = front
        cloze_back = back or extra
        if cloze_back:
            body += f"\n\n---\n\n{cloze_back}"
    else:
        raise YankiError("Card 'type' must be basic, reversed, type-answer, or cloze")
    return yaml_tags(tags) + body.strip() + "\n"


def plain_title(text: str) -> str:
    first = next((line.strip() for line in text.splitlines() if line.strip()), "Untitled card")
    first = re.sub(r"^#{1,6}\s+", "", first)
    first = re.sub(r"!\[\[[^]]+]]", "", first)
    first = re.sub(r"\[\[([^]|]+)(?:\|[^]]+)?]]", r"\1", first)
    first = re.sub(r"!?\[([^]]*)]\([^)]*\)", r"\1", first)
    first = re.sub(r"[`*_~]", "", first)
    return first


def safe_filename(title: str, max_length: int, folder: Path, ignore_folder_notes: bool) -> str:
    name = unicodedata.normalize("NFC", title)
    name = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", " ", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    if not name:
        name = "Untitled card"
    name = name[: max(1, max_length)].rstrip(" .")
    if name.upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}:
        name += " card"
    if ignore_folder_notes and name.casefold() == folder.name.casefold():
        name = (name + " card")[:max_length].rstrip(" .")
    return name or "Untitled card"


def unique_path(folder: Path, stem: str) -> Path:
    candidate = folder / f"{stem}.md"
    number = 2
    while candidate.exists():
        suffix = f" ({number})"
        trimmed = stem[: max(1, 240 - len(suffix))].rstrip()
        candidate = folder / f"{trimmed}{suffix}.md"
        number += 1
    return candidate


def load_spec(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    if path == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(path).read_text(encoding="utf-8")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise YankiError(f"Invalid card spec JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise YankiError("Card spec must be one JSON object")
    return value


def merged_spec(args: argparse.Namespace) -> dict[str, Any]:
    spec = load_spec(args.spec)
    for key in ("folder", "title", "type", "front", "back", "extra"):
        value = getattr(args, key, None)
        if value is not None:
            spec[key] = value
    if args.tag:
        existing = spec.get("tags", [])
        if isinstance(existing, str):
            existing = [existing]
        if not isinstance(existing, list):
            raise YankiError("'tags' must be a string or list of strings")
        spec["tags"] = [*existing, *args.tag]
    return spec


def infer_type(body: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    clozes = re.findall(r"~~(.*?)~~", body, flags=re.DOTALL)
    if any("\n" in cloze or "\r" in cloze for cloze in clozes):
        warnings.append("Yanki cloze deletions cannot span multiple lines or block elements")
    if any("\n" not in cloze and "\r" not in cloze for cloze in clozes):
        return "cloze", warnings
    separators = list(re.finditer(r"(?m)^---\s*$", body))
    if len(separators) >= 2:
        between = body[separators[0].end() : separators[1].start()]
        if not between.strip():
            return "reversed", warnings
    if separators:
        return "basic", warnings
    last = next((line.strip() for line in reversed(body.splitlines()) if line.strip()), "")
    if re.fullmatch(r"(?:_[^_\n]+_|\*[^*\n]+\*)", last):
        return "type-answer", warnings
    warnings.append("No structural cue found; Yanki will create a front-only Basic note")
    return "basic-front-only", warnings


def command_inspect(args: argparse.Namespace) -> None:
    vault = resolve_vault(args.vault)
    print(json.dumps(inspect_payload(vault), ensure_ascii=False, indent=2))


def command_add(args: argparse.Namespace) -> None:
    vault = resolve_vault(args.vault)
    _, settings, watched = load_yanki(vault)
    spec = merged_spec(args)
    folder = resolve_folder(vault, watched, spec.get("folder"), args.create_folder, args.dry_run)
    content = render_card(spec)
    canonical = strip_frontmatter(content)
    if not args.allow_duplicate:
        for existing in folder.glob("*.md"):
            try:
                if strip_frontmatter(existing.read_text(encoding="utf-8")) == canonical:
                    raise YankiError(f"Duplicate card body already exists: {existing}")
            except UnicodeDecodeError:
                continue
    raw_filename_settings = settings.get("manageFilenames", {})
    filename_settings = raw_filename_settings if isinstance(raw_filename_settings, dict) else {}
    configured_max = filename_settings.get("maxLength", 60)
    max_length = (
        configured_max
        if isinstance(configured_max, int) and not isinstance(configured_max, bool) and configured_max > 0
        else 60
    )
    title = str(spec.get("title") or plain_title(str(spec.get("front", ""))))
    stem = safe_filename(title, max_length, folder, bool(settings.get("ignoreFolderNotes", True)))
    destination = unique_path(folder, stem)
    inferred, warnings = infer_type(strip_frontmatter(content))
    result = {
        "created": not args.dry_run,
        "path": str(destination),
        "vault_relative_path": rel(vault, destination),
        "card_type": inferred,
        "warnings": warnings,
    }
    if not args.dry_run:
        with destination.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def command_validate(args: argparse.Namespace) -> None:
    vault = resolve_vault(args.vault)
    _, _, watched = load_yanki(vault)
    card = safe_vault_path(vault, args.file)
    if not card.is_file():
        raise YankiError(f"Card file does not exist: {card}")
    if card.suffix.lower() != ".md":
        raise YankiError(f"Card is not a Markdown file: {card}")
    if not any(is_within(card, root) for root in watched):
        raise YankiError(f"Card is outside Yanki watched folders: {card}")
    body = strip_frontmatter(card.read_text(encoding="utf-8"))
    inferred, warnings = infer_type(body)
    print(
        json.dumps(
            {
                "valid": True,
                "path": str(card),
                "vault_relative_path": rel(vault, card),
                "card_type": inferred,
                "warnings": warnings,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Discover a vault and list Yanki deck folders")
    inspect_parser.add_argument("--vault", help="Explicit Obsidian vault path; defaults to the current vault")
    inspect_parser.set_defaults(func=command_inspect)

    add_parser = subparsers.add_parser("add", help="Create one Yanki card Markdown file")
    add_parser.add_argument("--vault", help="Explicit Obsidian vault path; defaults to the current vault")
    add_parser.add_argument("--spec", help="JSON card spec path, or - for stdin")
    add_parser.add_argument("--folder", help="Existing folder inside a Yanki watched folder")
    add_parser.add_argument("--title", help="Filename stem; defaults to text derived from the front")
    add_parser.add_argument("--type", choices=("basic", "reversed", "type-answer", "cloze"))
    add_parser.add_argument("--front", help="Front or cloze content")
    add_parser.add_argument("--back", help="Back or type-in answer")
    add_parser.add_argument("--extra", help="Optional extra content")
    add_parser.add_argument("--tag", action="append", default=[], help="Anki/Obsidian tag; repeatable")
    add_parser.add_argument("--create-folder", action="store_true", help="Create a new target deck folder")
    add_parser.add_argument("--allow-duplicate", action="store_true", help="Allow an identical body in the target folder")
    add_parser.add_argument("--dry-run", action="store_true", help="Plan and validate without writing")
    add_parser.set_defaults(func=command_add)

    validate_parser = subparsers.add_parser("validate", help="Validate a card file and infer its Yanki type")
    validate_parser.add_argument("--vault", help="Explicit Obsidian vault path; defaults to the current vault")
    validate_parser.add_argument("--file", required=True, help="Absolute or vault-relative Markdown path")
    validate_parser.set_defaults(func=command_validate)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
        return 0
    except (YankiError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
