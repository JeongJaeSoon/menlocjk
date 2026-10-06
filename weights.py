"""Build the shipped MenloCJK weight ramp from the four merged base faces.

Menlo only designs two weights, and the gap between them is narrow: stems of
172 and 227 units. On screen a third of that is hard to see, so the ramp is
pinned to a 27-unit step - the smallest one that reads as a real difference
at 14px - and Menlo's own Bold lands on 600 (172 + 2*27 = 226 ~ 227). Weights
above it are emboldened from Bold, so every step across the family is equal.

Emboldening unions the outline with a stroked copy of itself; stroke width
adds itself to the stem, half per side. Advance widths never change, so the
terminal grid is unaffected.

Consequence worth knowing: 700 is no longer Menlo's drawn Bold but a heavier
synthesis. To keep ANSI bold on the drawn one, point the app's bold-weight
setting at 600.
"""
import os

from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from pathops import LineCap, LineJoin, Path, PathOp, op

FAMILY = "MenloCJK"
VERSION = "1.000"
STEP = 27  # stem units per 100 weight

# 700 carries the RIBBI bold bits for apps that style-link by them. iTerm2 is
# not one: it picks bold by AppKit weight (usWeightClass), see apply.py.
RIBBI_BOLD = 700

# style -> (base face, extra stems above that base, weight, subfamily, italic)
TARGETS = [
    ("Regular", "Regular", 0, 400, "Regular", False),
    ("Medium", "Regular", 1, 500, "Medium", False),
    ("SemiBold", "Bold", 0, 600, "SemiBold", False),
    ("Bold", "Bold", 1, 700, "Bold", False),
    ("ExtraBold", "Bold", 2, 800, "ExtraBold", False),
    ("Black", "Bold", 3, 900, "Black", False),
    ("Italic", "Italic", 0, 400, "Italic", True),
    ("MediumItalic", "Italic", 1, 500, "Medium Italic", True),
    ("SemiBoldItalic", "BoldItalic", 0, 600, "SemiBold Italic", True),
    ("BoldItalic", "BoldItalic", 1, 700, "Bold Italic", True),
    ("ExtraBoldItalic", "BoldItalic", 2, 800, "ExtraBold Italic", True),
    ("BlackItalic", "BoldItalic", 3, 900, "Black Italic", True),
]


def embolden(font, width):
    glyf, hmtx = font["glyf"], font["hmtx"]
    glyphset = font.getGlyphSet()
    failures = []

    # Snapshot every outline before mutating glyf. A composite glyph is
    # drawn through glyphset, which resolves its components live off glyf -
    # if a component's own glyf entry were already replaced by its
    # emboldened self earlier in this loop, the composite would draw that
    # already-thickened shape and stroke it a second time.
    originals = {}
    for name in font.getGlyphOrder():
        if glyf[name].numberOfContours == 0:
            continue
        src = Path()
        glyphset[name].draw(src.getPen(glyphSet=glyphset))
        originals[name] = src

    for name, src in originals.items():
        thick = Path()
        src.draw(thick.getPen())
        thick.stroke(width, LineCap.ROUND_CAP, LineJoin.ROUND_JOIN, 4.0)
        thick.convertConicsToQuads()

        try:
            merged = op(src, thick, PathOp.UNION, fix_winding=True)
        except Exception:
            failures.append(name)
            continue

        pen = TTGlyphPen(glyphset)
        merged.draw(Cu2QuPen(pen, 0.6))
        glyph = pen.glyph()
        glyph.recalcBounds(glyf)
        advance = hmtx[name][0]
        glyf[name] = glyph
        hmtx[name] = (advance, getattr(glyph, "xMin", 0))
    return failures


def rename(font, style, subfamily, italic):
    full = FAMILY if subfamily in ("Regular", "Italic") else f"{FAMILY} {subfamily}"
    records = {
        0: "Locally merged font for personal use. Menlo (c) Apple, "
           "UDEV Gothic (OFL), D2Coding (OFL).",
        1: full,
        2: "Italic" if italic else "Regular",
        3: f"{FAMILY};{VERSION};{style}",
        4: f"{FAMILY} {subfamily}",
        5: f"Version {VERSION}",
        6: f"{FAMILY}-{style}",
        16: FAMILY,
        17: subfamily,
    }
    name = font["name"]
    name.names = []
    for nid, value in records.items():
        name.setName(value, nid, 3, 1, 0x409)
        name.setName(value, nid, 1, 0, 0)


os.makedirs("out", exist_ok=True)
for style, base, steps, weight, subfamily, italic in TARGETS:
    font = TTFont(f"base/{FAMILY}-{base}.ttf")
    skipped = embolden(font, steps * STEP) if steps else []
    font["OS/2"].usWeightClass = weight
    bold = weight == RIBBI_BOLD
    font["OS/2"].fsSelection = {
        (False, False): 0x40,  # REGULAR
        (False, True): 0x01,  # ITALIC
        (True, False): 0x20,  # BOLD
        (True, True): 0x21,  # BOLD | ITALIC
    }[(bold, italic)]
    font["head"].macStyle = (0x01 if bold else 0) | (0x02 if italic else 0)
    font["post"].isFixedPitch = 1
    rename(font, style, subfamily, italic)
    font.save(f"out/{FAMILY}-{style}.ttf")
    print(f"{style:16s} base={base:10s} +{steps * STEP:<3d} weight={weight} skipped={len(skipped)}")
