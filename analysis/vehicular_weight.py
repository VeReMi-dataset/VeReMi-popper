#!/usr/bin/python3

import json
import os
from functools import reduce
import itertools
import matplotlib.pyplot as plt
import numpy as np
from gini import gini


inDir = "with_gt"
graphDir = "weight-graphs"

detectorNames = ["eART", "eSAW"]

# TODO uniqueness necessary?
markerList = itertools.cycle(('.', '+', 'o', '*', 'v', '^', '<', '.', '+'))
colorList = itertools.cycle(('b', 'g', 'r', 'c', 'm', 'y', 'k', 'b', 'g'))

# parameter that is being studied (useful for detectors with >1 parameter)
thresholdName = "TH"

simulationList = [f for f in os.listdir(inDir) if os.path.isfile(os.path.join(inDir, f)) and f.endswith('.json')]


# result is an array of name, params, result triplet; params is an array of key-value tuples
# we want detector name -> {threshold : (FP,FN,TP,TN))} for different thresholds
def map_to_result(obj):
    results = obj['results']
    map_result = {}
    for item in results:
        (det_name, pars, res) = item
    
        if det_name in detectorNames:
            if det_name not in map_result:
                map_result[det_name] = {}
    
            parameter_value = None
    
            for par in pars:
                (key, value) = par
                if key == thresholdName:
                    parameter_value = value

            if not thresholdName:
                # this detector does not have the specified parameter, skip it
                continue
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
            map_result[det_name][parameter_value] = res_array
    # end for -- result item
    return map_result


def accumulate(acc, item):
    # this assumes that every detector and every threshold occurs for every message
    # TODO insert (0,0,0,0) for missing stuff..?)
    result = {}
    for key in acc:
        result[key] = {}
        for thld in acc[key]:
            result[key][thld] = (acc[key][thld][0] + item[key][thld][0],
                                 acc[key][thld][1] + item[key][thld][1],
                                 acc[key][thld][2] + item[key][thld][2],
                                 acc[key][thld][3] + item[key][thld][3])
    return result


def precision_and_recall(data):
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


thresholds = {}

for sim in simulationList:
    tmp = sim.split("_")
    attackerType = tmp[0]
    attackerFraction = tmp[1]
    runNumber = tmp[2]

    print("working on", sim)

    inFileName = os.path.join(inDir, sim)
    simResultPerSender = {}
    simResultPerReceiver = {}

    with open(inFileName, 'r') as inFile:
        
        # map
        for line in inFile:
            obj = json.loads(line)

            if not int(obj['senderID']) in simResultPerSender:
                simResultPerSender[int(obj['senderID'])] = []

            if not int(obj['receiverID']) in simResultPerReceiver:
                simResultPerReceiver[int(obj['receiverID'])] = []

            mapRes = map_to_result(obj)

            simResultPerSender[int(obj['senderID'])].append(mapRes)
            simResultPerReceiver[int(obj['receiverID'])].append(mapRes)

    # reduce
    simAccumulateSender = {}
    for sender in simResultPerSender:
        simAccumulateSender[sender] = reduce(accumulate, simResultPerSender[sender])
        # reduces to {sender -> {NAME -> {thld -> (FP,FN,TP,TN)}}}
        for detector_name in simAccumulateSender[sender]:

            if detector_name not in thresholds:
                thresholds[detector_name] = []

            for threshold in simAccumulateSender[sender][detector_name]:
                if threshold not in thresholds[detector_name]:
                    thresholds[detector_name].append(threshold)

                # simAccumulateSender[sender][name][thld] = precisionAndRecall(simAccumulateSender[sender][name][thld])

    #

    simAccumulateReceiver = {}
    for receiver in simResultPerReceiver:
        simAccumulateReceiver[receiver] = reduce(accumulate, simResultPerReceiver[receiver])
        # reduces to {receiver -> {NAME -> {thld -> (FP,FN,TP,TN)}}}
        # for name in simAccumulateReceiver[receiver]:
        #     for thld in simAccumulateReceiver[receiver][name]:
        #         simAccumulateReceiver[receiver][name][thld] = precisionAndRecall(simAccumulateReceiver[receiver][name][thld])

    for detector in detectorNames:
        for threshold in thresholds[detector]:
            print('creating graph for', sim, 'with detector', detector, 'and threshold', threshold)

            legitimateSenderData = []

            attackerSenderData = []

            for sender in simAccumulateSender:
                senderData = simAccumulateSender[sender][detector][threshold]
                (FP, FN, TP, TN) = senderData
                total = FP + FN + TP + TN

                if FP or TN:
                    legitimateSenderData.append((sender, FP+TN, FP/(FP+TN)))
                elif FN or TP:
                    attackerSenderData.append((sender, FN+TP, FN/(FN+TP)))
                else:
                    print("Warning, no messages for", sender, ", please check for errors")

            # sort by FPR/FNR
            legitimateSenderData = sorted(legitimateSenderData, key=lambda item: item[2])
            attackerSenderData = sorted(attackerSenderData, key=lambda item: item[2])

            legitimateSenderX, legitimateSenderTot, legitimateSenderFPR = zip(*legitimateSenderData)

            legitimateSenderFPRCumulative = np.cumsum(legitimateSenderFPR)
            legitimateSenderFPRSum = max(legitimateSenderFPRCumulative)

            attackerSenderX, attackerSenderTot, attackerSenderFNR = zip(*attackerSenderData)

            attackerSenderFNRCumulative = np.cumsum(attackerSenderFNR)
            attackerSenderFNRSum = max(attackerSenderFNRCumulative)

            (_, axes) = plt.subplots(figsize=(10, 8))
            axes.set_xlabel("sender")
            axes.set_ylabel("FPR (" + detector +")")
            axes.set_xlim([0, len(legitimateSenderX)])
            axes.set_ylim([0, legitimateSenderFPRSum])
            #axes.set_ylim([0, max(max(legitimateSenderTot), max(attackerSenderTot))])
            #axes.scatter(range(len(legitimateSenderTot)), legitimateSenderTot, marker='+', color='r')
            axes.scatter(range(len(legitimateSenderFPR)), legitimateSenderFPRCumulative, marker='.', color='k')
            axes.scatter(range(len(legitimateSenderFPR)), [x*(legitimateSenderFPRSum/len(legitimateSenderFPR)) for x in range(len(legitimateSenderFPR))], marker='+', color='r')


            plt.title(sim[:18] + " - " + detector + " - " + str(threshold) + " - legit")
    
            plt.savefig(os.path.join(graphDir, sim + "-" + detector + "-" + str(threshold) + "-legitimate.png"), bbox_inces="tight", format='png')
            plt.close()

            (_, axes) = plt.subplots(figsize=(10, 8))
            axes.set_xlabel("sender")

            axes.set_ylabel("FNR")
            axes.set_xlim([0, len(attackerSenderX)])
            axes.set_ylim([0, attackerSenderFNRSum])
            #axes.scatter(range(len(attackerSenderX)), attackerSenderTot, marker='+', color='r')
            axes.scatter(range(len(attackerSenderX)), attackerSenderFNRCumulative, marker='.', color='k')
            axes.scatter(range(len(attackerSenderX)), [x*(attackerSenderFNRSum/len(attackerSenderFNR)) for x in range(len(attackerSenderX))], marker='+', color='r')

            plt.title(sim[:18] + " - " + detector + " - " + str(threshold) + " - attack")

            plt.savefig(os.path.join(graphDir, sim + "-" + detector + "-" + str(threshold) + "-attacker.png"), bbox_inces="tight", format='png')
            plt.close()
