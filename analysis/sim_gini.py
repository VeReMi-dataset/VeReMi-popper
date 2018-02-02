#!/usr/bin/python3

import json
import os
import itertools
import matplotlib.pyplot as plt
import numpy
from lib.gini import gini

import argparse

parser = argparse.ArgumentParser(description='Take result files with ground truth, computes gini coefficient for FPR and FNR, plot for each sim, as well as aggregate.')
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

#parameters that are being studied (should be at most 1 for any detector)
thresholdNames = ["TH", "TH_DISTANCE"]

simulationList = [f for f in os.listdir(inDir) if os.path.isfile(os.path.join(inDir, f)) and f.endswith('.json')]

# {detector -> {threshold -> {sim -> (giniFP, giniFN)}}}
gini_plot_data = {}

for sim in simulationList:
    tmp = sim.split("_")
    attackerType = None
    attackerFraction = None
    runNumber = None
    runID = None
    vehicleCount = None
    sim_data = None

    print("working on", sim)

    inFileName = os.path.join(inDir, sim)

    # {detector -> {threshold -> {sender -> [(FP,FN,TP,TN)]}}}
    simResultPerDetector = {}
    for x in detectorNames:
        simResultPerDetector[x] = {}

    with open(inFileName, 'r') as inFile:
        first = True
        # map
        for line in inFile:

            if first:
                # header

                obj = json.loads(line)
                sim_data = obj

                attackerType = obj['attackerType']
                attackerFraction = obj['attackerFraction']
                runNumber = obj['runNumber']
                runID = obj['runID']
                vehicleCount = obj['vehicleCount']

                first = False
                continue

            obj = json.loads(line)

            if 'attackertype' in obj:
                print('duplicate header, please fix your files')

            sender = int(obj['senderID'])

            results = obj['results']

            for item in results:
                (det_name, pars, res) = item
                if det_name not in detectorNames:
                    continue

                # find values for thresholdName
                parameter_value = None

                for par in pars:
                    (key, value) = par
                    if key in thresholdNames:
                        parameter_value = value

                if not parameter_value:
                    # this detector does not have the specified parameter, skip it
                    continue

                # set the detection decision
                res_array = None
                if res == "FP":
                    res_array = (1, 0, 0, 0)
                elif res == "FN":
                    res_array = (0, 1, 0, 0)
                elif res == "TP":
                    res_array = (0, 0, 1, 0)
                elif res == "TN":
                    res_array = (0, 0, 0, 1)
                else:
                    print("Warning, unexpected result", item, det_name)

                # det_name -> parameter_value -> sender -> array of results
                simResultPerDetector.setdefault(det_name, {}).setdefault(parameter_value, {}).setdefault(sender, []).append(res_array)

    # {detector -> {threshold -> {sender -> [(FP,FN,TP,TN)]}}}
    sim_gini = {}

    for det_name in simResultPerDetector:
        for threshold in simResultPerDetector[det_name]:
            data_dict = simResultPerDetector[det_name][threshold]
            FPR_array = []
            FNR_array = []
            for sender in data_dict:
                (FP, FN, TP, TN) = map(sum, zip(*data_dict[sender]))
                if FP+TN > 0:
                    FPR = FP/(FP+TN)
                    FPR_array.append(FPR)
                elif FN+TP > 0:
                    FNR = FN/(FN+TP)
                    FNR_array.append(FNR)
                else:
                    print("Warning, weird things are happening")

            if len(FPR_array) > 0:
                giniFP = gini(numpy.array(FPR_array))
            else:
                giniFP = -1
            if len(FNR_array) > 0:
                giniFN = gini(numpy.array(FNR_array))
            else:
                giniFN = -1

            gini_plot_data.setdefault(det_name, {}).setdefault(threshold, []).append((giniFP, giniFN, sim_data))
            sim_gini.setdefault(det_name, {})[threshold] = (giniFP, giniFN)

    #plot things

    for det_name in sim_gini:
        print('creating graph for', sim, 'with detector', det_name)

        (_, axes) = plt.subplots(figsize=(10, 8))
        axes.set_xlabel("threshold")
        axes.set_ylabel("giniFP")
        axes.set_xlim([0, len(sim_gini[det_name])])
        axes.set_ylim([0, 1])

        x = sorted(sim_gini[det_name].keys())
        yFP = []
        yFN = []
        for item in x:
            giniFP, giniFN = sim_gini[det_name][item]
            yFP.append(giniFP)
            yFN.append(giniFN)
        axes.bar(range(len(x)), yFP, align='center')
        plt.xticks(range(len(x)), list(x))

        plt.title(sim[:18] + " - " + det_name + " - legit")

        plt.savefig(os.path.join(graphDir, sim + "-" + det_name + "-legitimate.png"), bbox_inces="tight", format='png')
        plt.close()

        (_, axes) = plt.subplots(figsize=(10, 8))
        axes.set_xlabel("threshold")
        axes.set_ylabel("giniFN")
        axes.set_xlim([0, len(sim_gini[det_name])])
        axes.set_ylim([0, 1])

        axes.bar(range(len(x)), yFN, align='center')
        plt.xticks(range(len(x)), list(x))

        plt.title(sim[:18] + " - " + det_name + " - attackers")

        plt.savefig(os.path.join(graphDir, sim + "-" + det_name + "-attackers.png"), bbox_inces="tight", format='png')
        plt.close()

