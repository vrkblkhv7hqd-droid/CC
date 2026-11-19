#!/bin/bash
# concat lossless chunks -> final H.264 + AAC
set -e
cd "$(dirname "$0")"
OUT=${1:-out.mp4}; CH=${2:-chunks}; BGM=${3:-bgm.wav}; AF=${4:-anull}
ls $CH/seg_*.mkv | sort | sed "s/^/file '/;s/$/'/" > list_$CH.txt
ffmpeg -hide_banner -loglevel error -stats -y -f concat -safe 0 -r 60 -i list_$CH.txt -i "$BGM" \
  -vf "scale=in_range=full:out_range=tv:out_color_matrix=bt709:flags=accurate_rnd+full_chroma_int,format=yuv420p" \
  -c:v libx264 -preset slow -crf 15 -maxrate 24M -bufsize 48M -profile:v high -level 4.2 -g 120 -bf 2 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -af "$AF" -c:a aac -b:a 320k -ar 48000 -movflags +faststart -t 30 "$OUT"
ffprobe -v error -show_entries format=duration,size,bit_rate:stream=codec_name,profile,width,height,r_frame_rate,pix_fmt,nb_frames,sample_rate,channels -of default=nw=1 "$OUT"
