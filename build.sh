#!/bin/sh
set -e
uv run --with fonttools python prep.py
uv run --with fonttools python merge.py
uv run --with fonttools --with skia-pathops python weights.py
echo
echo "Built:"
ls -1 out/
