# -*- coding: utf-8 -*-
"""
Checks the two locale routes for the errors that silently kill hreflang:
  - missing self-referencing entry  (whole cluster discarded)
  - non-reciprocal pair             (pair dropped)
  - canonical not in the hreflang set (all hreflang ignored)
  - HTML annotations disagreeing with the sitemap (conflicting pair dropped)
  - broken local links
"""
import io, os, re, sys, glob
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\websites\vonk-elektra-homepage-design"
SITE = "https://vonkelektra.nl/"
os.chdir(ROOT)

fails = []


def note(ok, msg):
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        fails.append(msg)


# ---------------------------------------------------------------- gather pages
pages = {}   # url -> dict(file, canonical, alts{lang:url})
files = sorted(glob.glob("index.html") + glob.glob("nl/*.html") + glob.glob("en/*.html"))
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
        url_to_file[p["canonical"].rstrip("/") or SITE.rstrip("/")] = f

NO_HREFLANG = {"index.html"}   # the root chooser is noindex and outside the cluster
for f, p in sorted(pages.items()):
    print(" %s" % f)
    note(p["lang"] is not None, "  has <html lang> (%s)" % p["lang"])
    note(p["canonical"] is not None, "  has canonical")
    if f in NO_HREFLANG:
        note(not p["alts"], "  intentionally carries no hreflang")
        note("noindex" in p["body"], "  intentionally noindex")
        continue
    note(set(p["alts"]) >= {"nl", "en", "x-default"},
         "  declares nl + en + x-default (got %s)" % ",".join(sorted(p["alts"])))
    if p["canonical"] and p["alts"]:
        in_set = p["canonical"] in p["alts"].values()
        note(in_set, "  canonical appears in its own hreflang set")

# ---------------------------------------------------------------- reciprocity
print("\n== reciprocity (A names B  =>  B must name A)")
for f, p in sorted(pages.items()):
    for lang, target in p["alts"].items():
        if lang == "x-default":
            continue
        key = target.rstrip("/") or SITE.rstrip("/")
        tf = url_to_file.get(key)
        if tf is None:
            note(False, "%s -> %s (%s): target page not found locally" % (f, target, lang))
            continue
        back = pages[tf]["alts"]
        mine = p["canonical"]
        note(mine in back.values(),
             "%s <-> %s" % (f, tf))

# ---------------------------------------------------------------- sitemap agreement
print("\n== sitemap agrees with the HTML annotations")
ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9",
      "x": "http://www.w3.org/1999/xhtml"}
tree = ET.parse("seo/sitemap.xml")
sm = {}
for u in tree.getroot().findall("s:url", ns):
    loc = u.find("s:loc", ns).text
    alts = {a.get("hreflang"): a.get("href") for a in u.findall("x:link", ns)}
    sm[loc] = alts

note(len(sm) == len(pages) - len(NO_HREFLANG),
     "sitemap lists every indexable page (%d urls / %d indexable files)"
     % (len(sm), len(pages) - len(NO_HREFLANG)))

for loc, alts in sorted(sm.items()):
    key = loc.rstrip("/") or SITE.rstrip("/")
    f = url_to_file.get(key)
    if f is None:
        note(False, "sitemap <loc> %s has no page with that canonical" % loc)
        continue
    note(alts == pages[f]["alts"],
         "%s: sitemap hreflang == page hreflang" % loc)

# ---------------------------------------------------------------- local links
print("\n== local link targets resolve")
allf = sorted(glob.glob("index.html") + glob.glob("nl/*.html") + glob.glob("en/*.html"))
bad = 0
checked = 0
for f in allf:
    s = io.open(f, encoding="utf-8").read()
    base = os.path.dirname(f)
    for href in re.findall(r'(?:href|src)="([^"#?:]+?)"', s):
        h = href.replace("&amp;", "&")
        if h.startswith(("http", "mailto", "tel", "data:", "//")) or "{{" in h:
            continue
        target = os.path.normpath(os.path.join(base, h))
        checked += 1
        if not os.path.exists(target):
            print("  FAIL %s -> %s (missing)" % (f, h))
            bad += 1
note(bad == 0, "%d local references checked, %d broken" % (checked, bad))

print("\n" + ("ALL CHECKS PASSED" if not fails else "%d FAILURE(S)" % len(fails)))
sys.exit(1 if fails else 0)
