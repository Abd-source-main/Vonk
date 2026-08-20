# Vonk Elektra — SEO Audit

**Scope:** the four Claude Design prototype pages in this repo — `Vonk Elektra Homepage.dc.html`, `About.dc.html`, `Contact.dc.html`, `Services & Portfolio.dc.html` — plus `support.js` and `uploads/`.
**Date:** 20 August 2026
**Caveat:** this is a design handoff bundle, not a deployed site. There is no live URL, no Search Console, no traffic baseline. Findings below come from source inspection. Anything measurable only on a live host (Core Web Vitals field data, index coverage, backlinks) is marked *verify after launch*.

> **Status since this audit was written (21 August 2026).** The findings below are kept as the
> original record and still name the prototype filenames as they were. What has changed since:
>
> - **T5 (URLs)** — largely fixed. The spaces, ampersand and mixed case are gone, and so is the
>   `.dc.html` extension. Files are now `index.html`, `diensten.html`, `over-ons.html`,
>   `contact.html` plus the two legal pages, with English under `en/`. The one part of T5 still
>   open is the move from `.html` files to trailing-slash directory URLs
>   (`/diensten/`), which is a build-system change — see `SITE-ARCHITECTURE.md`.
> - **T6 (canonicals), T7 (robots/sitemap)** — done. Every page has a self-referencing absolute
>   canonical and a full hreflang set; `seo/robots.txt` and `seo/sitemap.xml` exist and agree
>   with the HTML.
> - **Locale structure** — Dutch is the default locale and is served from the site root. There
>   is no longer a language chooser at `/`; the switch is a globe in the nav of every page. See
>   `I18N.md`.
> - **C1 (placeholder reviews)** and the placeholder service imagery are **unchanged and still
>   block launch.**
>
> Run `python seo/verify-i18n.py` after any change to a filename, canonical or hreflang.

---

## Executive summary

The design is strong. The SEO layer does not exist yet — which is normal for a prototype, and exactly why fixing it before launch is cheap.

Two findings dominate everything else:

1. **The site is in English. The business is a Dutch installer in Nijmegen.** Nobody in Nijmegen searches "electrician Nijmegen." They search *elektricien Nijmegen*, *zonnepanelen laten installeren*, *warmtepomp Nijmegen*, *storing elektra spoed*. As it stands the site is invisible to essentially all of its commercial demand. This is not a meta-tag problem; it is the whole content layer.
2. **Eight services live as anchors on one page.** `#zonnepanelen` cannot rank. `/diensten/zonnepanelen/` can. Eight service pages is the difference between competing for one head term and competing for eight commercial-intent terms plus their long tails.

Behind those: no `<title>` on any page, no meta descriptions, no `lang`, no canonicals, no robots.txt, no sitemap, no structured data, and 26 MB of unreferenced images in `uploads/`.

**Top 5 priorities**

| # | Fix | Impact |
|---|-----|--------|
| 1 | Publish Dutch-language content as the primary locale | Critical |
| 2 | Split services into eight indexable URLs under `/diensten/` | Critical |
| 3 | Add title, meta description, `lang="nl"`, canonical to every page | Critical |
| 4 | Replace the placeholder reviews with real ones — or remove the section | Critical (legal) |
| 5 | Ship clean URLs, robots.txt, sitemap.xml, LocalBusiness schema | High |

**Quick wins** (under an hour each): `lang` attribute · titles and descriptions · robots.txt · sitemap.xml · delete the 26 MB of orphan images · add `width`/`height` to every `<img>` · self-host the fonts.

---

## Technical SEO findings

### T1 — No `<title>` element on any page

**Impact:** Critical · **Priority:** 1
**Evidence:** `grep -i "<title" *.dc.html` returns nothing across all four files.

Google will invent a title from page content or the URL. On a URL like `Services%20&%20Portfolio.dc.html` that goes badly.

**Fix:** one unique `<title>` per page. Copy is in `seo/COPY-AND-META.md`.

### T2 — No meta description on any page

**Impact:** Medium (no ranking effect; large CTR effect) · **Priority:** 2
**Evidence:** no `<meta name="description">` anywhere.

