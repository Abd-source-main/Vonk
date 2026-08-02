# Vonk Elektra — first design

Two landing page variants sharing one interaction model.

- **`index-deconstruct.html`** — blueprint spec-sheet theme. Each service
  assembles on screen, pulls itself apart, and names its own parts.
- **`index-sections.html`** — light editorial theme. One full photo scene per
  service, sliding horizontally.

`second design` runs the same player on `index-deconstruct.html` with
regenerated clips (see **Note on the clips**).

`index-sections.html` needs nothing — it uses still images and works straight
away.

## Run this first (deconstruct page only)

```
powershell -ExecutionPolicy Bypass -File .\split-frames.ps1
```

Needs ffmpeg: `winget install Gyan.FFmpeg`, then open a **new** terminal.

It downloads the four clips into `assets\video` and splits each into **96 WebP
frames** in `assets\frames\mod-1..4`.

**Until you run it the page is on the slow path.** Look at the bottom right of
the deconstruction section — it reads either `SRC: FRAMES` or
`SRC: VIDEO — run split-frames` in orange.

Frames mode uses `fetch`, so it needs a real server. Opening the file straight
off disk falls back to video:

```
python -m http.server 8000
```

then visit http://localhost:8000/index-deconstruct.html

## The player — both pages

Both pages in this folder use the same interaction model, and it's worth
understanding once.

**`index-deconstruct.html`** — each service has two rest states:

1. **ASSEMBLED** — the drawing whole
2. **EXPLODED** — fully apart, parts named, copy in

**`index-sections.html`** — each of the four services *is* a rest state, and the
horizontal slide between two panels is the transition.

In both cases the transition is **not scrolled — it's played**. Once you commit,
wheel, touch and key input are swallowed (`preventDefault`) and the
deconstruction runs on its own clock for 1.5 seconds at a constant, watchable
speed. The page's scroll position is animated underneath it, so the scrollbar
travels and it still reads as scrolling — you just can't stall it, race it, or
stop halfway.

**Committing takes intent.** 90px of accumulated scroll in one direction, and it
resets if you pause for 400ms. A stray nudge does nothing at all.

**Leaving is always free.** Scroll up from the first rest state or down from the
last and the page behaves normally. Only the direction that would *enter* a
transition is gated. Scroll back the other way and it plays in reverse.

**Arriving catches you.** The gesture that carries you into a rest state does
not count as a request to move on. Momentum from the hero used to sail straight
through the first service before you'd seen it; now the page stops there and
waits. Moving on takes a *new* scroll — a gap of 280ms separates one gesture
from the next. The counter flicks when you're being held, so it reads as
deliberate rather than broken.

Every input is timestamped whether the section is on screen or not. Without
that, the first event after the section appears looks like a brand-new gesture
and arms it immediately — which was exactly the bug.

**Rest states chain.** From EXPLODED, scrolling on hops to the next service's
ASSEMBLED (a short 520ms travel, not a replayed deconstruction). Only the very
first and very last rest states let you scroll out of the section freely.

`prefers-reduced-motion` disables the whole mechanism — no input capture, no
playback; sections stack vertically as static drawings.

| constant | does |
|---|---|
| `PLAY_MS` | how long a transition takes (1500 deconstruct / 1000 sections) |
| `COMMIT_PX` | scroll needed to start one (90) |
| `ARM_GAP` | quiet time that separates one gesture from the next (280) |
| `RAMP` | ease at each end; middle is constant speed (0.14) |
| `A_T` / `B_T` | where the two rest states sit (deconstruct only, 0.16 / 0.84) |
| `SECTION_VH` / `PANEL_VH` | scroll length per service (170 / 110) |
| `FRAME_COUNT` | must match `$FRAMES` in split-frames.ps1 (96) |

## Note on the clips

First design uses the **original** clips, which ease in and out — they really do
sit still at the start and end of each one. So `dwell()` keeps an aggressive
trim here: the first 16% and last 14% of a clip are passed in a fraction of the
play, and the time is spent on the frames where parts are actually moving.

Second design regenerated the clips to separate continuously edge to edge, and
uses a near-linear trim instead. Same player, different source material — worth
comparing the two side by side.

## Why frames and not video

A browser cannot jump an MP4 to an arbitrary frame. It finds the nearest
keyframe and decodes forward to the one you asked for. During playback you ask
for a new frame ~60 times a second, so the decoder is constantly re-seeking and
throwing away work. That is the stutter.

A folder of images has no such problem: frame 87 is just `0087.webp`. Decode it
once, keep the bitmap, blit it.

## Before going live

1. **Wire up the form.** There's a `TODO` in the submit handler — POST to your
   backend or a form service.
2. **Verify the contact details.** Phone, email and address came from the public
   site; check them.
3. **Add real proof.** Nothing converts a local trades customer like reviews.
   A Google Reviews widget or two or three named testimonials between "About"
   and the contact form would do more for conversion than any animation.
4. **Serve the frames with long cache headers** —
   `Cache-Control: public, max-age=31536000, immutable`.

## SEO notes

- `Electrician` schema.org JSON-LD with `areaServed: Nijmegen` and a full
  service catalogue — this is what earns rich results for local trade searches.
- Title and meta description lead with **service + place**, which is how people
  actually search.
- Every service is real crawlable text, and the part labels are HTML rather than
  baked into the video — so they're readable by Google and by screen readers.

**The biggest remaining win is not on this page.** It's a Google Business Profile
with photos, service areas and reviews, plus one page per service+city. This page
is the conversion destination; those pages feed it traffic.

Also worth saying plainly: an English page will not rank for Dutch searches in
Nijmegen. If organic traffic is the goal, a Dutch version matters more than
almost anything else here.

## What's in this folder

| file | what it is |
|---|---|
| `index-deconstruct.html` | blueprint theme — each service assembles, then pulls apart |
| `index-sections.html` | light theme — one photo scene per service, panels slide horizontally |
| `split-frames.ps1` | downloads the clips and splits them into frames (deconstruct page only) |
| `assets/img/` | logos — dark (bone) pair for the blueprint page, light pair for the sections page |

**`prepare-assets.sh` can be deleted.** It belonged to the original
scroll-scrubbed-video approach and has been superseded by `split-frames.ps1`.
Nothing references it any more. I can't remove files from your disk — the
bridge only writes — so delete it yourself.

`assets/video/` is also empty; `split-frames.ps1` recreates it when it runs.
