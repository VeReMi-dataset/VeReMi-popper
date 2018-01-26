#!/bin/sh

# Dependencies:
#  - SUMO 0.30.0 (tested, higher probably works)
#  - OMNeT++ 5.1.1 (tested, higher might work)
#  - rapidjson (in ~/rapidjson, changeable below)

# TODO install scripts for above tools, or at least check that they exist and run as expected
# see also veins -> jobscript.sh and job.moab for details

#install veins
cd ~
rm -rf veins-maat
git clone veins-maat.git veins-maat # insert URL to public repo here
cd veins-maat
git checkout securecomm2018
module load compiler/gnu #this is cluster-specific, ensuring a recent GCC install

if ./configure --include ~/rapidjson/include && \
  make -j ; then
    echo "successfully compiled veins with rapidjson"
else
    echo "error occurred"
fi
