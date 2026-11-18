#!/usr/bin/env python3
"""
PrepDrop — AI-powered prep resource organizer
Run: streamlit run app.py
"""

import os
import anthropic
import streamlit as st
from pathlib import Path
from docx import Document
from docx.shared import Pt

# ── Config ─────────────────────────────────────────────────────────────────────
DEFAULT_ROOT = str(Path(os.environ.get("NOTES_ROOT", "~/prep-notes")).expanduser())
MODEL        = os.environ.get("ORGANIZER_MODEL", "claude-opus-4-5")
MAX_ITER     = 20
# ───────────────────────────────────────────────────────────────────────────────

def get_client():
    key = os.environ.get("ANTHROPIC_API_KEY") or st.session_state.get("api_key", "")
    if not key:
        return None
    return anthropic.Anthropic(api_key=key)


# ── Filesystem helpers ──────────────────────────────────────────────────────────

def folder_tree(root: Path, max_depth: int = 3) -> str:
    lines = [f"{root.name}/  ← root"]
    def _walk(path: Path, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            items = sorted(path.iterdir())
        except PermissionError:
            return
        for item in items:
            if item.name.startswith("."):
                continue
            pad = "  " * depth
            if item.is_dir():
                lines.append(f"{pad}{item.name}/")
                _walk(item, depth + 1)
            else:
                lines.append(f"{pad}{item.name}")
    _walk(root, 1)
    return "\n".join(lines)


def _safe(root: Path, rel: str) -> Path:
    full = (root / rel).resolve()
    if not str(full).startswith(str(root.resolve())):
        raise ValueError(f"Path '{rel}' escapes notes root")
    return full


def tool_list_directory(root: Path, path: str) -> str:
    full = _safe(root, path)
    if not full.exists():
        return f"Error: '{path}' does not exist"
    items = [i for i in sorted(full.iterdir()) if not i.name.startswith(".")]
    return "\n".join(
        f"[DIR]  {i.name}/" if i.is_dir() else f"[FILE] {i.name}"
        for i in items
    ) or "(empty)"


def tool_read_file(root: Path, path: str) -> str:
    full = _safe(root, path)
    return full.read_text() if full.exists() else f"Error: '{path}' does not exist"


def tool_write_file(root: Path, path: str, content: str) -> str:
    full = _safe(root, path)
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)
    return f"Written: {path}"


def tool_append_to_file(root: Path, path: str, content: str) -> str:
    full = _safe(root, path)
    if not full.exists():
        return f"Error: '{path}' does not exist. Use write_file first."
    with open(full, "a") as f:
        f.write("\n" + content)
    return f"Appended to: {path}"


def tool_create_directory(root: Path, path: str) -> str:
    _safe(root, path).mkdir(parents=True, exist_ok=True)
    return f"Created: {path}"


def tool_read_docx(root: Path, path: str) -> str:
    full = _safe(root, path)
    if not full.exists():
        return f"Error: '{path}' does not exist"
    doc = Document(str(full))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs) or "(empty document)"


def tool_append_to_docx(root: Path, path: str, content: str) -> str:
    full = _safe(root, path)
    if not full.exists():
        return f"Error: '{path}' does not exist"
    doc = Document(str(full))
    # Add a visual separator
    doc.add_paragraph("─" * 40)
    # Add each line as a paragraph
    for line in content.strip().split("\n"):
        doc.add_paragraph(line)
    doc.save(str(full))
    return f"Appended to: {path}"


