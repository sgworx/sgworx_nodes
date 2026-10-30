"""sgworx_nodes - small helper nodes for ComfyUI workflows.
- js/auto_bypass.js: a node with properties.autoBypass is bypassed (purple) while its SETTINGS switch makes it unused.
- js/header_colours.js: coloured section titles + row-label arrows.
- Audio Option: plain dropdown (Default / No Audio / Custom).
- Save All: one box that saves every result, with an editable folder per file.
  A plain name (default "video", "audio", "prompt") is a folder inside ComfyUI's output; a full path saves anywhere.
  Inputs left empty (e.g. no 1080p video in Quick draft) are skipped. Shows no preview (it lives in SETTINGS).
- Preview Video: shows a video in its box (temp copy, nothing saved) - the OUTPUT previews."""
import json
import os
import re
from io import BytesIO

import av
import folder_paths
from comfy.cli_args import args
from comfy_api.latest import Types



class SgworxAudioOption:
    CATEGORY = "sgworx"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("choice",)
    FUNCTION = "pick"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"choice": (["Default", "No Audio", "Custom"], {"default": "Default"})}}

    def pick(self, choice):
        return (choice,)


def _target(folder, default):
    """(directory, is_inside_comfy_output); creates the directory. Empty = ComfyUI output/<default>."""
    out = os.path.abspath(folder_paths.get_output_directory())
    folder = (folder or "").strip().strip('"') or default
    folder = os.path.expandvars(os.path.expanduser(folder))
    path = os.path.abspath(folder if os.path.isabs(folder) else os.path.join(out, folder))
    os.makedirs(path, exist_ok=True)
    try:
        inside = os.path.commonpath([path, out]) == out
    except ValueError:  # different drive
        inside = False
    return path, inside


def _next_file(directory, name, ext):
    pat = re.compile(re.escape(name) + r"_(\d{5})_?\." + re.escape(ext) + "$")
    nums = [int(m.group(1)) for f in os.listdir(directory) if (m := pat.match(f))]
    return f"{name}_{(max(nums) + 1 if nums else 1):05}_.{ext}"


def _metadata(prompt, extra_pnginfo):
    if args.disable_metadata:
        return {}
    meta = dict(extra_pnginfo or {})
    if prompt is not None:
        meta["prompt"] = prompt
    return meta


def _save_video(video, directory, name, meta):
    filename = _next_file(directory, name, "mp4")
    video.save_to(os.path.join(directory, filename), format=Types.VideoContainer("mp4"), codec=Types.VideoCodec("auto"),
                  metadata=meta or None)
    return [filename]


def _save_audio(audio, directory, name, meta):
    meta = {k: json.dumps(v) for k, v in meta.items()}
    files = []
    for waveform in audio["waveform"].cpu():
        filename = _next_file(directory, name, "flac")
        buf = BytesIO()
        container = av.open(buf, mode="w", format="flac")
        for k, v in meta.items():
            container.metadata[k] = v
        layout = "mono" if waveform.shape[0] == 1 else "stereo"
        stream = container.add_stream("flac", rate=audio["sample_rate"], layout=layout)
        frame = av.AudioFrame.from_ndarray(waveform.movedim(0, 1).reshape(1, -1).float().numpy(), format="flt", layout=layout)
        frame.sample_rate, frame.pts = audio["sample_rate"], 0
        container.mux(stream.encode(frame))
        container.mux(stream.encode(None))
        container.close()
        with open(os.path.join(directory, filename), "wb") as f:
            f.write(buf.getbuffer())
        files.append(filename)
    return files


def _save_text(text, directory, name, meta):
    filename = _next_file(directory, name, "txt")
    with open(os.path.join(directory, filename), "w", encoding="utf-8") as f:
        f.write(text)
    return [filename]


class SgworxSaveAll:
    """One box for every result. Each field is that file's folder: a plain name = inside ComfyUI's output,
    a full path = anywhere. Results that weren't made this run are skipped."""
    CATEGORY = "sgworx"
    RETURN_TYPES = ()
    FUNCTION = "save"
    OUTPUT_NODE = True
    # input, field, default folder, file name, kind
    ITEMS = [("low_res_video", "low_res_video_folder", "video", "MiniMax_H3", "video"),
             ("high_res_video", "high_res_video_folder", "video", "MiniMax_H3_1080p", "video"),
             ("prompt_text", "prompt_folder", "prompt", "MiniMax_H3_prompt", "text"),
             ("yue2_song", "yue2_song_folder", "audio", "MiniMax_H3_YuE2_song", "audio"),
             ("h3_soundtrack", "h3_soundtrack_folder", "audio", "MiniMax_H3_soundtrack", "audio")]
    TYPES = {"video": "VIDEO", "audio": "AUDIO", "text": "STRING"}
    TIP = "Folder for this file. A plain name is a folder inside ComfyUI's output; paste a full path (e.g. C:/Users/you/Desktop/Kit) to save anywhere."

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {field: ("STRING", {"default": default, "tooltip": cls.TIP}) for _, field, default, _, _ in cls.ITEMS},
                "optional": {inp: (cls.TYPES[kind], {"forceInput": True} if kind == "text" else {}) for inp, _, _, _, kind in cls.ITEMS},
                "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"}}

    def save(self, prompt=None, extra_pnginfo=None, **kw):
        meta = _metadata(prompt, extra_pnginfo)
        saver = {"video": _save_video, "audio": _save_audio, "text": _save_text}
        for inp, field, default, name, kind in self.ITEMS:
            value = kw.get(inp)
            if value is not None:
                saver[kind](value, _target(kw.get(field), default)[0], name, meta)
        return {}


class SgworxPreviewVideo:
    """Shows a video in its box without saving it anywhere permanent."""
    CATEGORY = "sgworx"
    RETURN_TYPES = ()
    FUNCTION = "preview"
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {"optional": {"video": ("VIDEO",)}}

    def preview(self, video=None):
        if video is None:
            return {}
        tmp = folder_paths.get_temp_directory()
        os.makedirs(tmp, exist_ok=True)
        filename = _next_file(tmp, "sgworx_preview", "mp4")
        video.save_to(os.path.join(tmp, filename), format=Types.VideoContainer("mp4"), codec=Types.VideoCodec("auto"))
        return {"ui": {"images": [{"filename": filename, "subfolder": "", "type": "temp"}], "animated": (True,)}}


NODE_CLASS_MAPPINGS = {"SgworxAudioOption": SgworxAudioOption, "SgworxSaveAll": SgworxSaveAll, "SgworxPreviewVideo": SgworxPreviewVideo}
NODE_DISPLAY_NAME_MAPPINGS = {"SgworxAudioOption": "Audio Option", "SgworxSaveAll": "Save All", "SgworxPreviewVideo": "Preview Video"}
WEB_DIRECTORY = "./js"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
