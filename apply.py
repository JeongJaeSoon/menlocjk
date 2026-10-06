#!/usr/bin/env python3
"""Apply the MenloCJK terminal setup to VSCode, iTerm2 and Orca.

Run with --check to report the current state without changing anything.

Orca sits one weight step above the others on purpose: it puts
`-webkit-font-smoothing: antialiased` on `body`, so macOS Chromium draws the
same face with grayscale AA and it reads lighter. 500 (stem 199) there lands
on the same apparent weight as 400 (stem 172) elsewhere, and its bold 700 on
the others' 600.
"""
import argparse
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import time
from glob import glob
from pathlib import Path

FAMILY = "MenloCJK"
SIZE = 14

VSCODE_SETTINGS = {
    "editor.fontFamily": FAMILY,
    "terminal.integrated.fontFamily": FAMILY,
    "editor.fontSize": SIZE,
    "terminal.integrated.fontSize": SIZE,
    "terminal.integrated.fontWeightBold": 600,  # Menlo's drawn Bold, as in iTerm2
}

ITERM_PROFILE = {
    "Normal Font": f"{FAMILY}-Regular {SIZE}",
    "Non Ascii Font": f"{FAMILY}-Regular {SIZE}",
    "Use Non-ASCII Font": False,
    "Special Font Config": "{version:1,entries:[]}",
    "Thin Strokes": 0,  # 3 (Always) is the default and draws lighter than Chromium
    "Use Bold Font": True,
    "Use Italic Font": True,
}

# App-wide advanced setting, not per profile. iTerm2 finds bold by walking
# NSFontManager weights up from the regular face until one is at least this
# much heavier. AppKit maps usWeightClass 400/500/600/700 to 5/6/8/9, so the
# default 4 lands on the synthetic 700 and 3 on Menlo's drawn Bold at 600.
ITERM_DOMAIN = "com.googlecode.iterm2"
ITERM_BOLD_KEY, ITERM_BOLD_DIFF = "MinimumWeightDifferenceForBoldFont", 3

ORCA_SETTINGS = {
    "terminalFontFamily": FAMILY,
    "terminalFontSize": SIZE,
    "terminalFontWeight": 500,
    "terminalFontWeightBold": 700,
}

HOME = Path.home()
VSCODE_JSON = HOME / "Library/Application Support/Code/User/settings.json"
ORCA_PROFILES = HOME / "Library/Application Support/orca/profiles"
ITERM_PREFS = HOME / ".config/iterm2/com.googlecode.iterm2.plist"
FONT_DIR = HOME / "Library/Fonts"

OK, WARN, FAIL = "  ok", "warn", "fail"


def say(status, app, message):
    print(f"[{status}] {app}: {message}")


def process_running(name):
    out = subprocess.run(["ps", "-Ac", "-o", "comm="], capture_output=True, text=True).stdout
    return name in out.split("\n")


def backup(path):
    stamp = time.strftime("%Y%m%d%H%M%S")
    shutil.copy2(path, f"{path}.bak.{stamp}")


def check_fonts():
    faces = sorted(p.name for p in FONT_DIR.glob(f"{FAMILY}-*.ttf"))
    if len(faces) >= 12:
        say(OK, "fonts", f"{len(faces)} faces installed")
    elif faces:
        say(WARN, "fonts", f"only {len(faces)} faces: {', '.join(faces)} - run ./build.sh")
    else:
        say(FAIL, "fonts", f"no {FAMILY} in {FONT_DIR} - run ./build.sh first")
    return len(faces) >= 12


