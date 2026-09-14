# Copy editor

A one-off way to let the client rewrite the site's text without touching the
repo, a CMS, or the live site.

`build-copy-editor.py` bundles all eight pages into a single HTML file. The
client opens it, edits the words in place on what looks like the real site, and
clicks **Save changes** to get a small JSON file back.
`apply-copy-changes.py` writes those edits into `public/`.

## Making the file

```
python tools/build-copy-editor.py
```

Writes `tools/out/vonk-teksten-aanpassen.html` (~3.6 MB) — email it, or put it
on a USB stick. Nothing else needs to be sent with it: images are inlined as
data URIs and the design runtime is inlined from `public/support.js`.

**The client needs to be online when they open it.** The pages pull React from
unpkg and the fonts from Google, exactly as the live site does. Offline, the
carousels will not render.

Tested in Chrome. The editor uses `contenteditable="plaintext-only"`, which
Firefox has only supported since v136 — Chrome or Edge is the safe instruction.

## Applying what comes back

```
python tools/apply-copy-changes.py vonk-teksten-2026-08-21.json --dry-run
python tools/apply-copy-changes.py vonk-teksten-2026-08-21.json
git diff public/
```

Always read the diff. Anything the script could not place uniquely is skipped
and printed at the end for you to do by hand — it never guesses.

## How it holds together

`editor-shell.html` is the outer frame: page tabs, the change counter, the save
button, and a `localStorage` copy of everything typed so far. It loads one page
at a time into an iframe via `srcdoc`.

`editor-overlay.js` is injected into each page. Once the DOM settles it walks
every visible text node and makes it editable — editing the element in place
where it holds nothing but text, wrapping the run in a span otherwise, so the
layout never shifts. It reports each change to the shell over `postMessage`
rather than `window.parent`, because a file opened from disk gets an opaque
origin and direct property access would fail there.

Three things about this site made the naive version of this not work, and the
code carries a comment at each:

- **Copy lives in two places.** Roughly a third of the words — the homepage
  carousel, the service cards — are JavaScript string literals inside the
  design runtime's `<script type="text/x-dc">` block, not HTML text. They are
  editable because the overlay reads the rendered DOM, and they are writable
  because `apply-copy-changes.py` detects when a match landed inside that block
  and escapes the replacement as JS instead of HTML.
- **Some image paths are assembled at run time** (`"../uploads/" + s.file +
  ".jpg"`), so they never appear in the source for the build to find. The build
  matches uploads by filename stem instead, and the overlay asks the shell for
  anything still pointing at `../uploads/` after the page has rendered.
- **The embedded pages contain their own `</script>` tags**, which would close
  the shell's script block early. `embed()` escapes them.

## Known rough edge

Headings styled with an inline `<span>` split into two editable fields, because
they are two text nodes. The client edits each half separately. Fixing it
properly would mean merging adjacent inline text nodes, which risks losing the
styling that made them separate in the first place.
