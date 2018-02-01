#!/usr/bin/python3

import json

import os

inDir = "input"
outDir = "with_gt"

simulationList = [f for f in os.listdir(inDir) if os.path.isdir(os.path.join(inDir, f))]
print("list of simulation results:", simulationList)

for simName in simulationList:
    simSpecObject = {
        'attackerType': None,
        'attackerFraction': None,
        'runNumber': None,
        'runID': None,
        'vehicleCount': 0,
    }

    print("starting processing of", simName)
    GT = {}
    # messageID-indexed ground truth dictionary
    with open(os.path.join(inDir, simName, 'GroundTruthJSONlog.json'), 'r') as GTFile:
        for line in GTFile:
            GTObject = json.loads(line)
            GT[int(GTObject["messageID"])] = GTObject

    attackerType = None
    attackerFraction = None
    runNumber = None
    vehicleCount = 0

    scaFileName = [f for f in os.listdir(os.path.join(inDir, simName)) if f.endswith('.sca')]
    if scaFileName:
        scaFileName = scaFileName[0]
        # pattern: AttackerTypeX-NUM-#RUNID.sca
        simSpec = scaFileName.split('-')
        singleAttacker = False
        attackerType = simSpec[0][12:]
        if len(simSpec) == 4:
            singleAttacker = True

            attackerFraction = -1 * float(simSpec[2])
            # TODO parse the amount of vehicles from the file?

            runNumber = simSpec[3][1:-4]
        else:
            attackerFraction = float(simSpec[1])
            runNumber = simSpec[2][1:-4]

        with open(os.path.join(inDir, simName, scaFileName), 'r') as scaFile:
            for line in scaFile:
                if not line.startswith('scalar'):
                    pass
                else:
                    vehicle = int(line.split('[')[1].split(']')[0])
                    if vehicleCount < vehicle:
                        vehicleCount = vehicle

            pass
    else:
        print("could not find scalar file for", simName)

    simSpecObject['attackerType'] = attackerType
    simSpecObject['attackerFraction'] = attackerFraction
    simSpecObject['runNumber'] = runNumber
    simSpecObject['runID'] = simName
    simSpecObject['vehicleCount'] = vehicleCount

    # parse vehicleIDs from file names assuming results-XXX.json as structure (default)
    vehicleList = [int(f[8:-5]) for f in os.listdir(os.path.join(inDir, simName)) if
                   os.path.isfile(os.path.join(inDir, simName, f)) and f.startswith('results-') and f.endswith('.json')]
    print(os.listdir(os.path.join(inDir, simName)))
    print(vehicleList)

    outFileName = os.path.join(outDir, str(attackerType) + "_" + str(attackerFraction) + "_" + str(
        runNumber) + "_" + simName + "_with-GT.json")

    # write a JSON object as header that contains the simulation details, so we don't have to rely on file names
    with open(outFileName, 'a') as outFile:
        outFile.write(json.dumps(simSpecObject))
        outFile.write('\n')

    for vehicle in sorted(vehicleList):
        print("in", simName, " -- processing vehicle", vehicle)
        inFileName = os.path.join(inDir, simName, "results-" + str(vehicle) + ".json")
        with open(inFileName, 'r') as inFile, open(outFileName, 'a') as outFile:
            for line in inFile:
                inObj = json.loads(line)
                # inObj["trust"]
                # inObj["time"]
                # inObj["messageID"]
                # inObj["senderID"]
                inObj["receiverID"] = vehicle

                matchingGT = GT[int(inObj["messageID"])]

                newResults = []
                for item in inObj["results"]:
                    if item.startswith("Identity::"):
                        continue
                    (detectorName, params) = item[:-1].split('{')
                    paramKVs = []
                    pars = params.split(', ')
                    for kv in pars:
                        (key, value) = kv.split('=')
                        paramKVs.append((key, float(value)))
                    res = inObj["results"][item]
                    if matchingGT["attackerType"] == 0:
                        # not an attack
                        if res > 0.5:
                            # detection says legitimate -- true negative
                            res = 'TN'
                        else:
                            # detection says attack -- false positive
                            res = 'FP'
                    else:
                        if res > 0.5:
                            # detection says legitimate -- false negative
                            res = 'FN'
                        else:
                            # detection says attack -- true positive
                            res = 'TP'
                    newResults.append((detectorName, paramKVs, res))
                inObj["results"] = newResults

                outFile.write(json.dumps(inObj))
                # automatically converts to newline, see documentation of .write
                outFile.write('\n')
