"""Extract and normalise the three source fonts so they can be merged.

Everything ends up at 2048 upem with GSUB/GPOS dropped - the merged font is
for terminals, which never ask for shaping features.
"""
import os
from fontTools.ttLib import TTFont, TTCollection
from fontTools.ttLib.scaleUpem import scale_upem

MENLO = "/System/Library/Fonts/Menlo.ttc"
UDEV = os.path.expanduser("~/Library/Fonts/UDEVGothicNF-{}.ttf")
D2 = os.path.expanduser("~/Library/Fonts/D2Coding-Ver1.3.3-20260725.ttc")

# style -> (menlo ttc index, udev suffix, d2coding ttc index)
STYLES = {
    "Regular": (0, "Regular", 0),
    "Bold": (1, "Bold", 1),
    "Italic": (2, "Italic", 0),
    "BoldItalic": (3, "BoldItalic", 1),
}


def strip(font):
    for tag in ("GSUB", "GPOS", "GDEF", "DSIG", "morx", "kern"):
        if tag in font:
            del font[tag]
    return font


os.makedirs("src", exist_ok=True)
menlo = TTCollection(MENLO).fonts
d2 = TTCollection(D2).fonts

for style, (mi, usuf, di) in STYLES.items():
    strip(menlo[mi]).save(f"src/menlo-{style}.ttf")

    strip(TTFont(UDEV.format(usuf))).save(f"src/udev-{style}.ttf")

    f = strip(d2[di])
    scale_upem(f, 2048)
    f.save(f"src/d2-{style}.ttf")
    print(style, "ok")
