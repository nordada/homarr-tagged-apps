# Widget reference

Groups the apps you already have in Homarr by keywords you write in each app's
**Description** field, and pings each one for a live status dot and latency.

Nothing in the definition references a specific app, so it is portable: install
it anywhere, tag some apps, and it works.

```
      UTILITIES
 ┌──────────────────────────┐
 │ 🗄  ArchiveBox            │
 │    200  6 ms             │
 ├──────────────────────────┤
 │ 📕  Calibre              │
 │    401  12 ms            │
 └──────────────────────────┘
      ARRS
 ┌──────────────────────────┐
 │ 🐰  Autobrrr             │
 │    DOWN                  │   ← red border, unreachable
 └──────────────────────────┘
```

## Tagging apps

An app joins a group when its description contains that keyword. A plain comma
list, no numbering:

```
audio
arrs,media
```

An app can carry several keywords and appear in several copies. Apps with an
empty description never appear.

Leave the `categories` option blank and the widget lists every keyword it can
see, with counts, ready to copy. If nothing is tagged yet it explains how to
start instead. Both of those states carry a link back to this documentation,
and both stop rendering the moment `categories` is set, so a configured board
never shows either.

A link cannot go in an option's description instead: Homarr passes every
description through as an escaped JSX child, so markdown and HTML render
literally. `Anchor` inside the template is the only way to get a clickable
one.

## Category headings

Three things control the heading above each group.

**Rename a heading** by writing `keyword=Heading` in the categories option. The
part before the `=` is what gets matched against app descriptions, the part
after is what gets displayed:

```
public=Alpha, admin=Bravo, system=Charlie
```

Apps still carry `public`, `admin` and `system` in their descriptions; only the
headings change. This works per category, so a widget showing several groups
renames each one independently, and an entry with no `=` keeps using the
keyword as its own heading. Every existing board is therefore unaffected.

Case and spaces are preserved in the label but stripped from the match key, so
`home lab=Home Lab` matches the keyword `homelab` and displays `Home Lab`.
Spaces around an entry are dropped, so `public = Alpha` and `public=Alpha` are
the same thing. An entry written `public=` with nothing after it falls back to
the keyword rather than showing a blank heading.

**Hide the headings entirely** with *Show category headings*. The gap between
groups is kept, so categories stay visually separated instead of running into
one list. Worth it when a widget shows a single category and the heading just
repeats the tile title.

**Stop the capitalisation** with *Uppercase the headings*. Headings render in
capitals by default, which is fine for a raw keyword and less so once you are
naming groups yourself: `system=Charlie` shows as CHARLIE with it on, Charlie
with it off. Left on by default so existing boards look unchanged.

### Applying these to a widget already on a board

Re-paste `template.jsx` and `options.json` in the workbench. The two new option
keys arrive with their defaults on every placed copy, so nothing needs
reconfiguring; **adding** an option key is safe, it is removing or renaming one
that orphans stored values. See the root README.

## Options

Ordered the way the form presents them: each toggle, then only the settings it
governs.

| Option | Type | Default | What it does |
| --- | --- | --- | --- |
| `categories` | text | blank | Keywords to show, comma separated, in display order. Write `keyword=Heading` to relabel one. Blank shows the category picker. |
| **`showCategoryHeader`** | switch | on | **Print the category name above each group.** Off keeps the gap between groups so they stay separated. |
| `headerUppercase` | switch | on | Capitalise the headings. Off keeps the case you typed. |
| **`showStatus`** | switch | on | **Ping the apps and show dots.** Off makes this a plain link list at no request cost. |
| `statusLimit` | text | 24 | How many apps get pinged, counting from the top. |
| `highlightDown` | switch | on | Red border and fill on an unreachable card. |
| **`showCodes`** | switch | on | **Print the HTTP status under each name.** |
| `codePrefix` | text | `HTTP ` | Text before the code. Clear it for just the number. |
| `codeColor` | text | `gray.6` | Colour for OK codes: 2xx, 3xx, 401, 403. |
| `codeWarnColor` | text | `orange.6` | Colour for other 4xx/5xx. |
| `codeErrColor` | text | `red.6` | Colour for anything outside 1xx-5xx. |
| **`showLatency`** | switch | on | **Print how long the ping took.** |
| `latencyColor` | text | `gray.6` | Colour below the warning threshold. |
| `latencyWarnMs` | text | `300` | Switch to the warning colour at or above this. `0` disables. |
| `latencyWarnColor` | text | `blue.4` | Used at or above the warning threshold. |
| `latencyBadMs` | text | `1000` | Switch to the bad colour at or above this. `0` disables. |
| `latencyBadColor` | text | `yellow.6` | Used at or above the bad threshold. |
| `statusAlignRight` | switch | off | Push the code and latency to the right edge. They move together. |
| `hoverUnderline` | switch | on | Underline the name on hover. |
| `scrollWhenTall` | switch | on | Scrollbar when the list is taller than the tile. |

