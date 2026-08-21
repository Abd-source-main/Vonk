#!/usr/bin/env python
"""Build a single self-contained HTML file the client can open, edit the site's
text in, and hand back as a JSON file.

    python tools/build-copy-editor.py

Writes tools/out/vonk-teksten-aanpassen.html. Needs an internet connection when
opened: the pages pull the design runtime's React build and Google Fonts.
Apply the returned file with tools/apply-copy-changes.py."""

import base64, io, json, mimetypes, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
OUT = Path(__file__).resolve().parent / "out"

PAGES = [
    ("nl-home",     "nl/index.html",     "NL", "Home"),
    ("nl-diensten", "nl/diensten.html",  "NL", "Diensten"),
    ("nl-over-ons", "nl/over-ons.html",  "NL", "Over ons"),
    ("nl-contact",  "nl/contact.html",   "NL", "Contact"),
    ("en-home",     "en/index.html",     "EN", "Home"),
    ("en-services", "en/services.html",  "EN", "Services"),
    ("en-about",    "en/about.html",     "EN", "About"),
    ("en-contact",  "en/contact.html",   "EN", "Contact"),
]

MAX_W = 1400          # px; the design never renders wider than this
JPEG_Q = 72


def embed(value) -> str:
    """JSON for use inside a <script> block.

    The pages we are embedding contain their own </script> tags; left alone the
    first one would close the shell's script early and dump the rest of the
    bundle into the page as text."""
    # ensure_ascii already escapes the line separators that would break out
    # of a JS string, so </ is the only thing left to neutralise.
    return json.dumps(value, ensure_ascii=True).replace("</", "<\\/")


def has_alpha(img) -> bool:
    """True only when some pixel is actually see-through."""
    if img.mode == "P":
        if "transparency" not in img.info:
            return False
        img = img.convert("RGBA")
    if img.mode not in ("RGBA", "LA"):
        return False
    return img.convert("RGBA").getchannel("A").getextrema()[0] < 255


def data_uri(path: Path) -> str:
    """Inline an upload, downscaling photos so the bundle stays emailable."""
    raw = path.read_bytes()
    suffix = path.suffix.lower()

    if suffix in (".svg", ".gif"):
        mime = "image/svg+xml" if suffix == ".svg" else "image/gif"
        return "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode())

    from PIL import Image
    try:
        img = Image.open(io.BytesIO(raw))
    except Exception:
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode())

    if img.width > MAX_W:
        img = img.resize((MAX_W, round(img.height * MAX_W / img.width)), Image.LANCZOS)

    buf = io.BytesIO()
    # Only genuinely transparent images need PNG. Several of the uploads are
    # photos saved as RGBA with a fully opaque alpha channel; sent as JPEG they
    # cost a fraction of the bytes.
    if has_alpha(img):
        img.convert("RGBA").save(buf, "PNG", optimize=True)
        mime = "image/png"
    else:
        img.convert("RGB").save(buf, "JPEG", quality=JPEG_Q, optimize=True, progressive=True)
        mime = "image/jpeg"

    out = buf.getvalue()
    if len(out) >= len(raw) and suffix in (".jpg", ".jpeg", ".png", ".webp"):
        out = raw
        mime = mimetypes.guess_type(path.name)[0] or mime
    return "data:%s;base64,%s" % (mime, base64.b64encode(out).decode())


def build_image_map(sources):
    """Every upload the pages could ask for, as a data URI.

    Matching on the filename rather than on "../uploads/name" is deliberate:
    the carousels assemble their paths at run time from a bare stem
    ("../uploads/" + s.file + ".jpg"), so the full path never appears in the
    source and a path-based scan misses all ten slide images."""
    blob = "\n".join(sources)

    written = set(re.findall(r"\.\./uploads/([A-Za-z0-9._-]+)", blob))
    missing = sorted(n for n in written if not (PUBLIC / "uploads" / n).exists())

    uris = {}
    for path in sorted((PUBLIC / "uploads").iterdir()):
        if not path.is_file():
            continue
        # Stem, so "slide-01-solar.jpg" is found via file:"slide-01-solar",
        # and stem minus a width suffix, for the "-1200" srcset variants the
        # same code builds alongside it.
        base = re.sub(r"-\d+$", "", path.stem)
        if path.name not in blob and path.stem not in blob and base not in blob:
            continue
        uris["../uploads/" + path.name] = data_uri(path)
    return uris, missing


def transform(html: str, page_id: str, support_js: str, overlay_js: str) -> str:
    """Turn a production page into an editable copy of itself."""

    # The runtime ships as a sibling file; the editor is one standalone file.
    html = html.replace(
        '<script src="../support.js"></script>',
        "<script>\n%s\n</script>" % support_js,
    )

    # Images are swapped for data URIs by the shell before the page reaches
    # the iframe, so the 24 photos are stored once, not eight times over.
    boot = "<script>window.__CE_PAGE=%s;</script>" % json.dumps(page_id)
    html = html.replace("</head>", boot + "\n</head>", 1)

    overlay = "<script>\n%s\n</script>" % overlay_js
    html = html.replace("</body>", overlay + "\n</body>", 1)
    return html


def main():
    support_js = (PUBLIC / "support.js").read_text(encoding="utf-8")
    overlay_js = (ROOT / "tools" / "editor-overlay.js").read_text(encoding="utf-8")
    shell_tpl = (ROOT / "tools" / "editor-shell.html").read_text(encoding="utf-8")

    raw = {}
    for page_id, rel, _, _ in PAGES:
        path = PUBLIC / rel
        if not path.exists():
            sys.exit("missing page: %s" % rel)
        raw[page_id] = path.read_text(encoding="utf-8")

    print("inlining images ...")
    images, skipped = build_image_map(raw.values())
    for name in skipped:
        print("  ! referenced but not on disk: %s" % name)
    total = sum(len(v) for v in images.values())
    print("  %d images, %.1f MB inlined" % (len(images), total / 1048576))

    docs = {}
    for page_id, rel, lang, label in PAGES:
        docs[page_id] = transform(raw[page_id], page_id, support_js, overlay_js)

    manifest = [
        {"id": p, "file": rel, "lang": lang, "label": label}
        for p, rel, lang, label in PAGES
    ]

    out_html = (
        shell_tpl
        .replace("/*__MANIFEST__*/", embed(manifest))
        .replace("/*__IMAGES__*/", embed(images))
        .replace("/*__DOCS__*/", embed(docs))
    )

    OUT.mkdir(exist_ok=True)
    dest = OUT / "vonk-teksten-aanpassen.html"
    dest.write_text(out_html, encoding="utf-8")
    print("wrote %s  (%.1f MB)" % (dest, dest.stat().st_size / 1048576))


if __name__ == "__main__":
    main()