**Fix:** unique 150–160 character description per page. Written for you in `seo/COPY-AND-META.md`.

### T3 — No `lang` attribute

**Impact:** High · **Priority:** 1
**Evidence:** every file opens `<html>` with no attributes.

Bing in particular leans on `<html lang>` for language targeting, and screen readers pick the wrong pronunciation dictionary without it.

**Fix:** `<html lang="nl">` on Dutch pages, `<html lang="en">` on any English variant.

### T4 — Content and behaviour are entirely client-side rendered

**Impact:** High · **Priority:** 2
**Evidence:** `support.js` (69 KB) drives a custom template layer — `<x-dc>`, `<sc-for list="{{ slides }}">`, `<sc-if>`, `{{ mustache }}`. All eight service descriptions, the review cards, the proof-point marquee and the slider content exist only inside a JS class, not in the served HTML.

Googlebot does render JavaScript, but on a second pass, on a delay, and without guarantees. Bing and most AI crawlers are far weaker at it. Committing your entire commercial copy to a client-side template is a needless bet.

**Fix:** this is a prototype — when you build it for real, server-render or statically generate. The service copy, headings and links must be in the initial HTML response.

### T5 — URLs are unusable

**Impact:** High · **Priority:** 1
**Evidence:** `Vonk Elektra Homepage.dc.html`, `Services & Portfolio.dc.html` — spaces (encode to `%20`), an ampersand (a reserved character), mixed case, and a `.dc.html` extension.

**Fix:** the full URL map is in `seo/SITE-ARCHITECTURE.md`. Lowercase, hyphenated, Dutch, trailing slash.

### T6 — No canonical tags

**Impact:** High · **Priority:** 2

**Fix:** self-referencing absolute canonical on every page. Pick one host (`https://vonkelektra.nl`, no `www`) and one trailing-slash policy, then 301 everything else to it.

### T7 — No robots.txt, no XML sitemap

**Impact:** Medium · **Priority:** 2

**Fix:** both written — `seo/robots.txt`, `seo/sitemap.xml`. Deploy at the domain root and submit the sitemap in Search Console.

### T8 — No structured data

**Impact:** High for a local business · **Priority:** 1
**Evidence:** no `application/ld+json` in any file.

For a local installer this is the highest-leverage markup available: it feeds the knowledge panel, the local pack and AI answers.

**Fix:** `seo/schema/` — see the Schema section below.

### T9 — 26 MB of orphan images shipping in `uploads/`

**Impact:** Medium · **Priority:** 3
**Evidence:** `uploads/` is 50 MB. Unreferenced by any page or script: four `hf_2026*.png` files at ~6.5 MB each, `slide-04-fusebox-source.png` (6.2 MB), `5-1.png` (2.0 MB), `elektricien2.jpg`. The eight `mobile_*.png` files (up to 1.9 MB each) are referenced only through a `"mobile_*"` glob in JS — confirm they survive the production build.

**Fix:** delete the orphans. Convert what remains to WebP or AVIF at the sizes actually rendered. Target under 200 KB for any full-bleed hero image.

### T10 — No `width`/`height` on any image

**Impact:** Medium (CLS) · **Priority:** 3
**Evidence:** `grep -oE '<img[^>]*(width|height)=' *.dc.html` → 0 matches across 25 `<img>` elements.

Without intrinsic dimensions the browser cannot reserve space, so every image load shifts the layout. CLS is a Core Web Vitals metric.

**Fix:** add `width` and `height` attributes matching the true intrinsic size; let CSS handle display size.

### T11 — LCP element is unoptimised

**Impact:** Medium · **Priority:** 3
**Evidence:** the hero stacks two logo PNGs at `clamp(96px,15.3vw,220px)`. On desktop that pair is almost certainly the Largest Contentful Paint element. Neither is preloaded, neither has dimensions, and both sit behind a render-blocking Google Fonts stylesheet.

**Fix:** `<link rel="preload" as="image">` the hero mark, give it dimensions, and self-host the fonts with `font-display: swap`.

### T12 — Google Fonts loaded from Google's CDN

**Impact:** Low for SEO · **High for GDPR** · **Priority:** 2
**Evidence:** `<link href="https://fonts.googleapis.com/css2?family=Outfit...">` in every page's `<helmet>`.