def apply_vscode(check):
    if not VSCODE_JSON.exists():
        say(WARN, "vscode", f"{VSCODE_JSON} not found, skipping")
        return

    text = VSCODE_JSON.read_text(encoding="utf-8")
    changes, updated = [], text

    for key, value in VSCODE_SETTINGS.items():
        literal = json.dumps(value)
        # The file is JSONC, so edit the one key in place rather than
        # reparsing. Anchored to line start (with MULTILINE) so a
        # `// "key": ...` comment line doesn't match; the value alternates a
        # quoted JSON string - so an internal comma, e.g. a font fallback
        # list, doesn't truncate the capture - with a bare scalar that stops
        # before a `}` instead of swallowing one on a comma-less last entry.
        pattern = re.compile(
            rf'^(\s*"{re.escape(key)}"\s*:\s*)("(?:[^"\\]|\\.)*"|[^,\n}}]+)',
            re.MULTILINE)
        matches = list(pattern.finditer(updated))
        if len(matches) > 1:
            say(WARN, "vscode", f"{key}: {len(matches)} matches (language override?) - editing the first")
        found = matches[0] if matches else None
        if found:
            if found.group(2).strip() == literal:
                continue
            changes.append(f"{key}: {found.group(2).strip()} -> {literal}")
            updated = updated[:found.start()] + found.group(1) + literal + updated[found.end():]
        else:
            changes.append(f"{key}: (missing) -> {literal}")
            closing = updated.rstrip().rfind("}")
            prefix = updated[:closing].rstrip().rstrip(",")
            sep = "" if prefix.endswith("{") else ","
            updated = prefix + f'{sep}\n  "{key}": {literal},\n' + updated[closing:]

    if not changes:
        say(OK, "vscode", "already set")
    elif check:
        say(WARN, "vscode", f"would change {len(changes)}: " + "; ".join(changes))
    else:
        backup(VSCODE_JSON)
        VSCODE_JSON.write_text(updated, encoding="utf-8")
        say(OK, "vscode", f"set {len(changes)}: " + "; ".join(changes))


def iterm_python():
    """iTerm2 ships the `iterm2` module inside its own venv.

    It keeps several of them side by side (iterm2env, iterm2env-3.14, ...),
    each holding several Python versions, so pick the newest by parsed version
    rather than by string order - "3.8.19" sorts above "3.14.0" as text.
    """
    if "iterm2" in sys.modules or _importable("iterm2"):
        return sys.executable
    found = glob(str(HOME / "Library/Application Support/iTerm2/iterm2env*/versions/*/bin/python3"))
    for path in sorted(found, key=_version_key, reverse=True):
        probe = subprocess.run([path, "-c", "import iterm2"], capture_output=True)
        if probe.returncode == 0:
            return path
    return None


def _version_key(path):
    parts = Path(path).parent.parent.name.split(".")
    return tuple(int(p) if p.isdigit() else -1 for p in parts)


def _importable(module):
    try:
        __import__(module)
        return True
    except ImportError:
        return False


ITERM_API_SCRIPT = '''
import json, sys, iterm2
wanted = json.loads(sys.argv[1])
check = sys.argv[2] == "check"

async def main(connection):
    for partial in await iterm2.PartialProfile.async_query(connection):
        profile = await partial.async_get_full_profile()
        diff = {k: v for k, v in wanted.items() if profile._simple_get(k) != v}
        if not diff:
            print(f"{profile.name}: already set")
            continue
        if check:
            print(f"{profile.name}: would change {sorted(diff)}")
            continue
        for key, value in diff.items():
            await profile._async_simple_set(key, value)
        print(f"{profile.name}: set {sorted(diff)}")

iterm2.run_until_complete(main)
'''


def warn_if_chezmoi_would_revert(path):
    """A dotfiles manager tracking the prefs is a second source of truth.

    The API write below lands in the running app and, on exit, on disk - but a
    later `chezmoi apply` would put the tracked copy back and undo the font.
    """
    if not (path.exists() and shutil.which("chezmoi")):
        return
    rel = str(path.relative_to(HOME))
    managed = subprocess.run(["chezmoi", "managed"], capture_output=True, text=True)
    if rel not in managed.stdout.split("\n"):
        return
    status = subprocess.run(["chezmoi", "status", str(path)], capture_output=True, text=True)
    if status.stdout.strip():
        say(WARN, "iterm2", f"chezmoi tracks {rel} and its copy differs - run "
                            f"`chezmoi re-add {path}` or the next `chezmoi apply` reverts this")


