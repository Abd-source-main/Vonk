# CODING AGENTS: READ THIS FIRST

> **Structure changed — read this before the section below.**
>
> The four prototypes that used to sit at the repo root have been split into two complete,
> independently editable locale routes, and **Dutch is now the default locale served from the
> site root**. There is no language chooser and no root redirect. The old filenames are gone:
>
> | Was | Now (Dutch) | Now (English) |
> |-----|-------------|---------------|
> | `Vonk Elektra Homepage.dc.html` | `public/nl/index.html` | `public/en/index.html` |
> | `Services & Portfolio.dc.html` | `public/nl/diensten.html` | `public/en/services.html` |
> | `About.dc.html` | `public/nl/over-ons.html` | `public/en/about.html` |
> | `Contact.dc.html` | `public/nl/contact.html` | `public/en/contact.html` |
>
> The privacy policy and terms pages were removed on purpose; they are the last thing to be
> written before launch, so a reviewed text ships instead of a template. Restoring them means
> four things, not one: the files, a footer link on every page, a `sitemap.xml` entry, and a
> reciprocal hreflang pair.
>
> **Everything published lives in `public/`** — that is the Cloudflare Pages output directory.
> `seo/` and this README sit outside it and are never served, which is deliberate: `seo/`
> contains an audit stating the reviews are fabricated and must not be readable at
> `vonkelektra.nl/seo/`.
>
> The two locales are `public/nl/` and `public/en/`, side by side. Nothing is served at the
> published root — `/` 301s to `/nl/` via `public/_redirects`. The `.dc.html` extension is gone;
> `support.js` and `uploads/` are shared and both routes reference them as `../support.js` and
> `../uploads/`.
>
> Canonicals are extensionless (`/nl/diensten`, `/en/services`) because Cloudflare Pages serves
> clean URLs and 301s the `.html` form. In-page links still say `diensten.html` on purpose, so
> the files open over `file://` during design work.
>
> Every page carries a language switch in the nav — a globe icon plus the target language code,
> `.r-nav-lang` — pointing at its own equivalent page in the other locale, never at the
> homepage.
>
> **Start with `seo/I18N.md`** — it explains the split, the editing rules, and the one command
> (`python seo/verify-i18n.py`) that catches the hreflang and broken-link mistakes which
> otherwise fail silently in production. `seo/SEO-AUDIT.md` lists what is still outstanding
> before launch; the reviews and service photos are still placeholders.

---

This is a **handoff bundle** from Claude Design (claude.ai/design).

A user mocked up designs in HTML/CSS/JS using an AI design tool, then exported this bundle so a coding agent can implement the designs for real.

## What you should do — IMPORTANT

**Read `public/nl/index.html` in full** — the Dutch homepage (formerly `project/Vonk Elektra Homepage.dc.html`). The user had this file open when they triggered the handoff, so it's almost certainly the primary design they want built. Read it top to bottom — don't skim. Then **follow its imports**: open every file it pulls in (shared components, CSS, scripts) so you understand how the pieces fit together before you start implementing.

**If anything is ambiguous, ask the user to confirm before you start implementing.** It's much cheaper to clarify scope up front than to build the wrong thing.

## About the design files

The design medium is **HTML/CSS/JS** — these are prototypes, not production code. Your job is to **recreate them pixel-perfectly** in whatever technology makes sense for the target codebase (React, Vue, native, whatever fits). Match the visual output; don't copy the prototype's internal structure unless it happens to fit.

**Don't render these files in a browser or take screenshots unless the user asks you to.** Everything you need — dimensions, colors, layout rules — is spelled out in the source. Read the HTML and CSS directly; a screenshot won't tell you anything they don't.

## Bundle contents

- `vonk-elektra-homepage-design/README.md` — this file
- `vonk-elektra-homepage-design/project/` — the `Vonk Elektra homepage design` project files (HTML prototypes, assets, components)
