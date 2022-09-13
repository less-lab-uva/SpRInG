import numpy as np
import argparse
import math
import matplotlib.pyplot as plt
import networkx as nx
import copy
import json
import itertools
import pickle
import sys
import pylab
import time
from itertools import *
from relation import Relation
from graphfuncs import *
from neighbors import *
from outputfuncs import *
from pattern_generator import *
from infengine import *

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trace', action = 'store', dest='trace', help = 'Path to trace file (.json).')
    parser.add_argument('--patterns', action = 'store', dest='patterns', default = False, help = 'Path to patterns file (.json).')
    parser.add_argument('--withhold_gen_patterns', action = 'store_false', dest='gen_patterns', default=True, help = 'Do not generate patterns')
    parser.add_argument('--ndefs', action = 'store', dest='definitions', default = False, help = 'Path to entity neighbor definitions file (.json).')
    parser.add_argument('--athresh', action = 'store', dest='athresh', default = 1, help = 'Absence threshold.')
    parser.add_argument('--acthresh', action = 'store', dest='acthresh', default = 1, help = 'Consecutive absence threshold.')
    parser.add_argument('--classonly', action = 'store_true', dest='classonly', default = False, help = 'Specify that the neighbor definitions are defined by CLASS (default is by NAME)')
    parser.add_argument('--tautmodel', action = 'store', dest='tautmodel', default=None, help = 'Load a tautological model.')
    parser.add_argument('--start', action = 'store', dest='start', default=None, help = 'First desired observation.')
    parser.add_argument('--end', action = 'store', dest='end', default=None, help = 'Last desired observation.')
    parser.add_argument('--noquant', action = 'store_true', dest='noquant', default = False, help = 'Exclude quantifiers')

    arguments = parser.parse_args()

    quant = False if arguments.noquant else True
    start_time = time.time()

    tautmodel = openJSON(arguments.tautmodel)

    # Get trace and templates
    full_trace = openJSON(arguments.trace)

    start = int(arguments.start) if arguments.start != None else 0
    end = int(arguments.end) if arguments.end != None else len(full_trace)

    trace = {}
    timesteps = list(range(len(full_trace)))[start:end]
    for i in timesteps:
        k = list(full_trace.keys())[i]
        trace[k] = full_trace[k]


    if arguments.definitions:
        neighbor_defs = openJSON(arguments.definitions)
    else:
        neighbor_defs = generateEntityDef(trace, 15)


    vars = computeVars(trace, neighbor_defs, arguments.classonly) #dictionary of variables for each class

    templates = {}
    if arguments.patterns:
        templates.update(openJSON(arguments.patterns))

    if arguments.gen_patterns:
        templates.update(generateTemplates(vars, arguments.classonly, neighbor_defs, tautmodel!=None, len(templates), quant))

    # absence thresholding
    athresh = arguments.athresh * len(trace)
    aconsec_thresh = arguments.acthresh * len(trace)

    pass_thresh = 0
    fail_thresh = 0
    resolve = False
    # run first-pass inference
    relations, node_info, graphs, count, all_evals = inferenceEngine(trace, neighbor_defs, templates, pass_thresh, fail_thresh, athresh, aconsec_thresh, resolve, arguments.trace, tautmodel, arguments.classonly)

    end_time = time.time()

    print("Total time:", str(end_time - start_time))

if __name__ == main():
    main()
