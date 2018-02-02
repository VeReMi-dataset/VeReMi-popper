#!/bin/bash

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <folder-with-tgz-files> <folder to write results to>"
  exit
fi

for x in `ls "$1"`; do
  if [ ${x: -4} == ".tgz" ]; then
    RUN_ID=`basename "$x" .tgz`

    tar --file "$1/${x}" --wildcards --no-anchored --extract results/ --strip-components=7 --one-top-level="$2"/"$RUN_ID" 2>/dev/null

    if [ -f "$2/${RUN_ID}/results/GroundTruthJSONlog.json" ]; then
      mv "$2/${RUN_ID}/results/GroundTruthJSONlog.json" "$2/${RUN_ID}/GroundTruthJSONlog.json"
    fi


    if [ "$?" -eq 0 ]; then
      #success: in the output folder, a set of results was stored, including log files, GT, and simulation description.
      echo "$x successfully extracted"
      cd "$2/$RUN_ID"
      for item in `ls results-*.json`; do
        sed -i 's/de.uulm.vs.autodetect.posverif.//g;s/, SIGMA2=27380.0//g;s/, MAX_UNCERTAINTY=1.0//g;s/SIGMA2=29020.0, //g;s/, SIGMA2=117.0//g;s/THRESHOLD/TH/g;s/DistanceMovedVerifier/eDMV/g;s/Identity::/ID::/g' $item
      done

      cd ../..

    else
      #failure
      echo "Warning, run $RUN_ID (in $1/${x}) failed to run!"
    fi
  fi
done
