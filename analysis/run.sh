#!/bin/sh

#by default, do everything -- set this to false to assume your folders are sub-divided
OVERALL=true

#remove intermediate files? -- by default, no; set to true to enable
REMOVE=false

DOWNLOAD_FOLDER="./download"
INPUT_FOLDER="./input"
GT_FOLDER="./with_gt"
PR_GRAPHS="./graphs"
WEIGHT_GRAPHS="./weight-graphs"
GINI_GRAPHS="./gini-graphs"

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
  for SUBGROUP_NAME in `ls ${DOWNLOAD_FOLDER}`; do
    mkdir -p ${INPUT_FOLDER}/${SUBGROUP_NAME} ${GT_FOLDER}/${SUBGROUP_NAME} ${PR_GRAPHS}/${SUBGROUP_NAME} ${WEIGHT_GRAPHS}/${SUBGROUP_NAME} ${GINI_GRAPHS}/${SUBGROUP_NAME}

    echo "extracting..."
    ./extract.sh ${DOWNLOAD_FOLDER}/${SUBGROUP_NAME} ${INPUT_FOLDER}/${SUBGROUP_NAME}

    echo "appending..."
    python3 appendGT.py --source ${INPUT_FOLDER}/${SUBGROUP_NAME} --destination ${GT_FOLDER}/${SUBGROUP_NAME}

    if [ "${REMOVE}" = true ]
    then
      echo "removing input folders.."
      rm -r ${INPUT_FOLDER}
    fi

    echo "graphs..."
    python3 overall_precision_recall.py --source ${GT_FOLDER}/${SUBGROUP_NAME} --destination ${PR_GRAPHS}/${SUBGROUP_NAME}
    python3 vehicular_weight.py --source ${GT_FOLDER}/${SUBGROUP_NAME} --destination ${WEIGHT_GRAPHS}/${SUBGROUP_NAME}
    python3 sim_gini.py --source ${GT_FOLDER}/${SUBGROUP_NAME} --destination ${GINI_GRAPHS}/${SUBGROUP_NAME}
  done
fi