TOOL_SCHEMAS = [
    {
        "name": "list_directory",
        "description": "List files and subdirectories at a path (relative to notes root).",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "e.g. '.' or 'Meta/' or 'topics/RL/'"}},
            "required": ["path"],
        },
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Create or overwrite a file. Use for new, standalone notes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path":    {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "append_to_file",
        "description": "Append content to an existing file. Prefer over write_file when a relevant file already exists.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path":    {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "create_directory",
        "description": "Create a new directory.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "read_docx",
        "description": "Read the text content of a Word (.docx) file.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "append_to_docx",
        "description": "Append new content to the end of an existing Word (.docx) file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path":    {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
]


def dispatch(root: Path, name: str, args: dict) -> str:
    fns = {
        "list_directory":   lambda a: tool_list_directory(root, **a),
        "read_file":        lambda a: tool_read_file(root, **a),
        "write_file":       lambda a: tool_write_file(root, **a),
        "append_to_file":   lambda a: tool_append_to_file(root, **a),
        "create_directory": lambda a: tool_create_directory(root, **a),
        "read_docx":        lambda a: tool_read_docx(root, **a),
        "append_to_docx":   lambda a: tool_append_to_docx(root, **a),
    }
    return fns[name](args)


# ── Agentic loop ────────────────────────────────────────────────────────────────

def organize(user_input: str, root: Path, client: anthropic.Anthropic) -> None:
    system = f"""\
You are an intelligent organizer for prep notes and resources.

Notes folder: {root}

Current structure:
{folder_tree(root)}

When the user gives you a resource (note, link, paper, book, observation):
1. Explore relevant folders with list_directory, peek at existing files with read_file.
2. Decide the best location. Prefer appending to an existing file over creating a new one.
3. Format content cleanly in Markdown (heading, date if relevant, URL if present).
4. Write or append.
5. End with one sentence describing exactly what you did and where.

Never ask for confirmation — just act."""

    messages = [{"role": "user", "content": user_input}]

    with st.status("Working…", expanded=True) as status:
        for _ in range(MAX_ITER):
            response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=system,
                tools=TOOL_SCHEMAS,
                messages=messages,
            )

            # Print Claude's text
            for block in response.content:
                if block.type == "text" and block.text.strip():
                    st.markdown(block.text)

            if response.stop_reason == "end_turn":
                status.update(label="Done ✓", state="complete", expanded=False)
                break

            tool_uses = [b for b in response.content if b.type == "tool_use"]
            if not tool_uses:
                status.update(label="Done ✓", state="complete", expanded=False)
                break

            messages.append({"role": "assistant", "content": response.content})
            results = []

            for tu in tool_uses:
                status.update(label=f"`{tu.name}`…")

                # Show what Claude is doing
                args_preview = "  ".join(
                    f"**{k}** `{repr(v)[:60]}`" for k, v in tu.input.items()
                )
                st.markdown(f"→ `{tu.name}` — {args_preview}")

                try:
                    result_text = dispatch(root, tu.name, tu.input)
                    is_write = tu.name in ("write_file", "append_to_file", "create_directory", "append_to_docx")
                    st.caption(("✅ " if is_write else "   ") + result_text)
                except Exception as e:
                    result_text = f"Error: {e}"
                    st.caption(f"❌ {result_text}")

                results.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": result_text,
                })

            messages.append({"role": "user", "content": results})


# ── UI ──────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="PrepDrop",
    page_icon="🗂️",
    layout="wide",
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    # API key (hidden if already set via env var)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.subheader("API key")
        api_key_input = st.text_input(
            "Anthropic API key",
            type="password",
            label_visibility="collapsed",
            placeholder="sk-ant-...",
        )
        if api_key_input:
            st.session_state["api_key"] = api_key_input
        if not st.session_state.get("api_key"):
            st.caption("Get a key at [console.anthropic.com](https://console.anthropic.com)")
        st.divider()

    st.subheader("Notes folder")
    root_str = st.text_input("Path", value=DEFAULT_ROOT, label_visibility="collapsed")
    root = Path(root_str).expanduser().resolve()

    st.divider()

    if root.exists():
        st.code(folder_tree(root), language=None)
        if st.button("↺  Refresh tree"):
            st.rerun()
    else:
        st.error(f"Not found:\n{root}")
        st.caption("Set `NOTES_ROOT` env var or edit the path above.")

# ── Main ───────────────────────────────────────────────────────────────────────
st.title("🗂️  PrepDrop")

user_input = st.text_area(
    "Resource",
    height=180,
    label_visibility="collapsed",
    placeholder=(
        "Paste anything:\n\n"
        "  • A link     → https://arxiv.org/abs/...\n"
        "  • A note     → 'At the Meta screen they asked about two-tower rec sys models...'\n"
        "  • A book tip → 'Sutton & Barto ch.13 covers policy gradient clearly'\n"
        "  • A reminder → 'For Anthropic: re-read RLHF paper before the loop'"
    ),
)

client = get_client()
ready = bool(user_input.strip() and root.exists() and client)

go = st.button("Drop it →", type="primary", disabled=not ready)

if not client and not os.environ.get("ANTHROPIC_API_KEY"):
    st.caption("⚠️ Enter your Anthropic API key in the sidebar to get started.")

if go and ready:
    organize(user_input.strip(), root, client)
    st.divider()
    if st.button("↺  Refresh folder tree"):
        st.rerun()
