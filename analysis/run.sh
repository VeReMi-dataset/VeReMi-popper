#!/bin/sh

#by default, do everything -- set this to false to assume your folders are sub-divided
OVERALL=true

#remove intermediate files? -- by default, no; set to true to enable
REMOVE=false

DOWNLOAD_FOLDER="./download1"
INPUT_FOLDER="./input1"
GT_FOLDER="./with_gt1"
PR_GRAPHS="./graphs1"
WEIGHT_GRAPHS="./weight-graphs1"
GINI_GRAPHS="./gini-graphs1"

if [ "${OVERALL}" = true ]
then
  echo "creating folders"

  mkdir -p ${INPUT_FOLDER} ${GT_FOLDER} ${PR_GRAPHS} ${WEIGHT_GRAPHS} ${GINI_GRAPHS}

  echo "extracting..."
  ./extract.sh ${DOWNLOAD_FOLDER} ${INPUT_FOLDER}

  echo "appending..."
  python3 appendGT.py --source ${INPUT_FOLDER} --destination ${GT_FOLDER}

  if [ "${REMOVE}" = true ]
  then
    echo "removing input folder.."
    rm -r ${INPUT_FOLDER}
  fi

  echo "graphs..."
  python3 overall_precision_recall.py --source ${GT_FOLDER} --destination ${PR_GRAPHS}
  python3 vehicular_weight.py --source ${GT_FOLDER} --destination ${WEIGHT_GRAPHS}
  python3 sim_gini.py --source ${GT_FOLDER} --destination ${GINI_GRAPHS}

else
  echo "subfolders are not yet supported.."
fi


