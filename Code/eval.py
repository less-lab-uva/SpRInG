import os
import numpy as np
import argparse
import math
import matplotlib.pyplot as plt
import networkx as nx
import copy
import json
import itertools
import pickle
import pylab
import time
import graphfuncs as gr
from itertools import *
from relation import Relation
from graphfuncs import *
from neighbors import *
from outputfuncs import *
from pattern_generator import *
from infengine import *
lines = []
# compute all unique predicates
with open("../INT_RESULT.txt","w") as outfile:
    for filename in ["RQ1tracesSUMO_Intersectiontrace1.txt", "RQ1tracesSUMO_Intersectiontrace2.txt", "RQ1tracesSUMO_Intersectiontrace3.txt"]:
        with open(os.path.join("../scripts/evals/genpreds_pass", filename), 'r') as f1:
            for line in f1:
                if line not in lines:
                    lines.append(line)
                    outfile.write(line)
        with open(os.path.join("../scripts/evals/genimps_pass", filename), 'r') as f2:
            for line in f2:
                if line not in lines:
                    lines.append(line)
                    outfile.write(line)


tautmodel = openJSON("../RQ1/tautmodel.json")
count = 0
dd = {}
for filename in os.listdir("../RQ1/traces/SUMO_Intersection"):
    if "DS_Store" in filename or "trace" not in filename:
        continue

    trace = openJSON(os.path.join("../RQ1/traces/SUMO_Intersection", filename))
    neighbor_defs = openJSON("../RQ1/entityparams2.json")

    graphs = gr.generateGraphs(trace, neighbor_defs, False, tautmodel, True)
    names = getAllNodeNames(graphs)

    f = open("../INT_RESULT.txt", 'r')
    j = f.readlines()
    for i in range(len(j)):
        line_orig = j[i]
        line = copy.deepcopy(line_orig)
        testline = ""
        if 'implies' in line:
            line = "not (" + line.replace(" implies ", ") or ")

        if "passenger1" in line and "passenger2" in line:
            for pair in list(permutations(list(names), 2)):
                testline = line.replace("passenger1", pair[0])
                testline = testline.replace("passenger2", pair[1])
                if not monitor(trace, neighbor_defs, True, tautmodel, graphs, testline):
                    count += 1
                    dd[line] = False
                    print(testline)
                    break
                testline = ""
        else:
            for n in names:
                testline = line.replace("passenger1", n)
                if not monitor(trace, neighbor_defs, True, tautmodel, graphs, testline):
                    count += 1
                    print(testline)
                    dd[line] = False
                    break
                testline = ""


print("Violated:", len(dd))
f = open("../INT_RESULT.txt", 'r')
j = f.readlines()
print("Total:", len(j))
print(len(dd) / len(j))



'''
tautmodel = openJSON("./tautmodel.json")
d = {}
import copy

l = []
for filename in os.listdir("../SCluster/Expert"):
    if "DS_Store" in filename:
        continue

    d[filename] = 0
    trace = openJSON(os.path.join("../SCluster/Expert", filename))
    neighbor_defs = openJSON("./entityparamsJIGSAWS.json")

    graphs = gr.generateGraphs(trace, neighbor_defs, False, tautmodel, False)

    f = open("./evals/expert_results.txt", 'r')
    flag = True

    j = f.readlines()
    for i in range(len(j)):
        line_orig = j[i]
        line = copy.deepcopy(line_orig)
        if 'implies' in line:
            line = "not (" + line.replace(" implies ", ") or ")

        if not monitor(trace, neighbor_defs, True, tautmodel, graphs, line):
            l.append(line_orig)

f2 = open("./evals/expert_results.txt", 'r')
f3 = open("./exp_final.txt", "w")
for line in f2.readlines():
    if line not in l:
        f3.write(line)
'''


'''
neighbor_defs = openJSON("./entityparamsJIGSAWS.json")
tautmodel = openJSON("./tautmodel.json")
d = {}
out = open("fin_exp_results.txt", 'w')

f = open("./evals/expert_results.txt", 'r')
j = f.readlines()
for i in range(len(j)):
    line = j[i]
    flag = True
    for filename in os.listdir("../SCluster/Expert"):
        if "DS_Store" in filename:
            continue

        trace = openJSON(os.path.join("../SCluster/Expert", filename))
        graphs = gr.generateGraphs(trace, neighbor_defs, False, tautmodel, False)

        if not monitor(trace, neighbor_defs, True, tautmodel, graphs, line) == True:
            flag = False

    if flag == True:
        out.write(line)
'''
