"""Merge Menlo + UDEV Gothic NF + D2Coding into one family.

Cmap conflicts resolve to the first font, so Latin, box drawing and blocks
come from Menlo, Japanese and Nerd Font icons from UDEV Gothic NF, and
Hangul from D2Coding. Advance widths are left untouched so the result
renders exactly like the four-font CSS fallback chain it replaces.
"""
import logging, os
from fontTools.merge import Merger
from fontTools.ttLib import TTFont

logging.getLogger("fontTools").setLevel(logging.ERROR)

FAMILY = "MenloCJK"
VERSION = "1.000"
STYLES = {
    "Regular": dict(sub="Regular", mac=0, fs=0x40, weight=400),
    "Bold": dict(sub="Bold", mac=1, fs=0x20, weight=700),
    "Italic": dict(sub="Italic", mac=2, fs=0x01, weight=400),
    "BoldItalic": dict(sub="Bold Italic", mac=3, fs=0x21, weight=700),
}


def set_names(font, style, meta):
    full = FAMILY if meta["sub"] == "Regular" else f"{FAMILY} {meta['sub']}"
    ps = f"{FAMILY}-{style}"
    records = {
        0: "Locally merged font for personal use. Menlo (c) Apple, "
           "UDEV Gothic (OFL), D2Coding (OFL).",
        1: FAMILY,
        2: meta["sub"],
        3: f"{FAMILY};{VERSION};{style}",
        4: full,
        5: f"Version {VERSION}",
        6: ps,
        16: FAMILY,
        17: meta["sub"],
    }
    name = font["name"]
    name.names = []
    for nid, value in records.items():
        name.setName(value, nid, 3, 1, 0x409)
        name.setName(value, nid, 1, 0, 0)


def main():
    os.makedirs("out", exist_ok=True)
    for style, meta in STYLES.items():
        sources = [f"src/menlo-{style}.ttf", f"src/udev-{style}.ttf", f"src/d2-{style}.ttf"]
        merged = Merger().merge(sources)

        menlo = TTFont(sources[0])
        for tag in ("hhea",):
            for attr in ("ascent", "descent", "lineGap"):
                setattr(merged[tag], attr, getattr(menlo[tag], attr))
        for attr in ("sTypoAscender", "sTypoDescender", "sTypoLineGap",
                     "usWinAscent", "usWinDescent", "sxHeight", "sCapHeight"):
            if hasattr(menlo["OS/2"], attr):
                setattr(merged["OS/2"], attr, getattr(menlo["OS/2"], attr))

        merged["OS/2"].usWeightClass = meta["weight"]
        merged["OS/2"].fsSelection = meta["fs"]
        merged["OS/2"].panose.bProportion = 9  # monospaced
        merged["head"].macStyle = meta["mac"]
        merged["post"].isFixedPitch = 1
        set_names(merged, style, meta)

        path = f"out/{FAMILY}-{style}.ttf"
        merged.save(path)
        cmap = TTFont(path).getBestCmap()
        print(f"{style:11s} glyphs={len(merged.getGlyphOrder()):6d} cmap={len(cmap):6d} "
              f"A={0x41 in cmap} 漢={0x6F22 in cmap} 가={0xAC00 in cmap} "
              f"─={0x2500 in cmap} NF={0xF07C in cmap} PL={0xE0B0 in cmap}")


main()
