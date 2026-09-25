# homarr-tagged-apps

A custom widget for [Homarr](https://homarr.dev) 2.x that groups the apps you
already have by keywords you write in each app's **Description** field, with
live status dots, HTTP status codes and ping latency.

```
      UTILITIES
 ┌──────────────────────────┐
 │ 🗄  ArchiveBox            │
 │    HTTP 200  6 ms        │
 ├──────────────────────────┤
 │ 📕  Calibre              │
 │    HTTP 401  12 ms       │
 └──────────────────────────┘
      ARRS
 ┌──────────────────────────┐
 │ 🐰  Autobrrr             │
 │    DOWN                  │   ← red border, unreachable
 └──────────────────────────┘
```

Nothing in the definition names a specific app, so it is portable: install it,
tag some apps, and it works. Homarr has no dense multi-app widget; Bookmarks is
compact but carries no status.

See [WIDGET.md](WIDGET.md) for tagging, every option, and how the ping works.

## Installing

Homarr keeps widget definitions in its own database, so the files here are the
editable originals and pasting them in is what deploys them.

**Management → Custom Widgets.** For each file, paste into the matching field:

| File | Field |
| --- | --- |
| `template.jsx` | Template |
| `requests.json` | Requests (JSON) |
| `options.json` | Options (JSON) |
| `description.txt` | Description |

**Paste the template before the requests.** The validator checks the saved
template against the request config, so changing requests first can fail
against a template that has not caught up.

## Editing

`template.jsx` is **generated**. Edit `build-template.py` and re-run it:

```bash
python3 build-template.py
```

Hand edits to the `.jsx` are overwritten. The builder exists because the
template has to satisfy structural rules that are easy to break by hand, and it
checks three of them, exiting non-zero on any: bracket balance, that `SubFetch`
is still on one unbroken line, and that every option's `description` is within
512 characters and `label` within 128.

That last check matters because the workbench only rejects an over-long
description **on save**, after you have pasted, and the error does not name the
offending option.

## The sandbox

Templates run in a restricted runtime: a whitelist of Mantine components, no
user-defined functions, and resource ceilings. Most violations **render nothing
at all**, with no error, no fallback and no console message, so the only way to
find them is to bisect the template. These are the ones found the hard way.

### Silent failures

- **A `SubFetch` element must be written on one line.** Split its attributes
  across lines and it renders nothing, taking the surrounding markup with it.
  This is why `build-template.py` emits that whole element, attributes and
  children included, as one unbroken line. If you reformat a template for
  readability, this is the thing not to reflow.
- **`SubFetch` must sit inside a list, one instance per item.** Wrapping a whole
  list in a single `SubFetch` renders nothing.
- **Its children must not nest arrays more than two deep.** Three-deep renders
  nothing.
- **Unlisted props kill the element.** Confirmed rejected: `lh`, and `ta` with a
  dynamic value. Use `style={{lineHeight}}` and `style={{textAlign}}`.
- **Blocked props:** `on*`, `className`, `classNames`, `component`, `children`.
  There is no way to attach a hover effect or a click handler.
- **`Tooltip` is stripped**, silently, while its child still renders.

### Rejected outright

Unlike the silent failures above, these raise a visible `RUNTIME_RENDER_ERROR`
on the tile.

- **`.trim()` is not allowed.** Confirmed 2026-09-25, as
  `Calling method 'trim' is not allowed`, on an expression that had shipped and
  looked fine in review. Trim with `.split(" ").filter((s)=>s!=="").join(" ")`
  instead, which also collapses internal runs of spaces. The string methods this
  widget does use without complaint are `split`, `join`, `toLowerCase`,
  `includes` and `concat` via `+`.
- **A blocked call is found at call time, not at paste time.** The workbench
  saved the template without complaint. Nothing flags the expression until a
  tile renders and reaches it, so a blocked method sitting on any branch ships
  looking healthy. Place a copy with every option blank and a copy fully
  configured before calling a template good.

### Things that are true but not obvious

- **`SubFetch` results never appear in `data` or `status`.** They reach only the
  children function. An absent `status.<id>` is not evidence the request failed.
  The **request log** in the diagnostic pane is the reliable signal, and reading
  it earlier would have saved hours.
- **`trigger="auto"` fires on mount. `trigger="visible"` does not stagger
  anything.**
- **A board caps at roughly 8 concurrent widget requests.**
- **A refused connection returns a *successful* slot whose `statusCode` is
  absent**, not an errored slot. Treat anything outside 100-599 as down.
- **Boards set `user-select: none`** so tiles can be dragged, which kills text
  selection. An inline `style={{userSelect:'text'}}` overrides it, and works in
  view mode only.
- **Removing an option key orphans the stored value** on every already-placed
  copy, which surfaces as a validation error on the board. Changing a key's
  *type* is safe; removing or renaming it is not.

### Resource limits

| Limit | Value |
| --- | --- |
| Operations | 25,000 |
| Collection operations | 4,000 |
| AST depth | 64 |
| Template length | 50,000 |
| Option `description` | 512 |
| Option `label` | 128 |

Also: no regex with `+`, `*` or `{n,}`; callbacks only as direct arguments to
safe collection methods; `.sort()` requires a comparator.

**The 512 and 128 are per option**, not widget-wide, from
`packages/custom-widgets/src/core/options-schema.ts`. This row previously read
"Description / name 512 / 128", which was easy to read as the widget's own name
and description, and a `categories` description written at 517 characters got
through review on that basis.

The workbench rejects an over-long description **on save**, after you have
already pasted, and the error does not name the offending option. So
`tagged-apps/build-template.py` checks `options.json` against both limits and
exits non-zero, naming the option and its length. Worth copying into any new
widget's builder: it turns a confusing save failure into a build failure you
can read.

**The two that matter pull against each other.** Binding a value with
`[x].map((y)=>…)` costs about four AST levels on everything beneath it, so
inlining the value instead saves depth, but then it recomputes per item and
costs collection operations. The way out is to put the binding somewhere the
deep path does not traverse, computing it inside a value expression and
unwrapping with `[0]`. `tagged-apps/build-template.py` does this for both the
keyword list and the ping params.

Long `a+b+c+d` chains nest one level per `+`; `[a,b,c,d].join("")` is flat.
