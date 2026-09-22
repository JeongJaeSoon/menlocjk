---
name: menlocjk-apply
description: Point VSCode, iTerm2 and/or Orca at the MenloCJK font with the right size and weight, or diagnose one of them rendering differently from the others. Takes app names as arguments (vscode, iterm2, orca; default all) - "폰트 설정 적용", "폰트 통일", "vscode 폰트만", "orca 폰트 적용", "폰트 굵기 다름", "한글만 다르게 보임", "apply font settings", "fonts look different". Building the font first is menlocjk-build.
---

# Applying the MenloCJK setup

`apply.py` holds the per-app values and knows how each app has to be written to.
**It is the source of truth — change it, not the apps.**

## Usage

Arguments select the apps; no argument means all three.

```sh
python3 apply.py                    # all
python3 apply.py vscode             # one
python3 apply.py iterm2 orca        # some
python3 apply.py --check            # report only, change nothing
```

Always offer `--check` first when the user has not asked for a change outright.

```
[  ok] fonts: 12 faces installed
[  ok] vscode: already set
[  ok] iterm2: Default: already set
[warn] orca: running - quit it and rerun, or set it by hand in Settings > Terminal
```

If fonts report missing or incomplete, stop and run `menlocjk-build` first.

## Target state

| App | Font | Size | Weight |
|---|---|---:|---:|
| VSCode | `MenloCJK` | 14 | 400 (default) |
| iTerm2 | `MenloCJK-Regular` | 14 | 400, Thin Strokes **Never** |
| Orca | `MenloCJK` | 14 | **500**, bold 700 |

Orca is deliberately one step heavier. Do not "correct" it to 400.

## Why each app is written differently

**VSCode** — `settings.json` is JSONC, so reserialising it would strip the
user's comments. Only the target keys are replaced in place, with a timestamped
backup.

**iTerm2** — driven over its Python API while the app runs. Editing the prefs
file instead only works while iTerm2 is closed; on exit it writes its in-memory
state back over the file. The API needs Settings → General → Magic → Enable
Python API. The `iterm2` module lives in iTerm2's own venv, which `apply.py`
locates automatically.

**Orca** — only touched while Orca is quit. It rewrites `orca-data.json` from
memory within seconds, so a live edit silently reverts. Quitting Orca is safe:
PTYs belong to a detached daemon (`daemon-entry.js`, ppid 1), so agent sessions
survive and reattach on relaunch.

## Diagnosing "one app looks different"

Column alignment, run in each app:

```sh
printf '%s\n' '|한글한글한글|' '|日本語日本語|' '|ABCDEFGHIJKL|' '|------------|'
```

All four closing `|` must land in the same column. If they do, metrics are fine
and any remaining difference is weight or rasterisation — work down this list:

1. **Orca shows no weight difference between 400 and 500, and jumps at 600** —
   Orca has not been restarted since the faces were installed. Chromium caches
   the family at launch, so 500 falls back to 400 and 600+ to 700.
2. **iTerm2 looks thin** — Thin Strokes is back on Always (`3`). `apply.py
   iterm2` sets it to Never (`0`). CoreText draws lighter with it on and
   Chromium has no equivalent.
3. **Orca looks thin at the same weight as the others** — expected. Orca puts
   `-webkit-font-smoothing: antialiased` on `body`, so macOS Chromium uses
   grayscale AA there. Its plugin manifest offers no CSS injection, so this is
   not fixable; weight 500 compensates.
4. **Korean or Japanese falls back to a proportional system font** — the family
   name is wrong or empty. Check `terminalFontFamily` in Orca and
   `terminal.integrated.fontFamily` in VSCode; both must be exactly `MenloCJK`.
5. **Bold looks smeared in iTerm2 only** — the 700 faces lost their
   `fsSelection` BOLD / `macStyle` bits. Rebuild with `menlocjk-build`.

## Changing the setup

Edit the constants at the top of `apply.py` (`FAMILY`, `SIZE`,
`VSCODE_SETTINGS`, `ITERM_PROFILE`, `ORCA_SETTINGS`), rerun it, and commit. That
keeps every machine in agreement.