Everything from `statusLimit` down to `statusAlignRight` needs `showStatus` on, and
`headerUppercase` only does anything while `showCategoryHeader` is on.

### Colouring by value

Both the status code and the latency colour themselves by what they say, on by
default.

Codes render as `HTTP 200` by default. A bare number sitting beside a latency
reading is ambiguous, and HTTP has no unit marking a number as a status code;
the standardised pairing is the reason phrase (`200 OK`), which does not fit a
narrow card once you reach `500 Internal Server Error`. Clear `codePrefix` for
the compact look.

**Status codes** use the same three bands as the dot: OK is 2xx, 3xx and
401/403 (`gray.6`); questionable is other 4xx and 5xx (`orange.6`); error is
anything outside 1xx-5xx (`red.6`). `DOWN` ignores all of it and is always red.

**Latency** bands at 300 ms and 1000 ms:

| Reading | Colour |
| --- | --- |
| under 300 ms | `gray.6` |
| 300 ms and above | `blue.4` |
| 1000 ms and above | `yellow.6` |

Enter `0` in a threshold to turn that band off. Blank restores the default
rather than disabling, since a blank field reads as "unset", not "none".

Thresholds are per copy, which matters more than it sounds. An app pinged over
the LAN and one pinged through a cloud service like Unraid Connect have
completely different normal ranges, so a copy full of Connect-backed servers
wants much higher thresholds than a copy of local services.

## Dot colours

| Colour | Meaning |
| --- | --- |
| green | 2xx, 3xx, or 401/403. Reachable, may want auth. |
| orange | Other 4xx/5xx. Answering, but unhappy. |
| red + `DOWN` | No response at all. |
| grey | Not checked: past `statusLimit`, or past the 24th app. |

401 and 403 are green on purpose: the service answered, which for a down
detector is "up".

## Editing

`template.jsx` is **generated**. Edit `build-template.py` and re-run it:

```bash
python3 build-template.py
```

Hand edits to the `.jsx` are overwritten. The builder exists because the
template must satisfy structural rules that are easy to break by hand; see the
sandbox notes in the [README](README.md).

It also checks three things that otherwise fail late and quietly, and exits
non-zero on any of them:

- bracket balance across the whole template
- that `SubFetch` is still on one unbroken line, since splitting it renders
  nothing at all
- that every option's `description` is within 512 characters and `label` within
  128, naming the offending option

That last one matters because the workbench only rejects an over-long
description **on save**, after you have pasted, and the error does not say
which option is at fault.

## How the ping works

A custom widget request is a fixed string, and only `SubFetch` can feed it
values from the template. So `requests.json` declares `widget.app.ping` **24
times**, and the template fills the slots with the ids of the apps that copy is
showing, padding spare slots with a repeat of the first app.

Every card mounts its own `SubFetch` and sends the *same* full id list, then
reads its own slot. That looks wasteful and is deliberate: a board caps at
roughly 8 concurrent requests, so one request per card would cap the widget at 8
dots. Sending the full list means those 8 requests each carry all 24 results,
and identical params let the 60 second cache collapse them.

Responses come back `207`. Slots you filled succeed, padding repeats succeed,
and slots beyond your app count report an error the template reads as grey.

## FAQ

**I retagged an app and the widget still shows the old category.**
The `apps` request is cached for 60 seconds. Reload the board to see it now.
Both the grouping and the category picker read the same cached response, so they
go stale together.

**One copy picked up the change and another did not.**
Each copy caches from whenever it last fetched, so they sit at different points
in their cycle. The other catches up within its window.

**A card says DOWN but the site loads fine in my browser.**
The ping runs server-side from the Homarr container: no cookies, no browser
headers, different network path. Cloudflare in particular often refuses it.
Check the app's `pingUrl` is reachable from the container before assuming the
service is down.

**The picker lists the categories alphabetically, until there are more than 60
of them**, at which point it keeps board order instead. Past 60 the panel is
telling you the descriptions are prose rather than keywords, and sorting that
many is what pushes the widget over its budget.

**The picker lists categories I have already used elsewhere.**
A widget can only see the app list, never the board or other widgets, so it
cannot know which are already placed.

**Hovering does nothing but underline.**
That is the only hover affordance the sandbox allows. See the repo README.

**I cannot select the category list to copy it.**
Works in view mode, not while editing, where the drag handler takes the gesture.

## Testing the dot colours

`../tools/pingtest-apps.py` creates four throwaway apps tagged `pingtest`, one
per colour, using local targets so they resolve fast:

```bash
python3 ../tools/pingtest-apps.py            # create
python3 ../tools/pingtest-apps.py --delete   # remove
```

Set `categories` to `pingtest` and `statusLimit` to `3`.
