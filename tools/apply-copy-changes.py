#!/usr/bin/env python
"""Apply the JSON the client sends back onto the real pages.

    python tools/apply-copy-changes.py vonk-teksten-2026-08-21.json
    python tools/apply-copy-changes.py changes.json --dry-run

Every edit is matched against the page source and rewritten in place. Two
things make that less trivial than a string swap:

  * The client edited rendered text, so what they saw is HTML-decoded and has
    its whitespace collapsed, while the source may hold entities and line
    breaks. Matching is therefore done with a whitespace- and entity-tolerant
    pattern rather than a literal find.
  * Roughly a third of the copy lives inside the design runtime's script block
    as JavaScript string literals, not as HTML text. Replacements there need
    JS escaping, not HTML escaping, so the insert is quoted to suit whichever
    context the match landed in.

Anything that does not match exactly once is left alone and reported, so a
partial run never silently mangles a page. Check `git diff` afterwards."""

import argparse, html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"

# Characters the source may carry either literally or as an entity.
ENTITIES = {
    "&": ["&amp;"],
    "'": ["&#39;", "&apos;", "&#x27;", "\u2019"],
    '"': ["&quot;", "&#34;"],
    "<": ["&lt;"],
    ">": ["&gt;"],
    "\u2019": ["&#8217;", "&rsquo;", "'"],
    "\u2014": ["&mdash;", "&#8212;"],
    "\u2013": ["&ndash;", "&#8211;"],
}


def pattern_for(text: str) -> re.Pattern:
    """A regex matching `text` however the source happens to encode it."""
    parts = []
    for ch in text:
        if ch.isspace():
            if parts and parts[-1] == r"\s+":
                continue
            parts.append(r"\s+")
            continue
        forms = [re.escape(ch)]
        for alt in ENTITIES.get(ch, []):
            forms.append(re.escape(alt))
        if ord(ch) > 127:
            forms.append(re.escape("&#%d;" % ord(ch)))
            forms.append(re.escape("&#x%x;" % ord(ch)))
        parts.append(forms[0] if len(forms) == 1 else "(?:%s)" % "|".join(forms))
    return re.compile("".join(parts))


def script_spans(source: str):
    """Byte ranges of the runtime's script blocks, where copy is JS, not HTML."""
    spans = []
    for m in re.finditer(r'<script[^>]*type="text/x-dc"[^>]*>', source):
        end = source.find("</script>", m.end())
        spans.append((m.end(), end if end != -1 else len(source)))
    return spans


def in_script(pos: int, spans) -> bool:
    return any(a <= pos < b for a, b in spans)


def encode_for(text: str, quote: str) -> str:
    """`quote` is the JS string delimiter the text sits inside, or "" for HTML."""
    if quote:
        # Escape the delimiter only. Escaping the other quote character too
        # would be legal but litters the source with needless backslashes —
        # an apostrophe in "airco's" does not need one inside "…".
        out = text.replace("\\", "\\\\").replace(quote, "\\" + quote)
        return out.replace("\n", "\\n").replace("\r", "")
    # HTML text node: only the structural characters need escaping.
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def delimiter_at(source: str, start: int, end: int) -> str:
    """The quote character wrapping a match, when it is a whole JS literal."""
    before = source[start - 1] if start else ""
    after = source[end] if end < len(source) else ""
    if before in ('"', "'") and before == after:
        return before
    return '"'      # inside a longer literal; assume the common case


def apply_page(path: Path, changes, dry_run: bool):
    source = path.read_text(encoding="utf-8")
    spans = script_spans(source)
    applied, problems = 0, []

    # Longest first: stops a short string from being rewritten inside a longer
    # one that is itself still waiting to be matched.
    for change in sorted(changes, key=lambda c: -len(c["from"])):
        want, new = change["from"], change["to"]
        if want == new:
            continue

        matches = list(pattern_for(want).finditer(source))
        if len(matches) != 1:
            problems.append((change, "geen match" if not matches
                             else "%d matches" % len(matches)))
            continue

        m = matches[0]
        quote = delimiter_at(source, m.start(), m.end()) \
            if in_script(m.start(), spans) else ""
        insert = encode_for(new, quote)
        source = source[:m.start()] + insert + source[m.end():]
        spans = script_spans(source)          # offsets moved
        applied += 1

    if applied and not dry_run:
        path.write_text(source, encoding="utf-8")
    return applied, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("changes", help="the JSON file the client sent back")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change without writing")
    args = ap.parse_args()

    data = json.loads(Path(args.changes).read_text(encoding="utf-8"))
    if data.get("format") != "vonk-copy-edits/1":
        sys.exit("not a copy-editor file (missing format marker)")

    total, unresolved = 0, []
    for page_id, page in data.get("pages", {}).items():
        path = PUBLIC / page["file"]
        if not path.exists():
            print("!! %s missing, skipped" % page["file"])
            continue

        applied, problems = apply_page(path, page["changes"], args.dry_run)
        total += applied
        state = "would apply" if args.dry_run else "applied"
        print("%-22s %s %d/%d" % (page["file"], state, applied, len(page["changes"])))
        for change, why in problems:
            unresolved.append((page["file"], change, why))

    print("\n%s %d change(s)" % ("would apply" if args.dry_run else "applied", total))

    if unresolved:
        print("\n%d need a hand — the text moved or appears more than once:"
              % len(unresolved))
        for file, change, why in unresolved:
            print("\n  %s  [%s]  %s" % (file, why, change.get("where", "")))
            print("    van: %s" % change["from"][:110])
            print("    naar: %s" % change["to"][:110])
        sys.exit(1)


if __name__ == "__main__":
    main()
