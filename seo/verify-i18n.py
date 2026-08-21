# -*- coding: utf-8 -*-
"""
Checks the two locale routes for the errors that silently kill hreflang:
  - missing self-referencing entry  (whole cluster discarded)
  - non-reciprocal pair             (pair dropped)
  - canonical not in the hreflang set (all hreflang ignored)
  - HTML annotations disagreeing with the sitemap (conflicting pair dropped)
  - leftovers from the old flat + .dc.html layout
  - broken local links

Layout: everything published lives in public/ — the Cloudflare Pages output
directory. seo/ and README.md sit outside it and are never served. Dutch is the
locale routes are public/nl/ and public/en/, side by side. Nothing is served at
the published root: / is a 301 to /nl/, declared in _redirects.

URLs: Cloudflare Pages serves clean URLs, so canonicals are extensionless
(/nl/diensten, /en/services) and the two homepages use the directory form
(/nl/ and /en/). Internal href="diensten.html" links are intentional — they keep
the files openable over file:// and Cloudflare resolves both to one page.
"""
import io, os, re, sys, glob
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public")
SITE = "https://vonkelektra.nl/"
os.chdir(ROOT)

fails = []


def note(ok, msg):
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        fails.append(msg)


def key_of(url):
    """Collapse trailing slashes so / and /en/ compare cleanly."""
    return url.rstrip("/") or SITE.rstrip("/")


# ---------------------------------------------------------------- gather pages
pages = {}   # file -> dict(canonical, alts{lang:url}, lang, body)
files = sorted(glob.glob("nl/*.html") + glob.glob("en/*.html"))
for f in files:
    s = io.open(f, encoding="utf-8").read()
    can = re.search(r'<link rel="canonical" href="([^"]+)"', s)
    alts = dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', s))
    lang = re.search(r'<html lang="([^"]+)"', s)
    pages[f.replace("\\", "/")] = dict(
        canonical=can.group(1) if can else None,
        alts=alts,
        lang=lang.group(1) if lang else None,
        body=s,
    )

print("== pages found: %d" % len(pages))

# ---------------------------------------------------------------- per-page hreflang
print("\n== hreflang per page")
url_to_file = {}
for f, p in pages.items():
    if p["canonical"]:
        url_to_file[key_of(p["canonical"])] = f

for f, p in sorted(pages.items()):
    print(" %s" % f)
    note(p["lang"] is not None, "  has <html lang> (%s)" % p["lang"])
    note(p["canonical"] is not None, "  has canonical")
    note(set(p["alts"]) >= {"nl", "en", "x-default"},
         "  declares nl + en + x-default (got %s)" % ",".join(sorted(p["alts"])))
    if p["canonical"] and p["alts"]:
        note(p["canonical"] in p["alts"].values(),
             "  canonical appears in its own hreflang set")

# Cloudflare Pages serves diensten.html at /diensten and 301s /diensten.html to
# it. A canonical ending in .html would therefore point at a redirect rather than
# at the page, which is a self-conflicting signal. Homepages take the directory
# form; every other page takes the extensionless form.
print("\n== canonicals match the URL Cloudflare actually serves")
for f, want in (("nl/index.html", SITE + "nl/"), ("en/index.html", SITE + "en/")):
    note(pages[f]["canonical"] == want,
         "%s canonical is %s (got %s)" % (f, want, pages[f]["canonical"]))
for f, p in sorted(pages.items()):
    if f in ("nl/index.html", "en/index.html"):
        continue
    note(not (p["canonical"] or ".html").endswith(".html"),
         "%s canonical is extensionless (%s)" % (f, p["canonical"]))
for f, p in sorted(pages.items()):
    bad = [u for u in p["alts"].values() if u.endswith(".html")]
    note(not bad, "%s: no hreflang target ends in .html%s"
                  % (f, (" — " + ", ".join(bad)) if bad else ""))

# x-default belongs on the Dutch route, which is the root
print("\n== x-default points at the Dutch route")
for f, p in sorted(pages.items()):
    xd = p["alts"].get("x-default")
    note(xd is not None and xd == p["alts"].get("nl"),
         "%s: x-default == its nl alternate (%s)" % (f, xd))

