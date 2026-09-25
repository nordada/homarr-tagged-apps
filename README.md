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

## Checking a template before you paste it

`build-template.py` checks structure. It cannot tell you whether an expression
survives the interpreter, because that depends on the Homarr build. This does:

```bash
bash tools/sandbox-check.sh release/v2
bash tools/sandbox-check.sh 3aa14e22
```

Cases live in `sandbox-cases.json`. A case either names its apps or asks for a
generated instance (`"generate": {"count": 250, "tagsEach": 3}`), and the
generated ones are the point: four hand-written apps sit far inside every
budget, and a real board does not.

It fetches Homarr's `packages/custom-widgets` at that ref, bundles the real
interpreter and renders `template.jsx` through it once per case, with the
categories option blank, renamed, mixed and matching nothing. Any ref, branch or
commit that carries the package works.

Two refs rather than one, because the sandbox is not one fixed set of rules. The
equality failure below renders fine on current source and fails on the build it
was deployed to, and checking only the newer one would have said the template
was healthy.

`3aa14e22` is 2026-07-22, the first ref with the full component catalog, and it
still has the string-comparison equality that `47f6c1cc` fixed on 2026-09-24.
Anything released between those two dates behaves like it. Do not reach further
back than that for the old side: `83e3b22f` predates the catalog and silently
drops props that every shipped build accepts, `Anchor.href` among them, so it
reports failures that are not real.

Needs node, npx and network. Everything lands in `.sandbox-check/`, gitignored.

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

### Loose equality is not loose

`==` and `!=` are implemented as `String(left) === String(right)` in the build
this widget was first deployed against, so **`undefined != null` is true**. A
`value != null ? value : fallback` guard therefore takes the `value` branch when
the value is missing, and the next method call on it fails with a visible
`RUNTIME_RENDER_ERROR`: `Calling method 'trim' is not allowed`, naming whatever
method happened to be next. The message points at the method; the bug is the
comparison.

Newer builds special-case null on both sides and behave like JavaScript, which
is why this reproduces on one Homarr and not another.

- **Use `||` for a fallback, or `=== undefined` / `=== null` when an empty
  string has to survive.** `===` and `!==` are real strict equality in every
  build.
- **`.trim()` itself is allowed**, along with `split`, `join`, `toLowerCase`,
  `toUpperCase`, `includes`, `startsWith`, `endsWith`, `slice`, `substring`,
  `replace`, `replaceAll`, `indexOf`, `padStart`, `padEnd`, `charAt`, `repeat`,
  `match` and `search`. Every one of them raises that same
  `Calling method 'x' is not allowed` when the receiver is `undefined` or an
  array, so read the error as a wrong receiver before suspecting the method.
- **A blocked or misdirected call is found at call time, not at paste time.**
  The workbench saves the template without complaint. Place a copy with every
  option blank and a copy fully configured before calling a template good, or
  run `tools/sandbox-check.sh`, which renders the template against the real
  interpreter.

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

### Options

- **A `select` stores a string, even when the choice looks numeric.** The
  option validator requires a string for every control outside `number`,
  `slider`, `duration`, `switch`, `multiSelect` and `json`, and it runs against
  the declared `default` as well as stored values, so a numeric choice is
  refused on save with `options.<name>.default Expected text`. The settings
  form coerces a numeric choice back to a number, which is what makes this look
  supported. Declare the numbers as text and convert them in the template.
- **Removing an option key orphans the stored value** on every already-placed
  copy, which surfaces as a validation error on the board. Changing a key's
  *type* is safe; removing or renaming it is not.

### Budget, and what actually spends it

The collection budget is 4000 items and the operation budget 25,000, and a real
board reaches both. What they cost:

| Operation | Collection cost |
| --- | --- |
| `map`, `filter`, `flatMap`, `find`, `some`, `reduce` | 1 per item |
| `join`, `includes`, `indexOf` on an array | the whole array's length |
| `sort` | 1 per comparison, so n log n |
| `split` and `match` on a string | 1 per part produced |
| **every other string method** | **free** |

That last row is the lever. This widget's picker went from failing at 100 apps
to clearing 350 by moving work into strings:

- **`.replaceAll(" ", "")` in place of `.split(" ").join("")`.** The split/join
  pair charges twice per word, so one prose description cost six items instead
  of none. This ran once per app, in both the picker and the grouping.
- **Counting by splitting a delimited string** rather than
  `keys.filter((x) => x === k).length` per category, which was unique x total
  and on its own took a 189-app board down.
- **Deduplicating through a string accumulator** in one `reduce`, rather than
  `filter` plus `indexOf`, which is n squared because `indexOf` charges the
  array's length every call.
- **Sorting only when the list is short.** Sorting the full key list is n log n
  at the moment the budget is already tight.

Measured ceilings for this widget, from `tools/sandbox-check.sh`:

| Board | Apps before it fails |
| --- | --- |
| 1 keyword per app | 556 |
| 2 keywords per app | 353 |
| 3 keywords per app | 259 |
| every description a different sentence | 331 |
| **apps shown in one widget's categories** | **94** |

That last one is the operation budget rather than the collection budget, it is
about rendering cards rather than about the picker, and it has been there from
the start. One widget cannot show more than about 94 apps. Split them across
two widgets by category.

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
