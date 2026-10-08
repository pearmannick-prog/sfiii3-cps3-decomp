#!/bin/sh
# Full naming and comparison pipeline. usage: tools/pipeline.sh <work dir> <3s-decomp dir> [rounds]
# Expects <work>/sfiii3r1.bin (decrypt.py) and <work>/split-r1 (split.py). Reference objects are built once.
set -e
W=$1; REF=$2; N=${3:-3}; T=$(dirname "$0"); S=$T/../symbols
[ -f $W/ps2_index.json ] || python3 $T/ps2_index.py $REF $W/ps2_index.json
[ -d $W/obj ] || python3 $T/build_ref_sh2.py $REF $W/obj
[ -f $W/ev_ref.json ] || python3 $T/events.py ref $W/obj $W/ev_ref.json
[ -f $W/ev_arc.json ] || python3 $T/events.py arcade $W/sfiii3r1.bin $W/split-r1 $W/ev_arc.json
[ -f $W/content.csv ] || echo "arcade_addr,name,verdict" > $W/content.csv
mkdir -p $W/sem; [ -f $W/sem/feedback.csv ] || echo "arcade_addr,name,verdict" > $W/sem/feedback.csv
i=0
while [ $i -lt $N ]; do
  python3 $T/match.py $W/ps2_index.json $W/split-r1 $W/symbols.csv --content $W/content.csv,$W/sem/feedback.csv --overrides $S/overrides.csv --pins $S/aligned_pins.csv | tail -2
  python3 $T/globals.py $W/ps2_index.json $W/split-r1 $W/symbols.csv $W/data_symbols.csv
  python3 $T/lift_patterns.py $W/sfiii3r1.bin $REF $W/symbols.csv $W/data_symbols.csv $W/lift.csv --split $W/split-r1 --ps2 $W/ps2_index.json --content $W/content.csv | grep -v positions
  python3 $T/ps2_index.py $REF $W/ps2_index_arc.json $T/../src/arcade > /dev/null
  python3 $T/compare.py $W/ps2_index_arc.json $W/split-r1 $W/symbols.csv $W/status.csv
  python3 $T/semdiff.py $W/ev_ref.json $W/ev_arc.json $W/symbols.csv $W/status.csv $W/sem $W/ps2_index.json $W/split-r1
  i=$((i+1))
done
python3 $T/lift_patterns.py $W/sfiii3r1.bin $REF $W/symbols.csv $W/data_symbols.csv $W/lift.csv --emit $T/../src/arcade/generated | tail -1
