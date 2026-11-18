#!/bin/bash
# install the two brand fonts and copy the weights the film uses
set -e
cd "$(dirname "$0")"
npm install --no-audit --no-fund
mkdir -p film/fonts
for w in 400 500 700 900; do
  cp node_modules/@fontsource/noto-sans-sc/files/noto-sans-sc-chinese-simplified-$w-normal.woff2 film/fonts/
  cp node_modules/@fontsource/noto-sans-sc/files/noto-sans-sc-latin-$w-normal.woff2 film/fonts/
done
for w in 400 500 600 700 800; do
  cp node_modules/@fontsource/manrope/files/manrope-latin-$w-normal.woff2 film/fonts/
done
echo "fonts ready"
