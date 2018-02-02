#!/usr/bin/python3

import json
import os
from functools import reduce
import itertools
import matplotlib.pyplot as plt
import numpy

import argparse

parser = argparse.ArgumentParser(description='Take result files with ground truth, compute precision and recall, plot for each sim and aggregated.')
parser.add_argument('--source', required=True, help='output of appendGT.py')
parser.add_argument('--destination', required=True, help='folder in which graphs will be stored')

args = parser.parse_args()

inDir = args.source
graphDir = args.destination

if not inDir or not graphDir:
    sys.exit(1)


detectorNames = ["eART", "eSAW", "eMDM", "eDMV"]
# note: one agg color per detector..
aggregateColors = itertools.cycle(('b', 'g')) # , 'r', 'c', 'm', 'y', 'k')

markerList = itertools.cycle(('.', '+', 'o', '*', 'v', '^', '<'))
colorList  = itertools.cycle(('b', 'g', 'r', 'c', 'm', 'y', 'k'))

#parameters that are being studied (should be at most 1 for any detector)
thresholdNames = ["TH", "TH_DISTANCE"]

simulationList = [f for f in os.listdir(inDir) if os.path.isfile(os.path.join(inDir, f)) and f.endswith('.json')]

plotData = []

#result is an array of name, params, result triplet; params is an array of key-value tuples
#we want detector name -> {threshold : (FP,FN,TP,TN))} for different thresholds
def mapToResult(obj):
    results = obj['results']
    mapResult = {}
    for item in results:
        (name, pars, res) = item
    
        if name in detectorNames:
            if not name in mapResult:
                mapResult[name]={}
    
            threshold = None
    
            for par in pars:
                (key, value) = par
                if key in thresholdNames:
                    threshold = value
            if not threshold:
                #this detector does not have the specified parameter, skip it
                continue
            resArray = None
            if res == "FP":
                resArray = (1,0,0,0)
            elif res == "FN":
                resArray = (0,1,0,0)
            elif res == "TP":
                resArray = (0,0,1,0)
            elif res == "TN":
                resArray = (0,0,0,1)
            else:
                print("Warning, unexpected result",item,name)
            mapResult[name][threshold] = resArray
    #endfor -- result item
    return mapResult

def accumulate(acc, item):
    #this assumes that every detector and every threshold occurs for every message
    #TODO insert (0,0,0,0) for missing stuff..?)
    result = {}
    for key in acc:
        result[key]={}
        for thld in acc[key]:
            result[key][thld] = (acc[key][thld][0] + item[key][thld][0],
                                 acc[key][thld][1] + item[key][thld][1],
                                 acc[key][thld][2] + item[key][thld][2],
                                 acc[key][thld][3] + item[key][thld][3])
    return result

def precisionAndRecall(data):
    (FP, FN, TP, TN) = data
    positive = FP + TP
    relevant = TP + FN
    precision = TP/positive
    recall = TP/relevant

    if precision < 0.0 or precision > 1.0:
        print("Warning, bad precision")

    if recall < 0.0 or recall > 1.0:
        print("Warning, bad recall")

    return (precision, recall)

