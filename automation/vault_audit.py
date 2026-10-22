"""Audit local Obsidian navigation without opening credentials or calling services.

Links inside fenced code and inline code are examples, not graph edges. Personal
notes and hidden plugin data are excluded from content inspection. This checks
file targets, not factual accuracy, heading anchors, licenses, or approval validity.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
from urllib.parse import unquote


def visible_text(text: str) -> str:
    lines = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            lines.append("")
        else:
            lines.append("" if fence else re.sub(r"`+[^`]*`+", "", line))
    return "\n".join(lines)


def excluded(path: Path, vault: Path) -> bool:
    rel = path.relative_to(vault)
    return any(part.startswith(".") for part in rel.parts) or "1_LIFE" in rel.parts or path.name.upper() == "API_KEYS.MD"


def resolve_target(source: Path, target: str, vault: Path, files: set[Path], wiki: bool) -> tuple[str, list[Path]]:
    target = unquote(target.strip().strip("<>"))
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("//"):
        return "external", []
    target = target.split("#", 1)[0].split("?", 1)[0].replace("\\", "/")
    if not target:
        return "resolved", [source]
    if "[" in target or "]" in target or "{" in target:
        return "template", []
    def variants(path: Path) -> list[Path]:
        resolved = path.resolve()
        return [resolved, Path(str(resolved) + ".md")] if wiki and not path.suffix else [resolved]
    bases = [source.parent / target, vault / target]
    if wiki and not target.startswith(".") and "/" in target:
        bases.reverse()
    for base in bases:
        matches = [p for p in variants(base) if p in files or (not p.is_relative_to(vault) and p.is_file())]
        if matches:
            return "resolved", matches[:1]
    if wiki:
        suffix = target if Path(target).suffix else target + ".md"
        matches = sorted(p for p in files if p.relative_to(vault).as_posix().lower() == suffix.lower() or p.relative_to(vault).as_posix().lower().endswith("/" + suffix.lower()))
        if len(matches) == 1:
            return "resolved", matches
        if matches:
            return "ambiguous", matches
    return "missing", []


def audit(vault: Path, entry_note: str | None = None) -> dict:
    vault = vault.resolve()
    if not vault.is_dir():
        raise ValueError(f"Vault directory does not exist: {vault}")
    # Inventory filenames only for excluded material; never read its contents.
    files = {p.resolve() for p in vault.rglob("*") if p.is_file() and not any(x.startswith(".") for x in p.relative_to(vault).parts)}
    notes = sorted(p for p in files if p.suffix.lower() == ".md" and not excluded(p, vault))
    edges: set[tuple[str, str]] = set()
    issues = []
    external_count = template_count = 0
    for note in notes:
        text = visible_text(note.read_text(encoding="utf-8-sig"))
        source = note.relative_to(vault).as_posix()
        links = [(m.start(), m.group(1).split("|", 1)[0], True) for m in re.finditer(r"!?\[\[([^\]\n]+)\]\]", text)]
        links += [(m.start(), m.group(1) or m.group(2), False) for m in re.finditer(r"(?<!!)\[[^\]\n]+\]\((?:<([^>]+)>|([^\s)]+))(?:\s+\"[^\"]*\")?\)", text)]
        for offset, target, wiki in links:
            status, matches = resolve_target(note, target, vault, files, wiki)
            if status == "external":
                external_count += 1
            elif status == "template":
                template_count += 1
            elif status == "resolved":
                for match in matches:
                    if match in notes and match != note:
                        edges.add((source, match.relative_to(vault).as_posix()))
            else:
                issues.append({"source": source, "line": text[:offset].count("\n") + 1, "target": target, "status": status,
                               "candidates": [p.relative_to(vault).as_posix() for p in matches]})
    canvases = sorted(p for p in files if p.suffix.lower() == ".canvas" and not excluded(p, vault))
    for canvas in canvases:
        source = canvas.relative_to(vault).as_posix()
        try:
            data = json.loads(canvas.read_text(encoding="utf-8-sig"))
            nodes = data["nodes"]
            canvas_edges = data["edges"]
            ids = [n["id"] for n in nodes]
            if len(ids) != len(set(ids)):
                raise ValueError("duplicate node IDs")
            for node in nodes:
                if node.get("type") == "file":
                    target = (vault / node["file"]).resolve()
                    if not target.is_relative_to(vault) or target not in files:
                        issues.append({"source": source, "target": node["file"], "status": "missing_canvas_file"})
            for edge in canvas_edges:
                if edge["fromNode"] not in ids or edge["toNode"] not in ids:
                    issues.append({"source": source, "target": edge.get("id", ""), "status": "invalid_canvas_edge"})
        except (ValueError, KeyError, TypeError) as exc:
            issues.append({"source": source, "target": "", "status": "invalid_canvas", "reason": str(exc)})
    names = {p.relative_to(vault).as_posix() for p in notes}
    if entry_note is None and "00_START_HERE.md" in names:
        entry_note = "00_START_HERE.md"
    outgoing = defaultdict(set)
    adjacency = defaultdict(set)
    incoming = Counter()
    for source, target in edges:
        outgoing[source].add(target)
        adjacency[source].add(target)
        adjacency[target].add(source)
        incoming[target] += 1
    reachable = set()
    todo = [entry_note] if entry_note in names else []
    while todo:
        node = todo.pop()
        if node in reachable:
            continue
        reachable.add(node)
        todo.extend(outgoing[node] - reachable)
    pending = set(names)
    components = []
    while pending:
        todo = [min(pending)]
        component = set()
        while todo:
            node = todo.pop()
            if node in component:
                continue
            component.add(node)
            todo.extend(adjacency[node] - component)
        pending -= component
        components.append(sorted(component))
    stems = defaultdict(list)
    for note in notes:
        stems[note.stem.casefold()].append(note.relative_to(vault).as_posix())
    return {
        "schema_version": "cold_truth.vault_audit.v1", "scope": "local_file_navigation_only",
        "limitations": ["No external URL or factual verification", "No heading/block anchor validation", "Personal notes, API_KEYS.md and hidden plugin data not read", "Inline/fenced code examples excluded"],
        "note_count": len(notes), "edge_count": len(edges), "canvas_count": len(canvases), "external_link_count": external_count,
        "template_link_count": template_count, "issues": issues,
        "orphan_notes": sorted(n for n in names if not adjacency[n]),
        "entry_note": entry_note,
        "entry_note_exists": entry_note in names if entry_note is not None else None,
        "reachable_note_count": len(reachable) if entry_note is not None else None,
        "unreachable_from_entry": sorted(names - reachable) if entry_note is not None else [],
        "notes_without_incoming_links": sorted(n for n in names if not incoming[n]),
        "components": sorted(components, key=lambda c: (-len(c), c)),
        "duplicate_basenames": {k: v for k, v in sorted(stems.items()) if len(v) > 1},
        "folder_note_counts": dict(sorted(Counter(p.relative_to(vault).parts[0] for p in notes).items())),
        "edges": [list(edge) for edge in sorted(edges)],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", type=Path, default=Path(__file__).resolve().parents[1] / "Brody's Vault")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--entry-note", default="00_START_HERE.md", help="Vault-relative note used to check forward navigation")
    parser.add_argument("--strict", action="store_true", help="Exit 1 for invalid links/canvas, disconnected notes, a missing entry note or notes unreachable from it")
    args = parser.parse_args()
    result = audit(args.vault, entry_note=args.entry_note)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({k: result[k] for k in ("note_count", "edge_count", "canvas_count", "issues", "orphan_notes", "entry_note", "reachable_note_count", "unreachable_from_entry")}, indent=2))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.strict and (result["issues"] or len(result["components"]) > 1 or result["entry_note_exists"] is False or result["unreachable_from_entry"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
