---
name: menlocjk-build
description: Build the MenloCJK merged font (Menlo + UDEV Gothic NF + D2Coding) from source on a Mac and install it into ~/Library/Fonts. Use on a new machine, after a macOS reinstall, or when changing the weight ramp - "폰트 빌드", "폰트 만들어줘", "새 맥 폰트 설치", "MenloCJK 빌드", "build the font", "rebuild fonts". Applying app settings afterwards is menlocjk-apply.
---

# Building MenloCJK

One font family carrying Latin, Japanese and Korean so three apps with three
different fallback models render identically. The font is never committed —
Menlo is Apple's and its outlines cannot be redistributed — so every machine
builds its own.

## Prerequisites

- macOS (supplies Menlo)
- [`uv`](https://docs.astral.sh/uv/)
- [UDEV Gothic NF](https://github.com/yuru7/udev-gothic) — Regular, Bold, Italic, BoldItalic
- [D2Coding](https://github.com/naver/d2codingfont) — the `.ttc`

Install those two into `~/Library/Fonts/` first. Check before building:

```sh
ls ~/Library/Fonts/UDEVGothicNF-*.ttf ~/Library/Fonts/D2Coding*.ttc
```

If the D2Coding filename differs from the constant at the top of `prep.py`,
fix the constant rather than renaming the download.

## Build

```sh
./build.sh
cp out/MenloCJK-*.ttf ~/Library/Fonts/
```

Roughly 6 minutes; most of it is `weights.py` emboldening 54k glyphs per face.
Twelve files land in `out/` — Regular, Medium, SemiBold, Bold, ExtraBold, Black
and their italics.

## What the three stages do

`prep.py` pulls Menlo out of the system `.ttc`, drops GSUB/GPOS from all three
sources, and rescales D2Coding from 1000 to 2048 upem. `merge.py` merges them
into `base/` — cmap conflicts resolve to the first font, so Latin and box
drawing come from Menlo, Japanese and Nerd Font icons from UDEV Gothic NF,
Hangul from D2Coding — then forces Menlo's vertical metrics so line height is
unchanged. `weights.py` derives the twelve shipped faces from those four.

`merge.py` writes `base/` and `weights.py` writes `out/`, so re-running never
eats its own input.

## Verify the build

Stems must come out on a 27-unit grid, and advances must not have moved:

```sh
uv run --with fonttools python - <<'EOF'
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
for s in ("Regular","Medium","SemiBold","Bold","ExtraBold","Black"):
    f = TTFont(f"out/MenloCJK-{s}.ttf"); gs, c = f.getGlyphSet(), f.getBestCmap()
    p = BoundsPen(gs); gs[c[0x7C]].draw(p)
    print(f"{s:10s} wt={f['OS/2'].usWeightClass} stem={p.bounds[2]-p.bounds[0]:.0f} "
          f"fsSel=0x{f['OS/2'].fsSelection:04x} A={f['hmtx'][c[0x41]][0]} 가={f['hmtx'][c[0xAC00]][0]}")
EOF
```

Expected: stems 172 / 199 / 227 / 254 / 281 / 308, advances always A=1233 and
가=2048, and `fsSel=0x0020` on Bold only (0x0040 elsewhere). That bold bit is
what iTerm2 uses for style linking — `usWeightClass` alone is not enough there.

400 and 600 are Menlo's own two drawn weights; everything else is emboldened
with skia-pathops. Menlo's Bold lands on 600 rather than 700 because
172 + 2×27 = 226 ≈ 227, which is what makes the whole ramp even.

## After building

Run `menlocjk-apply` to configure the apps. Orca needs a restart before it can
see newly installed faces.
