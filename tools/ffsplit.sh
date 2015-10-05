#! /usr/bin/env bash

if [ $# -ne 2 ]; then
    echo "Usage: [INPUT] [SPLITSIZE]"
    exit 1
fi

INPUT=$1
SIZE=$2

if [ ! -e "${INPUT}.wav" ]; then
    echo "WAVE: ${INPUT}.wav not found."
    exit 1
fi

for ((i=0; i < $SIZE; ++i)); do
    dulation=$(($i * 900))
    ffmpeg -i "${INPUT}.wav" -ss $dulation -t 900 "${INPUT}-$i.wav"
done