Every visitor's IP address is transmitted to Google before they consent to anything. The Munich Regional Court ruled this an unlawful transfer in 2022 (Az. 3 O 17493/20), and the Dutch AP takes the same line. It also blocks you from truthfully claiming "no data goes to third parties" in the privacy policy.

**Fix:** self-host Outfit and Rubik (both are open-licensed). Faster *and* it makes the privacy claim true. See the marked block in `privacy.html`.

### T13 — Mobile and HTTPS

**Impact:** — · **Priority:** verify after launch

Viewport meta is present and correct, and the layout is genuinely responsive with sensible breakpoints at 1000px and 560px. Nothing to fix. HTTPS, HSTS, redirect chains and Core Web Vitals field data can only be checked once there is a live host.

---

## On-page SEO findings

### O1 — Not a single target keyword appears in any heading

**Impact:** Critical · **Priority:** 1

| Page | H1 | "elektricien"? | "Nijmegen"? |
|------|----|----------------|-------------|
| Home | "Living & working in complete comfort." | no | no |
| About | "The people behind the power." | no | no |
| Services | "Every service, and the work behind it." | no | no |
| Contact | "Let's get it sorted." | no | no |

These are good brand lines. They are not headlines a search engine can place. The fix is not to wreck the voice — let the H1 carry the service and the city, and move the poetic line to an eyebrow or subheadline. The rewrites in `seo/COPY-AND-META.md` keep "wonen en werken in comfort" as the spine.

### O2 — Duplicate H1/H2 on the services page

**Impact:** Low · **Priority:** 4
**Evidence:** "Every service, and the work behind it." appears as both the `<h1>` (line 161) and an `<h2>` (line 244) in `Services & Portfolio.dc.html`.

**Fix:** differentiate. The H1 targets the head term; the H2 introduces the walkthrough.

### O3 — Heading level skipped on the contact page

**Impact:** Low (accessibility more than SEO) · **Priority:** 4
**Evidence:** `Contact.dc.html` goes `<h1>` → `<h3>` with no `<h2>`.

**Fix:** promote the `<h3>` or insert the missing level.

### O4 — Footer service links all point to the same anchor

**Impact:** Medium · **Priority:** 2
**Evidence:** "Solar panels", "Home batteries", "Air conditioning" and "Fault repair" in the footer all resolve to `href="#services"`. Four distinct anchor texts, one destination, on the current page.

**Fix:** point each at its own `/diensten/{slug}/` page. Descriptive anchor text pointing at matching URLs is one of the cheapest internal-linking wins available.

### O5 — Image alt text: better than typical, with gaps

**Impact:** Low · **Priority:** 3

**Good:** all 25 images carry an `alt`; decorative wires and orbs correctly use `alt=""` plus `aria-hidden`; the paired logo lock-up correctly gives the mark `alt=""` and the wordmark `alt="Vonk Elektra"` so it is announced once.

**Gaps:** slider alts come from `{{ s.alt }}` in JS — confirm those strings survive the build. Filenames like `hf_20260730_211614_526c064a...png`, `images.jpeg`, `out.jpg`, `1-1.png` and `Screenshot_2026-08-08_235630_....webp` carry no signal.

**Fix:** rename to `zonnepanelen-nijmegen-schuin-dak.jpg` and similar. Write alts in Dutch on Dutch pages.

### O6 — Service imagery is still placeholder

**Impact:** Medium · **Priority:** 2
**Evidence:** the `services` array in `Vonk Elektra Homepage.dc.html` has `img:"[ photo: solar panels on a Dutch roof ]"` and seven similar bracketed stand-ins.

**Fix:** real photography of real Vonk jobs. Original photos of your own work are also an E-E-A-T signal that stock cannot buy.

---

## Content and trust findings

### C1 — The reviews are fabricated, and the code says so

**Impact:** Critical · **Priority:** 1
**Evidence:** in `Vonk Elektra Homepage.dc.html`, above the reviews section:

> `⚠ PLACEHOLDER COPY — the quotes and names below are illustrative, not real customer reviews. Replace with genuine, attributable reviews before this goes live.`

