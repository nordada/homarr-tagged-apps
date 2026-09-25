#!/usr/bin/env python3
"""Emit template.jsx. Edit here, not in the .jsx, which is overwritten.

Structural rules this file exists to satisfy (see ../README.md):
  * a SubFetch element must be emitted on ONE line
  * its children must not nest arrays more than two deep
  * AST depth ceiling is 64 and collection ops 4000, and they pull against
    each other: binding a value costs depth, inlining it costs iterations.
    Values used on the deep card path are therefore computed inside the list
    expression and unwrapped with [0].
"""
import pathlib

N = 24
IDX = '"' + ",".join(str(i) for i in range(N)) + '".split(",")'

# Each entry is "keyword" or "keyword=Label". Split on "," first and "=" second,
# so the label keeps its case and spaces while the match key stays normalised.
#
# The label falls back with || rather than a != null test. Older sandbox builds
# implement == and != as String(left) === String(right), so undefined != null is
# true and an entry with no "=" takes the undefined branch, which then raises
# RUNTIME_RENDER_ERROR "Calling method 'trim' is not allowed" on undefined.
# Only === and !== behave like JavaScript in every build. See ../README.md.
# An entry with no "=" yields label == keyword, which is why every existing
# board is unaffected.
#
# Pairs rather than two parallel arrays: filtering an empty entry out of two
# arrays independently would slide their indices apart, and _gi indexes both.
K = ('(options.categories||"").split(",").map((e)=>e.split("="))'
     '.map((p)=>[(p[0]||"").toLowerCase().split(" ").join(""),'
     '(p[1]||p[0]||"").trim()])'
     '.filter((p)=>p[0]!=="")')

PIPELINE = ('data.apps.filter((a)=>(a.description||"")!=="")'
            '.map((a)=>[(a.description||"").toLowerCase().split(" ").join("")]'
            '.map((d)=>({...a,_d:d,_gi:keys.length===0?0:'
            'keys.findIndex((k)=>(","+d+",").includes(","+k[0]+","))}))[0])'
            '.filter((a)=>a._gi>=0)'
            '.map((a)=>({...a,_g:keys.length===0?a._d.split(",")[0]:keys[a._gi][1]}))'
            '.sort((x,y)=>x._gi!==y._gi?x._gi-y._gi:((x._g||"")<(y._g||"")?-1:'
            '((x._g||"")>(y._g||"")?1:((x.name||"")<(y.name||"")?-1:((x.name||"")>(y.name||"")?1:0)))))')

# identical for every card, so build once and hang it on each app as _q
QEXPR = ('[\'{\',' + IDX +
         '.map((s,n)=>[\'"\',n,\'":{"json":{"id":"\',(arr[n]||arr[0]).id,\'"}}\'].join(""))'
         '.join(\',\'),\'}\'].join("")')

LIST = ('[[' + K + '].map((keys)=>[' + PIPELINE + '].map((arr)=>['
        + QEXPR + '].map((q)=>arr.map((a)=>({...a,_q:q})))[0])[0])[0]]')

# One binding holding [code, latencyMs]. code: a real 1xx-5xx, or -1 for down,
# or null for a slot that was never filled. ms: -1 when unknown. Binding the
# pair keeps the deep leaves at v[0]/v[1] instead of re-walking the response.
CODE = 'v[0]'
MS   = 'v[1]'
BIND = ('[[r?((r.result&&r.result.data&&r.result.data.json'
        '&&Number(r.result.data.json.statusCode)>=100'
        '&&Number(r.result.data.json.statusCode)<600)'
        '?Number(r.result.data.json.statusCode):-1):null,'
        'r&&r.result&&r.result.data&&r.result.data.json'
        '&&r.result.data.json.durationMs!==undefined'
        '&&r.result.data.json.durationMs!==null'
        '?Number(r.result.data.json.durationMs):-1]]')

OK   = f'(({CODE}>=200&&{CODE}<400)||{CODE}===401||{CODE}===403)'
WARN = f'({CODE}>=400&&{CODE}<600)'

DOT = ('<Indicator size={8} offset={3} position="bottom-end" withBorder '
       f'color={{{CODE}===null?"gray.6":({CODE}===-1?"red":({OK}?"green":({WARN}?"orange":"red")))}}>'
       '<Image src={app.iconUrl} alt={app.name} w={24} h={24} fit="contain"/></Indicator>')

PLAIN_ICON = '<Image src={app.iconUrl} alt={app.name} w={24} h={24} fit="contain"/>'

# Blank warn/err colours fall back to codeColor, so the default is one colour
# for everything and banding is opt-in.
CODE_C = (f'{CODE}===-1?"red.5":({OK}?(options.codeColor||"gray.6")'
          f':({WARN}?(options.codeWarnColor||"orange.6")'
          f':(options.codeErrColor||"red.6")))')

