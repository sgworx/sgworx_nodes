import { app } from "../../scripts/app.js";

// Workflow extra settings read here:
//   sgworx_header_colours: {"SETTINGS": "#f2d36b", ...}  colours just the title bar of those sections
//   sgworx_label_arrows: ["START HERE", ...]  draws a right-pointing arrow under those sections' titles

function rectOf(g) {
    const b = g._bounding ?? g.boundingRect;
    if (b) return [b[0], b[1], b[2], b[3]];
    return [g.pos[0], g.pos[1], g.size[0], g.size[1]];
}

function drawHeaders(ctx, graph) {
    const colours = graph.extra?.sgworx_header_colours;
    if (!colours) return;
    for (const g of graph._groups ?? graph.groups ?? []) {
        const colour = colours[g.title];
        if (!colour) continue;
        const [x, y, w] = rectOf(g);
        const fs = g.font_size ?? 24;
        const th = g.titleHeight ?? Math.round(fs * 1.4);
        ctx.fillStyle = colour;
        ctx.beginPath();
        ctx.roundRect ? ctx.roundRect(x, y, w, th, [6, 6, 0, 0]) : ctx.rect(x, y, w, th);
        ctx.fill();
        ctx.fillStyle = "#1a1a1a";
        ctx.font = `${fs}px Arial`;
        ctx.textBaseline = "middle";
        ctx.textAlign = "left";
        ctx.fillText(g.title, x + 10, y + th / 2);
    }
}

function drawLabelArrows(ctx, graph) {
    // label boxes: title redrawn centred, small arrow centred underneath
    const names = graph.extra?.sgworx_label_arrows;
    if (!Array.isArray(names)) return;
    for (const g of graph._groups ?? graph.groups ?? []) {
        if (!names.includes(g.title)) continue;
        const [x, y, w, h] = rectOf(g);
        const fs = g.font_size ?? 24;
        const th = g.titleHeight ?? Math.round(fs * 1.4);
        ctx.fillStyle = g.color ?? "#1f1f1f";
        ctx.fillRect(x, y, w, th);                         // cover the left-aligned built-in title
        ctx.fillStyle = "#d0d0d0";
        ctx.font = `bold ${fs}px Arial`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(g.title, x + w / 2, y + th / 2);
        const cy = y + th + (h - th) / 2, len = w * 0.5, head = 22;
        const x0 = x + w / 2 - len / 2, x1 = x + w / 2 + len / 2;
        ctx.strokeStyle = "#d0d0d0";
        ctx.lineWidth = 6;
        ctx.lineCap = "round";
        ctx.beginPath(); ctx.moveTo(x0, cy); ctx.lineTo(x1 - head, cy); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(x1, cy); ctx.lineTo(x1 - head * 1.3, cy - head); ctx.lineTo(x1 - head * 1.3, cy + head); ctx.closePath(); ctx.fill();
    }
}

app.registerExtension({
    name: "sgworx.headerColours",
    setup() {
        const canvas = app.canvas;
        const orig = canvas.onDrawForeground;
        canvas.onDrawForeground = function (ctx, area) {
            orig?.apply(this, arguments);
            const graph = app.graph;
            if (!graph) return;
            ctx.save();
            drawHeaders(ctx, graph);
            drawLabelArrows(ctx, graph);
            ctx.restore();
        };
    },
});