and again at line 680: `PLACEHOLDER REVIEWS — representative copy for layout only. These are NOT real customer reviews.`

The designer flagged this properly. It must not survive to production. Publishing invented testimonials with invented customer names is a misleading commercial practice under the Wet oneerlijke handelspraktijken, actively enforced by the ACM against installers. Wrapping them in `Review`/`AggregateRating` schema adds a Google structured-data manual action on top.

**Fix:** collect real reviews (Google Business Profile is the obvious source and feeds the local pack anyway), or ship without the section. `seo/schema/05-reviews-DO-NOT-SHIP-YET.jsonld` holds the markup, deliberately left uninstallable until it holds real data.

### C2 — Stat claims need substantiation

**Impact:** Medium · **Priority:** 2
**Evidence:** "100% work done to code", "4 wks from approval to solar on your roof", "7/7 fault response".

These are good, specific, differentiating claims — exactly the kind that convert. They also need to be true and defensible. "7/7" reads as a 24/7 promise; the body copy says "evenings and weekends included", which is a different commitment.

**Fix:** keep the specificity, tighten the wording so it matches what you actually deliver.

### C3 — No privacy policy, no terms

**Impact:** Medium (E-E-A-T, and legally required) · **Priority:** 1

**Fix:** delivered — `privacy.html` and `terms.html`, to be linked from the footer.

### C4 — No Google Business Profile signals

**Impact:** High for local · **Priority:** 1
**Evidence:** `sameAs` has nothing to point at; no GBP embed, no review widget, no map.

For "elektricien Nijmegen" the local pack sits above the organic results. A complete, verified, actively-reviewed Google Business Profile matters more than anything on this page.

**Fix:** claim and verify the profile. Make NAP identical to the footer, byte for byte: *Vonk Installatie & Onderhoud B.V. · De Kluijskamp 1273 · 6545 JK Nijmegen · 024 785 1050*. Then add the profile URL to `sameAs` in the schema.

### C5 — Thin content depth for commercial queries

**Impact:** High · **Priority:** 2

Each service currently gets roughly 60 words. Competitors ranking for *zonnepanelen Nijmegen* run 800–1500 words plus FAQs, pricing indications and job photos.

**Fix:** 600–900 words per service page, in Dutch: what it costs (a range is fine, and it is what people search for), how long it takes, what happens on the day, what standards you work to, three to five FAQs, photos of your own work. Depth earns the ranking; schema only helps Google understand it.

### C6 — What is genuinely working

Worth stating, because it is unusual: NAP is consistent across all four pages, `tel:` links use correct E.164 (`+31247851050`), KvK and BTW numbers are published in the footer, the slider has real ARIA labels and keyboard-reachable controls, decorative imagery is correctly hidden from assistive tech, and the brand voice is specific and human rather than generic installer-speak. That last one is the hardest to buy and you already have it. Everything above is scaffolding around it.

---

## Prioritised action plan

**Phase 1 — before launch (blocking)**

1. Commit to Dutch as the primary locale and translate the content layer
2. Build the eight `/diensten/{slug}/` pages with real depth
3. Titles, meta descriptions, `lang="nl"`, self-referencing canonicals
4. Replace or remove the placeholder reviews
5. Deploy `robots.txt`, `sitemap.xml`, and the LocalBusiness schema from `seo/schema/`
6. Publish `privacy.html` and `terms.html`, linked in the footer
7. Clean URLs per `seo/SITE-ARCHITECTURE.md`

**Phase 2 — launch week**

8. Claim and verify the Google Business Profile; align NAP exactly
9. Self-host the fonts (speed + GDPR)
10. Delete the orphan images, convert the rest to WebP, add `width`/`height`
11. Fix the footer service links; add breadcrumbs
12. Verify in Search Console and Bing Webmaster Tools; submit the sitemap
13. Validate every page in the Rich Results Test — it renders JS, `curl` does not

**Phase 3 — first 90 days**

14. Collect real reviews continuously; add `Review` schema once genuine
15. Location pages for Beuningen, Wijchen, Malden, Groesbeek, Elst — only where you can write genuinely local content
16. `/projecten/` case studies with real photos, one per service
17. Start measuring which service pages earn calls, not just clicks
