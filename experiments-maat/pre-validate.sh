#!/bin/sh

# software checks
if ! parallel -V;
then
  echo "parallel -V failed, do you have GNU parallel installed?"
  exit 1
fi

if ! java -jar maat/Maat.jar maat/test.json; 
  echo "Maat failed on test.json, please check corresponding logs"
  exit 1
fi


# input data validation
if ! ls ${HOME}/veins-maat-output;
then
  echo "veins-maat-output could not be read, input data missing..?"
  exit 1
fi

#TODO tgz integrity?

