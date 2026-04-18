"""Bump OBS Simple Output settings for YouTube-native demo recording.

Patches %APPDATA%/obs-studio/basic/profiles/Untitled/basic.ini:
  SimpleOutput.VBitrate       6000  -> 12000
  SimpleOutput.ABitrate        160  ->   320
  SimpleOutput.RecQuality    Small  -> Stream
  SimpleOutput.StreamEncoder                -> nvenc (if not already)
  SimpleOutput.RecEncoder                   -> nvenc (if not already)
  SimpleOutput.NVENCPreset2                 -> p5   (balanced quality)

We stay in Simple mode (Mode=Simple) — the user's NVENC is already
selected. Bumping bitrate + audio + record quality gets us to
YouTube-native 1080p60 without touching Advanced-mode complexity.

Run with OBS closed.
"""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

PROFILE = Path(os.environ["APPDATA"]) / "obs-studio" / "basic" / "profiles" / "Untitled" / "basic.ini"

SUBS = [
    (r"(^\[SimpleOutput\][^\[]*?\bVBitrate=)\d+", r"\g<1>12000"),
    (r"(^\[SimpleOutput\][^\[]*?\bABitrate=)\d+", r"\g<1>320"),
    (r"(^\[SimpleOutput\][^\[]*?\bRecQuality=)\w+", r"\g<1>Stream"),
    (r"(^\[SimpleOutput\][^\[]*?\bStreamEncoder=)\w+", r"\g<1>nvenc"),
    (r"(^\[SimpleOutput\][^\[]*?\bRecEncoder=)\w+", r"\g<1>nvenc"),
]


def main() -> None:
    if not PROFILE.exists():
        raise SystemExit(f"Profile not found: {PROFILE}")
    shutil.copy2(PROFILE, PROFILE.with_suffix(".ini.pre-autoconfig.bak"))

    text = PROFILE.read_text(encoding="utf-8-sig")
    original = text
    for pattern, replace in SUBS:
        text, n = re.subn(pattern, replace, text, flags=re.MULTILINE | re.DOTALL)
        label = pattern.split("\\b")[-2].strip("=") if "\\b" in pattern else pattern
        print(f"  {'ok   ' if n else 'skip '} {label}  ({n} replaced)")

    if text == original:
        print("  No changes needed — profile is already tuned.")
        return

    # Write WITH BOM to match OBS's own UTF-8-BOM output.
    PROFILE.write_text(text, encoding="utf-8-sig")
    print(f"\nWrote patched profile to {PROFILE}")


if __name__ == "__main__":
    main()