# ---------------------------------------------------------------- reciprocity
print("\n== reciprocity (A names B  =>  B must name A)")
for f, p in sorted(pages.items()):
    for lang, target in p["alts"].items():
        if lang == "x-default":
            continue
        tf = url_to_file.get(key_of(target))
        if tf is None:
            note(False, "%s -> %s (%s): target page not found locally" % (f, target, lang))
            continue
        note(p["canonical"] in pages[tf]["alts"].values(), "%s <-> %s" % (f, tf))

# ---------------------------------------------------------------- sitemap agreement
print("\n== sitemap agrees with the HTML annotations")
ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9",
      "x": "http://www.w3.org/1999/xhtml"}
tree = ET.parse("sitemap.xml")
sm = {}
for u in tree.getroot().findall("s:url", ns):
    loc = u.find("s:loc", ns).text
    sm[loc] = {a.get("hreflang"): a.get("href") for a in u.findall("x:link", ns)}

note(len(sm) == len(pages),
     "sitemap lists every indexable page (%d urls / %d files)" % (len(sm), len(pages)))

for loc, alts in sorted(sm.items()):
    f = url_to_file.get(key_of(loc))
    if f is None:
        note(False, "sitemap <loc> %s has no page with that canonical" % loc)
        continue
    note(alts == pages[f]["alts"], "%s: sitemap hreflang == page hreflang" % loc)

# ---------------------------------------------------------------- old layout
print("\n== no leftovers from the old /nl/ + .dc.html layout")
STALE = re.compile(r'(?:href|src)="([^"]*\.dc\.html[^"]*)"')
stale = 0
for f, p in sorted(pages.items()):
    for hit in STALE.findall(p["body"]):
        print("  FAIL %s -> %s" % (f, hit))
        stale += 1
note(stale == 0, "%d stale link(s) to the old layout" % stale)
note(os.path.isdir("nl") and os.path.isdir("en"), "both locale folders exist")
note(not os.path.exists("index.html"),
     "no page at the published root — / is a redirect to /nl/, handled in _redirects")
rd = io.open("_redirects", encoding="utf-8").read()
note(any(l.split()[:2] == ["/", "/nl/"] for l in rd.splitlines() if l.startswith("/")),
     "_redirects sends / to /nl/ (without it the bare domain serves nothing)")
note(os.path.exists("_redirects"), "_redirects is in the published directory")
note(os.path.exists("robots.txt") and os.path.exists("sitemap.xml"),
     "robots.txt and sitemap.xml are in the published directory")
note(not os.path.exists("README.md") and not os.path.isdir("seo"),
     "internal notes are NOT in the published directory")
note(not os.path.exists("index.html.orig"), "no stray backup files at the root")

# ---------------------------------------------------------------- language switch
print("\n== every page offers the other language")
for f, p in sorted(pages.items()):
    sw = re.search(r'<a href="([^"]+)"[^>]*class="r-nav-lang"', p["body"]) \
        or re.search(r'<a href="([^"]+)"[^>]*hreflang="(?:nl|en)"[^>]*>(?:English|Nederlands)<', p["body"])
    if sw is None:
        note(False, "%s: no visible language switch" % f)
        continue
    target = os.path.normpath(os.path.join(os.path.dirname(f), sw.group(1).split("#")[0]))
    note(os.path.exists(target), "%s -> %s" % (f, sw.group(1)))

# ---------------------------------------------------------------- local links
print("\n== local link targets resolve")
bad = 0
checked = 0
for f, p in sorted(pages.items()):
    base = os.path.dirname(f)
    for href in re.findall(r'(?:href|src)="([^"]+)"', p["body"]):
        h = href.replace("&amp;", "&").split("#")[0].split("?")[0]
        if not h or h.startswith(("http", "mailto", "tel", "data:", "//")) or "{{" in h:
            continue
        checked += 1
        if not os.path.exists(os.path.normpath(os.path.join(base, h))):
            print("  FAIL %s -> %s (missing)" % (f, href))
            bad += 1
note(bad == 0, "%d local references checked, %d broken" % (checked, bad))

print("\n" + ("ALL CHECKS PASSED" if not fails else "%d FAILURE(S)" % len(fails)))
sys.exit(1 if fails else 0)
