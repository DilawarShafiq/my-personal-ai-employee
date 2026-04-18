"""Patch the existing OBS scene collection to add the Outro scene + mic
filter chain (Noise Suppression, Compressor, Limiter) for Dilawar.

Reads:  %APPDATA%/obs-studio/basic/scenes/autosapiendemo.json
Writes: same path (makes a .bak first)

Assumes OBS is NOT running. Kill it first with taskkill.
"""
from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path

APPDATA = Path(os.environ["APPDATA"])
SCENE_FILE = APPDATA / "obs-studio" / "basic" / "scenes" / "autosapiendemo.json"
OUTRO_IMG = r"C:/Users/TechTiesIbrahim/hackathon0_by_dilawar/docs/rendered/outro_card.png"


def _source_boilerplate() -> dict:
    """Fields every OBS source needs. Matches the shape of existing entries."""
    return {
        "prev_ver": 536936449,
        "mixers": 0,
        "sync": 0,
        "flags": 0,
        "volume": 1.0,
        "balance": 0.5,
        "enabled": True,
        "muted": False,
        "push-to-mute": False,
        "push-to-mute-delay": 0,
        "push-to-talk": False,
        "push-to-talk-delay": 0,
        "hotkeys": {},
        "deinterlace_mode": 0,
        "deinterlace_field_order": 0,
        "monitoring_type": 0,
        "private_settings": {},
    }


def _scene_item(name: str, source_uuid: str, item_id: int) -> dict:
    """A scene-item that places a source inside a scene at 0,0 fit-to-screen."""
    return {
        "name": name,
        "source_uuid": source_uuid,
        "visible": True,
        "locked": False,
        "rot": 0.0,
        "scale_ref": {"x": 1920.0, "y": 1080.0},
        "align": 5,
        "bounds_type": 2,  # 2 = "scale to inner bounds" (fit)
        "bounds_align": 0,
        "bounds_crop": False,
        "crop_left": 0, "crop_top": 0, "crop_right": 0, "crop_bottom": 0,
        "id": item_id,
        "group_item_backup": False,
        "pos": {"x": 0.0, "y": 0.0},
        "pos_rel": {"x": -1.7777777910232544, "y": -1.0},
        "scale": {"x": 1.0, "y": 1.0},
        "scale_rel": {"x": 1.0, "y": 1.0},
        "bounds": {"x": 1920.0, "y": 1080.0},
        "bounds_rel": {"x": 3.555555582046509, "y": 2.0},
        "scale_filter": "disable",
        "blend_method": "default",
        "blend_type": "normal",
        "show_transition": {"duration": 300},
        "hide_transition": {"duration": 300},
        "private_settings": {},
    }


def _filter_noise_suppression() -> dict:
    return {
        "prev_ver": 536936449,
        "name": "Noise Suppression",
        "uuid": str(uuid.uuid4()),
        "id": "noise_suppress_filter_v2",
        "versioned_id": "noise_suppress_filter_v2",
        "settings": {"method": "rnnoise"},
        "mixers": 0, "sync": 0, "flags": 0, "volume": 1.0, "balance": 0.5,
        "enabled": True, "muted": False,
        "push-to-mute": False, "push-to-mute-delay": 0,
        "push-to-talk": False, "push-to-talk-delay": 0,
        "hotkeys": {},
        "deinterlace_mode": 0, "deinterlace_field_order": 0,
        "monitoring_type": 0, "private_settings": {},
    }


def _filter_compressor() -> dict:
    return {
        "prev_ver": 536936449,
        "name": "Compressor",
        "uuid": str(uuid.uuid4()),
        "id": "compressor_filter",
        "versioned_id": "compressor_filter",
        "settings": {
            "ratio": 4.0,
            "threshold": -18.0,
            "attack_time": 6,
            "release_time": 60,
            "output_gain": 3.0,
            "sidechain_source": "none",
        },
        "mixers": 0, "sync": 0, "flags": 0, "volume": 1.0, "balance": 0.5,
        "enabled": True, "muted": False,
        "push-to-mute": False, "push-to-mute-delay": 0,
        "push-to-talk": False, "push-to-talk-delay": 0,
        "hotkeys": {},
        "deinterlace_mode": 0, "deinterlace_field_order": 0,
        "monitoring_type": 0, "private_settings": {},
    }