for sim in simulationList:
    attackerType = None
    attackerFraction = None
    runNumber = None
    runID = None
    vehicleCount = None
    simDescription = None

    print("working on",sim)

    inFileName = os.path.join(inDir, sim)
    simResultSet = []
    with open(inFileName, 'r') as inFile:

        first = True
        
        #map
        for line in inFile:

            if first:
                # header

                obj = json.loads(line)

                attackerType = obj['attackerType']
                attackerFraction = obj['attackerFraction']
                runNumber = obj['runNumber']
                runID = obj['runID']
                vehicleCount = obj['vehicleCount']
                simDescription = obj

                first = False
                continue

            obj = json.loads(line)

            mapRes = mapToResult(obj)

            simResultSet.append(mapRes)
    #reduce
    simAccumulate = reduce(accumulate, simResultSet)
    
    #reduces to {NAME -> {thld -> (FP,FN,TP,TN)}}
    for name in simAccumulate:
        for thld in simAccumulate[name]:
            simAccumulate[name][thld] = precisionAndRecall(simAccumulate[name][thld])
    
    for detector in detectorNames:
        print('creating graph for', sim, 'with detector', detector)
        (fig, axes) = plt.subplots(figsize=(10,8))
        axes.set_xlabel("precision")
        axes.set_ylabel("recall")
        axes.set_xlim([0,1])
        axes.set_ylim([0,1])
    
        for threshold in sorted(list(simAccumulate[detector])):
            marker = next(markerList)
            color = next(colorList)
            axes.scatter(simAccumulate[detector][threshold][0], simAccumulate[detector][threshold][1], marker=marker, color=color, label=threshold)
            plotData.append([attackerType, attackerFraction, runNumber, vehicleCount, detector, threshold, simAccumulate[detector][threshold][0], simAccumulate[detector][threshold][1]])


        # Shrink current axis by 20%
        box = axes.get_position()
        axes.set_position([box.x0, box.y0, box.width * 0.8, box.height * 0.9])

        plt.legend(loc='center left', bbox_to_anchor=(1,0.5))
        plt.title(sim + " - " + detector)
    
        plt.savefig(os.path.join(graphDir, sim+ "-" + detector + ".png"), bbox_inces="tight", format='png')
        plt.close()

# plotData contains a list of 8-arrays (attackerType, attackerFraction, runNumber, vehicleCount, detector, threshold, precision, recall)

# TODO here, write some code that to generate specific views on this data.
plotObjects = []

# plot key, (attackerType, attackerFraction) -> lines: key, (name) -> data: key, (thld) -> [precisionArray, recallArray]
newData = {}

for (attackerType, attackerFraction, runNumber, vehicleCount, detector, threshold, precision, recall) in plotData:
    # aggregate runNumber away, discard vehicleCount
    # graph will contain (precision, recall) curve for multiple detectors, drawn in order by threshold (i.e., line plot), which is an aggregate
    # other data (attacker type and fraction of attackers) will be shown in each plot title
    linesObject = newData.setdefault((attackerType, attackerFraction), {})

    thresholds = linesObject.setdefault(detector, {})

    (precisionArray, recallArray) = thresholds.setdefault(threshold, [[], []])

    precisionArray.append(precision)
    recallArray.append(recall)

for (attackerType, attackerFraction) in newData:

    (fig, axes) = plt.subplots(figsize=(10,8))
    axes.set_xlabel("precision")
    axes.set_ylabel("recall")
    axes.set_xlim([0,1])
    axes.set_ylim([0,1])

    title = "Precision-recall with respect to attacker type " + str(attackerType) + " (approx. " + str(attackerFraction) + " attackers)"
    for name in newData[(attackerType, attackerFraction)]:
        label = name
        XY = []
        for threshold in newData[(attackerType, attackerFraction)][name]:
            (precisionArray, recallArray) = newData[(attackerType, attackerFraction)][name][threshold]
            #note: stdev here shows the variation in the *population of samples*, i.e., is a biased estimator of the standard deviation of the underlying normal distribution, if this is normally distributed
            XY.append([numpy.mean(precisionArray), numpy.mean(recallArray), numpy.std(precisionArray), numpy.std(recallArray)])
        (x, y, xerr, yerr) = zip(*XY)
        color = next(aggregateColors)
        axes.errorbar(x, y, xerr=xerr, yerr=yerr, fmt='--o', label=name, color=color)
        minthld = min(newData[(attackerType, attackerFraction)][name].keys())
        maxthld = max(newData[(attackerType, attackerFraction)][name].keys())
        axes.annotate(minthld, xy=(x[0],y[0]), xytext=(x[0]-0.1, y[0]-0.1), arrowprops=dict(facecolor=color, shrink=0.001))
        axes.annotate(maxthld, xy=(x[-1],y[-1]), xytext=(x[-1]-0.1, y[-1]-0.1), arrowprops=dict(facecolor=color, shrink=0.001))

    # Shrink current axis by 20%
    box = axes.get_position()
    axes.set_position([box.x0, box.y0, box.width * 0.8, box.height * 0.9])

    plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.title(title)

    plt.savefig(os.path.join(graphDir, "attacker-" + str(attackerType) + "-frac-" + str(attackerFraction) + ".png"), bbox_inces="tight", format='png')
    plt.close()