# Thresholds are blank by default, which disables banding entirely.
LAT_C = (f'({MS}>=Number(options.latencyBadMs||1000)&&Number(options.latencyBadMs||1000)>0)'
         f'?(options.latencyBadColor||"yellow.6")'
         f':(({MS}>=Number(options.latencyWarnMs||300)&&Number(options.latencyWarnMs||300)>0)'
         f'?(options.latencyWarnColor||"blue.4")'
         f':(options.latencyColor||"gray.6"))')

CODE_LINE = ('<Group gap={5} wrap="nowrap" '
             'justify={options.statusAlignRight?"flex-end":"flex-start"}>'
             f'{{options.showCodes===false||{CODE}===null?null:'
             f'(<Text size="9px" fw={{{CODE}===-1?700:400}} c={{{CODE_C}}}>'
             f'{{{CODE}===-1?"DOWN":[options.codePrefix===undefined||options.codePrefix===null?"HTTP ":options.codePrefix,{CODE}].join("")}}</Text>)}}'
             f'{{(options.showLatency!==false&&{CODE}>0&&{MS}>=0)'
             f'?(<Text size="9px" c={{{LAT_C}}}>'
             f'{{[String({MS}).split(".")[0]," ms"].join("")}}</Text>):null}}'
             '</Group>')

NAME = '<Text fw={700} size="xs" lineClamp={1}>{app.name}</Text>'


def card(dot):
    paper = ('<Paper withBorder radius={6} p="xs" '
             f'bg={{options.highlightDown&&{CODE}===-1?"rgba(224,49,49,0.10)":"transparent"}} '
             'style={{borderColor:options.highlightDown&&'
             f'{CODE}===-1?"var(--mantine-color-red-6)":undefined}}}}>'
             ) if dot else '<Paper withBorder radius={6} p="xs">'
    body = (('<Stack gap={2} style={{minWidth:0,flex:1}}>' + NAME + CODE_LINE + '</Stack>')
            if dot else NAME)
    return ('<Anchor href={app.href} target="_blank" '
            'underline={options.hoverUnderline===false?"never":"hover"} c="inherit">' + paper +
            '<Group wrap="nowrap" gap="xs" justify="start">' + (DOT if dot else PLAIN_ICON) +
            body + '</Group></Paper></Anchor>')


# The group gap is kept when the header is hidden, otherwise categories run
# together into one undifferentiated list. tt is an option because a custom
# label typed as "Alpha" would otherwise still render as ALPHA.
HEAD = ('{(options.showCategoryHeader===false)?((i===0||list[i-1]._gi!==app._gi)&&i!==0'
        '?(<Space h="10px"/>):null)'
        ':((i===0||list[i-1]._gi!==app._gi)?(<Text fw={700} '
        'tt={options.headerUppercase===false?"none":"uppercase"} c="dimmed" fz="xs" '
        'mt={i===0?0:"10px"} mb="2px" ta="center">{app._g}</Text>):null)}')

SKEL = '<Paper withBorder radius={6} p="xs"><Skeleton height={24} radius="sm"/></Paper>'
SEL  = "userSelect:'text',WebkitUserSelect:'text'"
UNIQ = 'all.filter((v,i,arr)=>i===0||arr[i-1]!==v)'

ALL = ('[data.apps.filter((a)=>(a.description||"")!=="")'
       '.map((a)=>(a.description||"").toLowerCase().split(" ").join(""))'
       '.join(",").split(",").filter((k)=>k!=="")'
       '.sort((a,b)=>a<b?-1:(a>b?1:0))]')

# Shown only in the two unconfigured states below, which stop rendering the
# moment `categories` is set. So a working board never carries this, and no
# option is needed to switch it off.
#
# A link cannot go in an option description: every Homarr render path passes
# descriptions as an escaped JSX child, so markdown and HTML render literally.
# Anchor inside the template is the only way to get a clickable one.
DOCS_URL = "https://github.com/nordada/homarr-tagged-apps"
DOCS = ('<Anchor href="' + DOCS_URL + '" target="_blank" size="xs" ta="center">'
        'Options and setup guide</Anchor>')

EMPTY = ('<Stack gap={8}>'
         '<Text fw={700} fz="sm" tt="uppercase" ta="center">No categories yet</Text>'
         '<Text size="sm" c="dimmed" ta="center" style={{lineHeight:1.5}}>'
         'This widget groups your apps by keywords you write in the Description '
         'field of each app. In Homarr go to Manage, then Apps, edit an app, and set '
         'its description to a keyword such as media or servers. Separate several '
         'with commas.</Text>'
         '<Text size="xs" c="dimmed" ta="center" style={{lineHeight:1.5}}>'
         'Apps with an empty description never appear here. Once you have tagged a '
         'few, this panel lists them for you.</Text>'
         + DOCS +
         '</Stack>')

