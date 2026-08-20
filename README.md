# CODING AGENTS: READ THIS FIRST

> **Structure changed — read this before the section below.**
>
> The four prototypes that used to sit at the repo root have been split into two
> complete, independently editable locale routes. The old filenames no longer exist:
>
> | Was | Now |
> |-----|-----|
> | `Vonk Elektra Homepage.dc.html` | `nl/index.dc.html` · `en/index.dc.html` |
> | `Services & Portfolio.dc.html` | `nl/diensten.dc.html` · `en/services.dc.html` |
> | `About.dc.html` | `nl/over-ons.dc.html` · `en/about.dc.html` |
> | `Contact.dc.html` | `nl/contact.dc.html` · `en/contact.dc.html` |
>
> Dutch is the primary locale. `index.html` at the root is a language chooser.
> `support.js` and `uploads/` stay at the root and are shared by both routes, which is
> why the pages reference them as `../support.js` and `../uploads/`.
>
> **Start with `seo/I18N.md`** — it explains the split, the editing rules, and the one
> command (`python seo/verify-i18n.py`) that catches the hreflang mistakes which
> otherwise fail silently in production. `seo/SEO-AUDIT.md` lists what is still
> outstanding before launch; the reviews and service photos are still placeholders.

---

This is a **handoff bundle** from Claude Design (claude.ai/design).

A user mocked up designs in HTML/CSS/JS using an AI design tool, then exported this bundle so a coding agent can implement the designs for real.

## What you should do — IMPORTANT

**Read `nl/index.dc.html` in full** (formerly `project/Vonk Elektra Homepage.dc.html`). The user had this file open when they triggered the handoff, so it's almost certainly the primary design they want built. Read it top to bottom — don't skim. Then **follow its imports**: open every file it pulls in (shared components, CSS, scripts) so you understand how the pieces fit together before you start implementing.

**If anything is ambiguous, ask the user to confirm before you start implementing.** It's much cheaper to clarify scope up front than to build the wrong thing.

## About the design files

The design medium is **HTML/CSS/JS** — these are prototypes, not production code. Your job is to **recreate them pixel-perfectly** in whatever technology makes sense for the target codebase (React, Vue, native, whatever fits). Match the visual output; don't copy the prototype's internal structure unless it happens to fit.

**Don't render these files in a browser or take screenshots unless the user asks you to.** Everything you need — dimensions, colors, layout rules — is spelled out in the source. Read the HTML and CSS directly; a screenshot won't tell you anything they don't.

## Bundle contents

- `vonk-elektra-homepage-design/README.md` — this file
- `vonk-elektra-homepage-design/project/` — the `Vonk Elektra homepage design` project files (HTML prototypes, assets, components)