def apply_iterm(check):
    """Drive the running app over its Python API.

    Editing the prefs file instead only works while iTerm2 is closed - on exit
    it writes its in-memory state back over whatever is on disk.
    """
    if not process_running("iTerm2"):
        say(WARN, "iterm2", "not running - start it and rerun (prefs on disk get overwritten on exit)")
        return
    python = iterm_python()
    if not python:
        say(FAIL, "iterm2", "iterm2 python module not found; enable the Python API in Settings > General > Magic")
        return

    result = subprocess.run(
        [python, "-c", ITERM_API_SCRIPT, json.dumps(ITERM_PROFILE), "check" if check else "apply"],
        capture_output=True, text=True)
    if result.returncode != 0:
        tail = (result.stderr or result.stdout).strip().splitlines()[-1:]
        say(FAIL, "iterm2", f"API call failed: {' '.join(tail)}")
        return
    for line in result.stdout.strip().splitlines():
        say(OK, "iterm2", line)
    apply_iterm_bold(check)
    warn_if_chezmoi_would_revert(ITERM_PREFS)


def apply_iterm_bold(check):
    """Written through `defaults` while the app runs, so it shares the live
    domain; iTerm2 copies that into the custom prefs folder on exit."""
    read = subprocess.run(["defaults", "read", ITERM_DOMAIN, ITERM_BOLD_KEY], capture_output=True, text=True)
    current = read.stdout.strip() if read.returncode == 0 else "(default)"
    if current == str(ITERM_BOLD_DIFF):
        say(OK, "iterm2", f"{ITERM_BOLD_KEY}: already set")
    elif check:
        say(WARN, "iterm2", f"would change {ITERM_BOLD_KEY}: {current} -> {ITERM_BOLD_DIFF}")
    else:
        subprocess.run(["defaults", "write", ITERM_DOMAIN, ITERM_BOLD_KEY, "-int", str(ITERM_BOLD_DIFF)], check=True)
        say(OK, "iterm2", f"set {ITERM_BOLD_KEY}: {current} -> {ITERM_BOLD_DIFF} - restart iTerm2, new windows keep the old bold")


def apply_orca(check):
    """Orca rewrites its data file from memory every few seconds while running."""
    if process_running("Orca"):
        say(WARN, "orca", "running - quit it and rerun, or set it by hand in Settings > Terminal")
        return

    files = sorted(ORCA_PROFILES.glob("*/orca-data.json"))
    if not files:
        say(WARN, "orca", f"no profile under {ORCA_PROFILES}, skipping")
        return

    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        settings = data.setdefault("settings", {})
        diff = {k: v for k, v in ORCA_SETTINGS.items() if settings.get(k) != v}
        if not diff:
            say(OK, "orca", f"{path.parent.name}: already set")
            continue
        if check:
            say(WARN, "orca", f"{path.parent.name}: would change {sorted(diff)}")
            continue
        backup(path)
        settings.update(diff)
        path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        say(OK, "orca", f"{path.parent.name}: set {sorted(diff)}")


APPS = {"vscode": apply_vscode, "iterm2": apply_iterm, "orca": apply_orca}


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("apps", nargs="*", metavar="APP",
                        help=f"any of: {', '.join(APPS)} (default: all)")
    parser.add_argument("--check", action="store_true", help="report without changing anything")
    args = parser.parse_args()

    if sys.platform != "darwin":
        sys.exit("macOS only")

    unknown = [a for a in args.apps if a not in APPS]
    if unknown:
        parser.error(f"unknown app(s): {', '.join(unknown)} - pick from {', '.join(APPS)}")
    selected = args.apps or list(APPS)
    check_fonts()
    for app in selected:
        APPS[app](args.check)

    if "orca" in selected:
        print("\nRestart Orca afterwards: Chromium caches the font family at launch, "
              "so new faces are invisible until it restarts (500 falls back to 400, "
              "600+ to 700).")


main()