FOUND = ('<Stack gap={10}>'
         '<Text fw={700} fz="sm" tt="uppercase" ta="center">Available categories</Text>'
         '<Text size="sm" c="dimmed" ta="center" style={{lineHeight:1.5}}>'
         'Copy the ones you want into the categories option, separated by commas, '
         'in the order you want the groups stacked.</Text>'
         '<Group gap={6} justify="center">{' + UNIQ + '.map((k)=>('
         '<Paper key={k} withBorder radius={999} style={{padding:\'3px 10px\',' + SEL + '}}>'
         '<Group gap={6} wrap="nowrap">'
         '<Text size="sm" fw={600}>{k}</Text>'
         '<Text size="xs" c="dimmed">{all.filter((x)=>x===k).length}</Text>'
         '</Group></Paper>))}</Group>'
         '<Text size="xs" c="dimmed" ta="center">All of them, ready to paste:</Text>'
         '<Paper withBorder radius={6} style={{padding:\'6px 10px\',' + SEL + '}}>'
         '<Text size="xs" ta="center" style={{lineHeight:1.6,wordBreak:\'break-word\'}}>{'
         + UNIQ + '.join(", ")}</Text></Paper>'
         '<Text size="xs" c="dimmed" ta="center" style={{lineHeight:1.5}}>'
         'The number is how many apps carry that category. A widget cannot see other '
         'widgets, so every category is listed, not just unused ones.</Text>'
         + DOCS +
         '</Stack>')

CATALOGUE = ('<Stack gap={10} p="xs" style={{' + SEL + ',cursor:\'text\'}}>'
             '{' + ALL + '.map((all)=>all.length===0?(' + EMPTY + '):(' + FOUND + '))}'
             '</Stack>')

SUB = ('{options.showStatus&&i<(Number(options.statusLimit)||24)'
       '?(<SubFetch key={app.id} requestId="pings" params={{q:app._q}} trigger="auto" '
       'triggerAriaLabel={"Check "+app.name} loadingLabel="Checking" '
       'fallback={' + SKEL + '} triggerContent={' + card(False) + '}>'
       '{(res)=>[(res||[])[i]].map((r)=>' + BIND + '.map((v)=>(' + card(True) + ')))}'
       '</SubFetch>)'
       ':' + card(False) + '}')

tpl = (
'<Stack gap={8} px="sm" pb="sm" style={{width:\'100%\',maxHeight:\'100%\','
"boxSizing:'border-box',paddingTop:'26px',"
"overflowY:options.scrollWhenTall===false?'hidden':'auto',"
"overflowX:'hidden',scrollbarWidth:'thin'}}>\n"
'{(status.apps?.error||status.apps?.loading)\n'
'  ? (status.apps?.error ? (<Alert color="red">{status.apps.error}</Alert>) : (<Skeleton height={160} radius="md"/>))\n'
'  : ' + K + '.length===0 ? (' + CATALOGUE + ')\n'
'  : ' + LIST + '.map((list)=>(\n'
'      list.length===0\n'
'      ? (<Text size="xs" c="dimmed" ta="center" p="md">No apps matched.</Text>)\n'
'      : list.map((app,i)=>(\n'
'          <Stack key={app.id} gap={2}>\n'
'            ' + HEAD + '\n'
'            ' + SUB + '\n'
'          </Stack>\n'
'        ))\n'
'    ))\n'
'}\n'
'</Stack>\n')

pathlib.Path(__file__).with_name("template.jsx").write_text(tpl)

d = {'(': 0, '{': 0, '[': 0}
pair = {')': '(', '}': '{', ']': '['}
instr = False
q = ''
for c in tpl:
    if instr:
        if c == q:
            instr = False
        continue
    if c in '"\'':
        instr, q = True, c
        continue
    if c in d:
        d[c] += 1
    elif c in pair:
        d[pair[c]] -= 1
sub = [l for l in tpl.split("\n") if "<SubFetch" in l]
print(f"template.jsx: {len(tpl)} chars  balance: {d} -> "
      + ("OK" if all(v == 0 for v in d.values()) else "BAD"))
print("SubFetch on one line:", len(sub) == 1 and "</SubFetch>" in sub[0])

# Schema limits on each option, from packages/custom-widgets/src/core/
# options-schema.ts: description max 512, label max 128. These are per option
# and are separate from the widget-level name and description limits.
#
# Checked here because the workbench rejects an over-long description on save,
# after the paste, and the message does not name the offending option. A
# categories description written at 517 characters got through review once.
import json as _json
import sys as _sys
from pathlib import Path as _Path

LIMITS = {"description": 512, "label": 128}
_opts_path = _Path(__file__).with_name("options.json")
if _opts_path.exists():
    _opts = _json.loads(_opts_path.read_text())
    _bad = [
        (name, field, len(value), limit)
        for name, opt in _opts.items()
        for field, limit in LIMITS.items()
        if (value := opt.get(field, "")) and len(value) > limit
    ]
    _longest = max(len(o.get("description", "")) for o in _opts.values())
    if _bad:
        for name, field, length, limit in _bad:
            print(f"options.json: {name}.{field} is {length} chars, limit {limit}",
                  file=_sys.stderr)
        _sys.exit(1)
    print(f"options.json: {len(_opts)} options within limits "
          f"(longest description {_longest}/512)")
