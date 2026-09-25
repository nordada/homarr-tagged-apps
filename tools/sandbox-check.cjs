// Renders template.jsx through Homarr's interpreter once per case below and
// reports the rendered text. Called by sandbox-check.sh, which builds the
// bundle for a given Homarr ref.
//
// A case that renders nothing is not necessarily healthy: silent failures are
// how most sandbox violations show up. Read the text, do not just count OKs.
//
// Only headings and the two empty states show up as text. The app cards live
// inside a SubFetch children function, which the component stubs cannot call,
// so this checks the grouping and the option handling, not the card layout.
const React = require("react");
const fs = require("fs");

const [bundlePath, templatePath, optionsPath] = process.argv.slice(2);
const { renderSafeJsx, createCustomJsxBindings } = require(bundlePath);
const template = fs.readFileSync(templatePath, "utf8");
const optionDefs = JSON.parse(fs.readFileSync(optionsPath, "utf8"));
const defaults = Object.fromEntries(Object.entries(optionDefs).map(([key, option]) => [key, option.default]));

// Every component resolves, so a case fails on the expression, not on a name.
const components = new Proxy(
  {},
  {
    get: (_target, name) => {
      if (typeof name !== "string") return undefined;
      const Stub = (props) =>
        React.createElement("div", { "data-component": name }, typeof props.children === "function" ? null : props.children);
      Stub.displayName = name;
      return Stub;
    },
    has: () => true,
  },
);

const apps = [
  { id: "a1", name: "Sonarr", href: "http://host/1", description: "media, admin", iconUrl: "/icon/1.png" },
  { id: "a2", name: "Grafana", href: "http://host/2", description: "system", iconUrl: "/icon/2.png" },
  { id: "a3", name: "Plex", href: "http://host/3", description: "media", iconUrl: "/icon/3.png" },
  { id: "a4", name: "Untagged", href: "http://host/4", description: "", iconUrl: "" },
];

const cases = [
  ["no categories, apps tagged", {}, apps],
  ["no categories, nothing tagged", {}, []],
  ["plain keywords", { categories: "media, system" }, apps],
  ["renamed headings", { categories: "media=Alpha, system=Bravo" }, apps],
  ["one renamed, one not", { categories: "media, system=Bravo" }, apps],
  ["spaces around the entry", { categories: " media = My Media " }, apps],
  ["keyword with a trailing =", { categories: "media=" }, apps],
  ["headings hidden", { categories: "media, system", showCategoryHeader: false }, apps],
  ["headings not uppercased", { categories: "media", headerUppercase: false }, apps],
  ["keyword that matches nothing", { categories: "nosuchtag" }, apps],
];

let failed = 0;
for (const [label, options, data] of cases) {
  try {
    const result = renderSafeJsx({
      template,
      components,
      bindings: { ...createCustomJsxBindings({ apps: data }), options: { ...defaults, ...options }, status: {}, inputs: {} },
    });
    const text = [];
    const walk = (node) => {
      if (node == null || typeof node === "boolean" || typeof node === "function") return;
      if (typeof node === "string" || typeof node === "number") return void text.push(String(node));
      if (Array.isArray(node)) return void node.forEach(walk);
      if (node.props) walk(node.props.children);
    };
    walk(result.node);
    const warnings = (result.warnings ?? []).length;
    const rendered = text.join(" ").replace(/\s+/g, " ").trim();
    console.log(
      `  ok    ${label.padEnd(30)} ${warnings ? `warnings=${warnings} ` : ""}${rendered.slice(0, 70) || "(rendered nothing)"}`,
    );
  } catch (error) {
    failed += 1;
    console.log(`  FAIL  ${label.padEnd(30)} ${error.message}`);
  }
}
process.exit(failed === 0 ? 0 : 1);
