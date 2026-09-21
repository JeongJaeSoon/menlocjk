"""Fill the 400-700 gap in MenloCJK with Medium (500) and SemiBold (600).

Orca renders the terminal with `-webkit-font-smoothing: antialiased`, which
makes the same face look lighter than it does in VSCode. With intermediate
weights in the family, Orca's Font Weight setting can compensate without
touching the other apps, which stay on 400.

Stroke widths come from Menlo's own Regular->Bold stem growth (172 -> 227
units), interpolated per 100 weight steps.
"""
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from pathops import LineCap, LineJoin, Path, PathOp, op

FAMILY = "MenloCJK"
VERSION = "1.000"
# (new style, source style, stroke width, weight class, subfamily, italic)
TARGETS = [
    ("Medium", "Regular", 18, 500, "Medium", False),
    ("SemiBold", "Regular", 37, 600, "SemiBold", False),
    ("MediumItalic", "Italic", 18, 500, "Medium Italic", True),
    ("SemiBoldItalic", "Italic", 37, 600, "SemiBold Italic", True),
]


def embolden(font, width):
    glyf, hmtx = font["glyf"], font["hmtx"]
    glyphset = font.getGlyphSet()
    failures = []
    for name in font.getGlyphOrder():
        if glyf[name].numberOfContours == 0:
            continue
        src = Path()
        glyphset[name].draw(src.getPen(glyphSet=glyphset))

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
    full = f"{FAMILY} {subfamily}"
    records = {
        0: "Locally merged font for personal use. Menlo (c) Apple, "
           "UDEV Gothic (OFL), D2Coding (OFL).",
        1: full,
        2: "Italic" if italic else "Regular",
        3: f"{FAMILY};{VERSION};{style}",
        4: full,
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


for style, source, width, weight, subfamily, italic in TARGETS:
    font = TTFont(f"out/{FAMILY}-{source}.ttf")
    failed = embolden(font, width)
    font["OS/2"].usWeightClass = weight
    font["OS/2"].fsSelection = 0x01 if italic else 0x40
    font["head"].macStyle = 0x02 if italic else 0
    rename(font, style, subfamily, italic)
    font.save(f"out/{FAMILY}-{style}.ttf")
    print(f"{style}: stroke={width} weight={weight} skipped={len(failed)}")