def _filter_limiter() -> dict:
    return {
        "prev_ver": 536936449,
        "name": "Limiter",
        "uuid": str(uuid.uuid4()),
        "id": "limiter_filter",
        "versioned_id": "limiter_filter",
        "settings": {"threshold": -1.0, "release_time": 60},
        "mixers": 0, "sync": 0, "flags": 0, "volume": 1.0, "balance": 0.5,
        "enabled": True, "muted": False,
        "push-to-mute": False, "push-to-mute-delay": 0,
        "push-to-talk": False, "push-to-talk-delay": 0,
        "hotkeys": {},
        "deinterlace_mode": 0, "deinterlace_field_order": 0,
        "monitoring_type": 0, "private_settings": {},
    }


def main() -> None:
    if not SCENE_FILE.exists():
        raise SystemExit(f"Scene file not found: {SCENE_FILE}")

    shutil.copy2(SCENE_FILE, SCENE_FILE.with_suffix(".json.pre-autoconfig.bak"))
    doc = json.loads(SCENE_FILE.read_text(encoding="utf-8"))
    sources = doc["sources"]
    existing_names = {s["name"] for s in sources}

    # 1. Outro Card (image source) if missing
    outro_card_uuid = None
    for s in sources:
        if s["name"] == "Outro Card":
            outro_card_uuid = s["uuid"]
            break
    if outro_card_uuid is None:
        outro_card_uuid = str(uuid.uuid4())
        sources.append({
            **_source_boilerplate(),
            "name": "Outro Card",
            "uuid": outro_card_uuid,
            "id": "image_source",
            "versioned_id": "image_source",
            "settings": {"file": OUTRO_IMG},
        })
        print("  added  Outro Card image source")

    # 2. Outro scene (referencing Outro Card) if missing
    if "Outro" not in existing_names:
        sources.append({
            **_source_boilerplate(),
            "name": "Outro",
            "uuid": str(uuid.uuid4()),
            "id": "scene",
            "versioned_id": "scene",
            "settings": {
                "id_counter": 1,
                "custom_size": False,
                "items": [_scene_item("Outro Card", outro_card_uuid, 1)],
            },
            "hotkeys": {
                "OBSBasic.SelectScene": [],
                "libobs.show_scene_item.1": [],
                "libobs.hide_scene_item.1": [],
            },
            "canvas_uuid": "6c69626f-6273-4c00-9d88-c5136d61696e",
        })
        print("  added  Outro scene")

    # 3. Mic/Aux audio source + filter chain if missing
    mic_exists = any(s.get("id") in ("wasapi_input_capture", "wasapi_input_capture_device")
                     for s in sources)
    if not mic_exists:
        sources.append({
            **_source_boilerplate(),
            "name": "Mic/Aux",
            "uuid": str(uuid.uuid4()),
            "id": "wasapi_input_capture",
            "versioned_id": "wasapi_input_capture",
            "settings": {"device_id": "default"},
            "mixers": 255,    # route to all tracks
            "volume": 1.0,
            "filters": [
                _filter_noise_suppression(),
                _filter_compressor(),
                _filter_limiter(),
            ],
            "hotkeys": {
                "libobs.mute": [],
                "libobs.unmute": [],
                "libobs.push-to-mute": [],
                "libobs.push-to-talk": [],
            },
        })
        print("  added  Mic/Aux + RNNoise + Compressor + Limiter filters")
    else:
        # Mic already exists — append filters to it if not present.
        for s in sources:
            if s.get("id") in ("wasapi_input_capture", "wasapi_input_capture_device"):
                s.setdefault("filters", [])
                have = {f.get("name") for f in s["filters"]}
                if "Noise Suppression" not in have:
                    s["filters"].append(_filter_noise_suppression())
                    print("  added  Noise Suppression filter")
                if "Compressor" not in have:
                    s["filters"].append(_filter_compressor())
                    print("  added  Compressor filter")
                if "Limiter" not in have:
                    s["filters"].append(_filter_limiter())
                    print("  added  Limiter filter")

    # 4. scene_order
    order_names = {e["name"] for e in doc["scene_order"]}
    if "Outro" not in order_names:
        doc["scene_order"].append({"name": "Outro"})
        print("  added  Outro to scene_order")

    # 5. current_scene stays Main (that's fine; user will set it via hotkey during recording)

    SCENE_FILE.write_text(json.dumps(doc, indent=4), encoding="utf-8")
    print(f"\nWrote patched scene collection to {SCENE_FILE}")
    print(f"Backup at: {SCENE_FILE.with_suffix('.json.pre-autoconfig.bak')}")


if __name__ == "__main__":
    main()