for det_name in gini_plot_data:
    print('gini plot for: ' + det_name)

    (_, axes) = plt.subplots(figsize=(10, 8))
    axes.set_xlabel("giniFP")
    axes.set_ylabel("giniFN")
    axes.set_xlim([0, 1])
    axes.set_ylim([0, 1])

    thresholds = sorted(gini_plot_data[det_name].keys())

    label = det_name
    XY=[]
    for threshold in thresholds:
        gini_FP_array, gini_FN_array, _ = zip(*gini_plot_data[det_name][threshold])
        #note: stdev here shows the variation in the *population of samples*, i.e., is a biased estimator of the standard deviation of the underlying normal distribution, if this is normally distributed
        XY.append([numpy.mean(gini_FP_array), numpy.mean(gini_FN_array), numpy.std(gini_FP_array), numpy.std(gini_FN_array)])
    (x, y, xerr, yerr) = zip(*XY)
    color = next(aggregateColors)
    axes.errorbar(x, y, xerr=xerr, yerr=yerr, fmt='--o', label=det_name, color=color)
    minthld = min(gini_plot_data[det_name].keys())
    maxthld = max(gini_plot_data[det_name].keys())
    axes.annotate(minthld, xy=(x[0],y[0]), xytext=(x[0]-0.1, y[0]-0.1), arrowprops=dict(facecolor=color, shrink=0.001))
    axes.annotate(maxthld, xy=(x[-1],y[-1]), xytext=(x[-1]-0.1, y[-1]-0.1), arrowprops=dict(facecolor=color, shrink=0.001))

    plt.savefig(os.path.join(graphDir, det_name + "-gini.png"), bbox_inces="tight", format='png')
    plt.close()


#        label = name
#        XY = []
#        for threshold in newData[(attackerType, attackerFraction)][name]:
#            (precisionArray, recallArray) = newData[(attackerType, attackerFraction)][name][threshold]
#            XY.append([numpy.mean(precisionArray), numpy.mean(recallArray), numpy.std(precisionArray), numpy.std(recallArray)])
#        (x, y, xerr, yerr) = zip(*XY)
#        color = next(aggregateColors)
#        axes.errorbar(x, y, xerr=xerr, yerr=yerr, fmt='--o', label=name, color=color)
#        minthld = min(newData[(attackerType, attackerFraction)][name].keys())
#        maxthld = max(newData[(attackerType, attackerFraction)][name].keys())
#        axes.annotate(minthld, xy=(x[0],y[0]), xytext=(x[0]-0.1, y[0]-0.1), arrowprops=dict(facecolor=color, shrink=0.001))
#        axes.annotate(maxthld, xy=(x[-1],y[-1]), xytext=(x[-1]-0.1, y[-1]-0.1), arrowprops=dict(facecolor=color, shrink=0.001))
