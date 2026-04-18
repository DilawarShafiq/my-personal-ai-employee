# OBS Studio setup — scene by scene, field by field

Skip the guesswork. Every OBS setting below is concrete.

## A. Output / Audio / Video (one-time settings)

**Settings → Output → Output Mode: Advanced**

| Tab | Field | Value |
|---|---|---|
| Recording | Type | Standard |
| Recording | Recording Path | any local folder with ≥ 5 GB free |
| Recording | Recording Format | MP4 |
| Recording | Video Encoder | **NVIDIA NVENC H.264** (if GPU) else **x264** |
| Recording | Rate Control | **CBR** |
| Recording | Bitrate | **12000 Kbps** |
| Recording | Keyframe Interval | 2 |
| Recording | Preset | Quality (NVENC) or veryfast (x264) |
| Recording | Profile | high |
| Audio | Track 1 Bitrate | **320** |

**Settings → Audio**

| Field | Value |
|---|---|
| Sample Rate | 48 kHz |
| Mic/Aux Audio | your dedicated USB or built-in mic |

**Settings → Video**

| Field | Value |
|---|---|
| Base (Canvas) Resolution | 1920x1080 |
| Output (Scaled) Resolution | 1920x1080 |
| Downscale Filter | Lanczos |
| Common FPS Values | **60** |

## B. Mic filters — click the gear icon on your Mic/Aux source → Filters

Add these three, in this order:

1. **Noise Suppression**
   - Method: **RNNoise** (best quality, low CPU).
2. **Compressor**
   - Ratio: 4.0:1
   - Threshold: -18 dB
   - Attack: 6 ms
   - Release: 60 ms
   - Output Gain: +3 dB
   - Sidechain/Ducking Source: None
3. **Limiter**
   - Threshold: -1 dB
   - Release: 60 ms

Test by recording 20 s of speech + a clap. The clap should not clip
(no red on the meter). Speech should peak around -12 to -8 dB.

## C. Scenes — create these three

### Scene 1 — "Intro" (3-second hold at video start)

1. Scene Collection → New → name: `autosapien-demo`.
2. Click **+ Add Scene**, name it **Intro**.
3. Click **+ Add Source → Image**.
   - Browse to `docs/rendered/intro_card.png` (produced by
     `scripts\render_cards.ps1`; see below).
   - Transform: **Fit to screen** (right-click the source → Transform
     → Fit to screen).

### Scene 2 — "Main" (the 7+ minutes of actual demo)

1. **+ Add Scene**, name it **Main**.
2. **+ Add Source → Display Capture** → pick your primary monitor.
   - Transform → Fit to screen.
3. The mic is already a Global audio source; no per-scene add needed.

(Optional, only if you want your face in a corner — Personal taste. Skipping is fine for this kind of demo.)

### Scene 3 — "Outro" (3-second hold at video end)

Same as Intro, but source the `docs/rendered/outro_card.png`.

## D. Render the intro/outro cards

From the repo root in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\render_cards.ps1
```

This uses headless Chrome (or Edge as a fallback) to rasterize
`docs/intro_card.svg` and `docs/outro_card.svg` to 1920×1080 PNG files
under `docs/rendered/`. Once done, point the OBS Image sources at
those PNGs.

## E. Hotkeys (Settings → Hotkeys)

| Action | Bind to |
|---|---|
| Start Recording | **F9** |
| Stop Recording | **F10** |
| Switch Scene: Intro | Ctrl+1 |
| Switch Scene: Main | Ctrl+2 |
| Switch Scene: Outro | Ctrl+3 |

## F. Record flow

1. Load scene **Intro**. Hit **F9** (start record).
2. Hold on Intro card for **3 seconds** (count silently).
3. Ctrl+2 → switch to **Main**. Start the narration.
4. When done, Ctrl+3 → **Outro**. Hold 3 s.
5. **F10** to stop.

The MP4 lands in your Recording Path. Open it once to verify audio is
clean and the terminal text is sharp.

## G. One-shot bootstrap (optional)

If you want a single command to cover rendering cards + smoke-testing
OBS, `scripts\record_bootstrap.ps1` runs the card render plus opens
OBS Studio if you have it installed:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\record_bootstrap.ps1
```
