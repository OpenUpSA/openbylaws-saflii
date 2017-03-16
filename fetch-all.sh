#!/bin/bash

date

for MUNI in \
  CPT \
  ETH \
  JHB \
  ; do
  echo $MUNI
  ./fetch.py --target /data/home/saflii/raw/ZA${MUNI}ByLaws/ --regions za-$MUNI
done
