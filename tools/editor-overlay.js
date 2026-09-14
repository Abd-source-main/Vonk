/* Copy-editor overlay. Injected into a copy of each live page.
   Makes visible text editable in place and reports every change to the shell.
   Talks to the shell over postMessage rather than window.parent, so it keeps
   working when the client opens the file straight from disk, where Chrome
   gives the page an opaque origin. Build artefact — never shipped. */
(function () {
  "use strict";

  var PAGE = window.__CE_PAGE;
  var SKIP_TAGS = { SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, SVG: 1, PATH: 1, TITLE: 1, HELMET: 1, TEMPLATE: 1 };
  var nodes = [];
  var byKey = {};

  function send(type, data) {
    var msg = { channel: "vonk-copy-editor", type: type, page: PAGE };
    for (var k in data) msg[k] = data[k];
    try { window.parent.postMessage(msg, "*"); } catch (e) {}
  }

  /* ---- locating text ------------------------------------------------ */

  function skipped(el) {
    for (var n = el; n && n.nodeType === 1; n = n.parentNode) {
      if (SKIP_TAGS[n.tagName]) return true;
      if (n.hasAttribute && n.hasAttribute("data-ce-ignore")) return true;
    }
    return false;
  }

  /* A human-readable "where is this" label, built from the nearest landmark. */
  function describe(el) {
    var section = "";
    for (var n = el; n && n.nodeType === 1; n = n.parentNode) {
      if (n.id) { section = n.id; break; }
      if (n.tagName === "HEADER") { section = "header"; break; }
      if (n.tagName === "FOOTER") { section = "footer"; break; }
      if (n.tagName === "NAV") { section = "menu"; break; }
    }
    var tag = el.tagName.toLowerCase();
    var kind = /^h[1-6]$/.test(tag) ? "heading" :
               tag === "a" ? "link/button" :
               tag === "button" ? "button" :
               tag === "li" ? "list item" : "text";
    return (section || "page") + " · " + kind;
  }

  function sectionOf(el) {
    return describe(el).split(" · ")[0];
  }

  function collect() {
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode: function (t) {
        if (!t.nodeValue || !t.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        if (!t.parentElement || skipped(t.parentElement)) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var found = [], t;
    while ((t = walker.nextNode())) found.push(t);
    return found;
  }

  /* ---- making it editable ------------------------------------------- */

  var counter = 0;

  function mount(textNode) {
    var parent = textNode.parentElement;
    if (!parent) return;
    var host;

    /* Element holds nothing but this text: edit the element itself, so the
       layout is untouched. Otherwise wrap the run in an inline span. */
    if (parent.childNodes.length === 1) {
      host = parent;
    } else {
      host = document.createElement("span");
      host.style.display = "inline";
      textNode.parentNode.replaceChild(host, textNode);
      host.appendChild(textNode);
    }
    if (host.hasAttribute("data-ce-key")) return;

    var original = textNode.nodeValue;
    var key = PAGE + ":" + sectionOf(parent) + ":" + (counter++);

    host.setAttribute("data-ce-key", key);
    host.classList.add("ce-field");
    try { host.contentEditable = "plaintext-only"; }
    catch (e) { host.contentEditable = "true"; }
    host.spellcheck = true;
    host.setAttribute("title", "Click to edit this text");

    var rec = { key: key, host: host, original: original, where: describe(parent) };
    nodes.push(rec);
    byKey[key] = rec;

    host.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { e.preventDefault(); host.blur(); }
    });
    host.addEventListener("input", function () { changed(rec, false); });
    host.addEventListener("focus", function () { host.classList.add("ce-active"); });
    host.addEventListener("blur", function () {
      host.classList.remove("ce-active");
      changed(rec, true);
    });
  }

  function tidy(s) {
    return s.replace(/\s+/g, " ").trim();
  }

  function changed(rec, settle) {
    var was = tidy(rec.original);
    var now = tidy(rec.host.textContent);

    /* An emptied field collapses to an unclickable sliver — put it back. */
    if (settle && !now) {
      rec.host.textContent = rec.original;
      now = was;
    }

    var dirty = now !== was;
    rec.host.classList.toggle("ce-changed", dirty);
    send("record", { key: rec.key, entry: {
      original: was, updated: now, where: rec.where, dirty: dirty
    }});
  }

  /* ---- restore previously typed edits -------------------------------- */

  function restore(saved) {
    if (!saved) return;
    nodes.forEach(function (rec) {
      var v = saved[rec.key];
      if (v && v.dirty && v.updated) {
        rec.host.textContent = v.updated;
        rec.host.classList.add("ce-changed");
      }
    });
  }

  window.addEventListener("message", function (e) {
    var d = e.data;
    if (!d || d.channel !== "vonk-copy-editor") return;
    if (d.type === "saved") restore(d.saved);
    if (d.type === "images") paintImages(d.images);
  });

  /* ---- late-bound images --------------------------------------------- */

  /* The carousels assemble their own paths at run time ("../uploads/" + file
     + ".jpg"), so those never met the build's search-and-replace. Ask the
     shell for whatever is still pointing at the uploads folder. */

  function uploadRefs() {
    var wanted = {};
    Array.prototype.forEach.call(document.querySelectorAll("img"), function (img) {
      ["src", "srcset"].forEach(function (attr) {
        var v = img.getAttribute(attr);
        if (!v) return;
        (v.match(/\.\.\/uploads\/[A-Za-z0-9._-]+/g) || []).forEach(function (p) {
          wanted[p] = 1;
        });
      });
    });
    return Object.keys(wanted);
  }

  function paintImages(map) {
    if (!map) return;
    Array.prototype.forEach.call(document.querySelectorAll("img"), function (img) {
      ["src", "srcset"].forEach(function (attr) {
        var v = img.getAttribute(attr);
        if (!v || v.indexOf("../uploads/") === -1) return;
        var next = v;
        for (var ref in map) next = next.split(ref).join(map[ref]);
        if (next !== v) img.setAttribute(attr, next);
      });
    });
  }

  /* ---- keep the client inside the editor ----------------------------- */

  function neutralise() {
    document.addEventListener("click", function (e) {
      var a = e.target.closest && e.target.closest("a[href]");
      if (!a) return;
      var href = a.getAttribute("href") || "";
      if (href.charAt(0) === "#") return;      /* in-page anchors still work */
      e.preventDefault();
      send("notify", { message: "Links are disabled in this text-editing copy." });
    }, true);
    Array.prototype.forEach.call(document.querySelectorAll("form"), function (f) {
      f.addEventListener("submit", function (e) { e.preventDefault(); });
    });
  }

  function styles() {
    var css = document.createElement("style");
    css.textContent = [
      ".ce-field{outline:none;cursor:text;border-radius:3px;",
      "  transition:background-color .15s ease,box-shadow .15s ease;}",
      ".ce-field:hover{background:rgba(230,114,6,.13);",
      "  box-shadow:0 0 0 2px rgba(230,114,6,.35);}",
      ".ce-active{background:rgba(230,114,6,.18)!important;",
      "  box-shadow:0 0 0 2px #E67206!important;}",
      ".ce-changed{background:rgba(46,160,67,.16);",
      "  box-shadow:0 0 0 2px rgba(46,160,67,.5);}",
      ".ce-changed.ce-active{background:rgba(46,160,67,.22)!important;}",
      "@media print{.ce-field{background:none!important;box-shadow:none!important;}}"
    ].join("");
    document.head.appendChild(css);
  }

  /* ---- boot ---------------------------------------------------------- */

  function boot() {
    styles();
    collect().forEach(mount);
    neutralise();
    send("ready", { fields: nodes.length, needImages: uploadRefs() });
  }

  /* The pages build their carousels through the design runtime, so wait for
     the DOM to stop changing before taking the text census. */
  function whenSettled(done) {
    var last = Date.now();
    var obs = new MutationObserver(function () { last = Date.now(); });
    obs.observe(document.documentElement, { childList: true, subtree: true });
    var started = Date.now();
    (function poll() {
      if (Date.now() - last > 400 || Date.now() - started > 8000) {
        obs.disconnect();
        done();
      } else setTimeout(poll, 120);
    })();
  }

  if (document.readyState === "complete") whenSettled(boot);
  else window.addEventListener("load", function () { whenSettled(boot); });
})();
