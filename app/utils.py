"""Helpers for turning Markdown plan text into structured, displayable data."""
import html
import re

import markdown as md
from markupsafe import Markup

_DAY_RE = re.compile(
    r"^[ \t]*(?:#{1,6}[ \t]*)?(?:\*\*|__)?[ \t]*Day[ \t]*(\d+)[ \t]*(?:[:\-\u2013\u2014.)][ \t]*)?(.*?)[ \t]*(?:\*\*|__)?[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)
_NOTES_RE = re.compile(
    r"^[ \t]*(?:#{1,6}[ \t]*)?(?:\*\*|__)?[ \t]*"
    r"(?:Important Notes|Additional Notes|Key Notes|Notes|Feedback adjustments|Tips|Disclaimer|Remember)\b.*$"
    r"|^[ \t]*(?:---|\*\*\*)[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)


def render_markdown(text: str | None) -> Markup:
    """Escape any raw HTML, then render Markdown. Safe to output in templates."""
    if not text:
        return Markup("")
    safe = html.escape(text, quote=False)
    return Markup(md.markdown(safe, extensions=["extra", "sane_lists"]))


def _clean_title(raw: str) -> str:
    return re.sub(r"[*_#]+", "", raw).strip(" :-\u2013\u2014.") or "Training day"


def split_plan(text: str | None) -> dict:
    """Split a plan into intro, per-day blocks and closing notes.

    Returns {"ok": bool, "intro": Markup, "days": [...], "notes": Markup, "full": Markup}.
    `ok` is False when Day 1..N headings could not be found; callers should then show `full`.
    """
    text = text or ""
    result = {"ok": False, "intro": Markup(""), "days": [], "notes": Markup(""),
              "full": render_markdown(text)}

    matches = []
    for m in _DAY_RE.finditer(text):
        if int(m.group(1)) == len(matches) + 1:  # only accept Day 1, 2, 3... in order
            matches.append(m)
    if len(matches) < 2:
        return result

    result["intro"] = render_markdown(text[: matches[0].start()].strip())
    notes_text = ""
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end(): end].strip()
        if i + 1 == len(matches):  # last day: split off closing notes
            cut = _NOTES_RE.search(body)
            if cut:
                notes_text = body[cut.start():].strip()
                body = body[: cut.start()].strip()
        title = _clean_title(m.group(2))
        rest = any(w in title.lower() for w in ("rest", "recovery", "recover"))
        result["days"].append({
            "number": i + 1, "title": title, "is_rest": rest, "html": render_markdown(body),
        })
    result["notes"] = render_markdown(notes_text)
    result["ok"] = True
    return result


def source_label(source: str | None) -> str:
    if not source or source == "offline":
        return "Built-in planner"
    return f"Gemini ({source})"
