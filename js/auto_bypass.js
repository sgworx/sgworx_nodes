import { app } from "../../scripts/app.js";

// properties.autoBypass on a node:
//   {"source": id, "when": value}                         bypass while source == value
//   {"any": [{"source": id, "eq": v}, {"source": id, "ne": v}]}  bypass while any condition holds
const BYPASS = 4, ALWAYS = 0;

function holds(graph, cond) {
    const value = graph.getNodeById(cond.source)?.widgets?.[0]?.value;
    if (value === undefined) return undefined;
    if ("ne" in cond) return value !== cond.ne;
    return value === ("eq" in cond ? cond.eq : cond.when);
}

function sync() {
    const graph = app.graph;
    if (!graph?._nodes) return;
    let changed = false;
    for (const node of graph._nodes) {
        const rule = node.properties?.autoBypass;
        if (!rule) continue;
        const results = (rule.any ?? [rule]).map((c) => holds(graph, c));
        if (results.includes(undefined)) continue;
        const mode = results.some(Boolean) ? BYPASS : ALWAYS;
        if (node.mode !== mode) {
            node.mode = mode;
            changed = true;
        }
    }
    if (changed) graph.setDirtyCanvas(true, true);
}

app.registerExtension({
    name: "sgworx.autoBypass",
    setup() {
        setInterval(sync, 300);
    },
});
