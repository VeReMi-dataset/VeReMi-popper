#!/bin/python
import sys
import csv
import string
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import rcParams
rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['Latin Modern Roman']

high_csv = sys.argv[1]
med_csv = sys.argv[2]
low_csv = sys.argv[3]
speed = sys.argv[4]

if __name__ == "__main__":
  colors = [["#7D9AAA","#A9A280","#56AA1C","#A32638","#26247C","#BD6005"],["#b1c2ca","#c9c6b9","#96ca74","#c77a84","#7a98b0","#d59c69"]]
  font = {'fontname':'Latin Modern Roman'}

  csvs = []
  with open(high_csv) as high, open(med_csv) as med, open(low_csv) as low:

    if speed == "speed":
        labels = ["high","medium","low"]
        x_range = [-1,50]
        x_axis_label = "momentary speed (m/s)"
        filename_hist = "histogram-speed.png"
        filename_box = "boxplot-speed.png"
        bins_resolution = [2.5,1200]
    else:
        labels = ["high","medium","low"]
        x_range = [-50,5000]
        x_axis_label = "reception events"
        filename_hist = "histogram-reception-events.png"
        filename_box = "boxplot-reception-events.png"
        bins_resolution = [2.5,2000]

    csvs.append(high)
    csvs.append(med)
    csvs.append(low)

    data = [ [] for _ in range(0,len(sys.argv)-2)]

    for i in range(0,len(data)):
      reader = csv.reader(csvs[i], delimiter=',')
      for row in reader:
        data[i].append(float(row[0]))


    plt.figure()
    for j in range(0,3):
      
      ax = plt.gca()    
      ax.axes.set_xlim(x_range[0],x_range[1])   
      #ax.axes.set_ylim(0,700)
      plt.hold(True)

      bins = []
      #plt.boxplot(data)
      for i in range(0,bins_resolution[1]):
        bins.append(i*bins_resolution[0])
      
      plt.hist(data[j],bins,alpha = 0.5, color=colors[0][j+2], label = labels[j])

      
    plt.ylabel("amount",**font)
    plt.xlabel(x_axis_label,**font)

    plt.legend()
    plt.savefig(filename_hist,dpi=900)

    plt.figure()
    
    ax = plt.gca()      

    plt.boxplot(data)
    
    #plt.hist(data[j],bins)
    xi = [i for i in range(1, len(data)+1)]
    plt.xticks(xi, [high_csv.split('.')[0],med_csv.split('.')[0],low_csv.split('.')[0]])
    plt.savefig(filename_box,dpi=900)
