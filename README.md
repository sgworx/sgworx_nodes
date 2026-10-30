# sgworx_nodes

Small helper nodes for ComfyUI workflows. They keep a workflow simple for artists: one place to choose audio, one box that saves every result, clean video previews, and boxes that switch themselves off when they aren't needed.

## Nodes

| Node | What it does |
|---|---|
| **Audio Option** | A dropdown: `Default` / `No Audio` / `Custom`. Feeds the workflow's audio switches. |
| **Save All** | One box that saves every result. Each field is the folder for one file (low-res video, high-res video, prompt text, generated song, soundtrack). A plain name such as `video` saves inside ComfyUI's `output` folder; a full path such as `C:/Users/you/Desktop/Kit` saves anywhere. Inputs that weren't produced this run (for example no 1080p video in a quick draft) are skipped. |
| **Preview Video** | Shows a video inside its box. It writes a temporary copy only, nothing permanent. |

## Front-end helpers

- **Auto bypass** - a node whose `properties.autoBypass` rule matches turns purple (bypassed) automatically, so unused parts of a workflow never run. Example rule:
  `{"any": [{"source": 146, "eq": true}]}` = bypass while node 146's first widget is `true`. `ne` means "not equal".
- **Header colours** - colours the title bar of named groups (`extra.sgworx_header_colours`) and draws row-label arrows (`extra.sgworx_label_arrows`).

## Install

**ComfyUI Manager:** *Install via Git URL* and paste `https://github.com/sgworx/sgworx_nodes`.

**Manually:**
```
cd ComfyUI/custom_nodes
git clone https://github.com/sgworx/sgworx_nodes sgworx_nodes
```
Restart ComfyUI. No extra Python packages are needed.

Needs ComfyUI 0.39 or newer.

## Licence

MIT - see `LICENSE`.
