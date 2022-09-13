import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import copy
from itertools import *
from relation import Relation
from graphfuncs import *
from neighbors import *
from outputfuncs import *
from infengine import *

# Automatically generates invariant templates
def generateTemplates(vars, classonly, entityparams, distinction, start_val, quantifiers):
    templates = {}
    operators = ["==", ">=", "<="]
    sep = 'class' if classonly else 'name'

    for entity in vars:

        templates[entity] = {}
        desired = []
        compare = []
        for var in vars[entity]['vars']:
            if var not in entityparams['vars'] and var != 'name' and var != 'class' and var != 'bclass' and var != 'region':
                desired.append(var)
                compare.append(var)


        # compute contructs for each class var
        var_constructs = []
        # for each class, generate a template that includes each of its variables for the left-hand argument and CONST token on the right
        # we don't want to keep "pos", "class", "name", or "detections", since we are strictly using the "==", ">=", and "<=" operators here. And pos is abstracted away.

        for var in desired:
            for op in operators:
                new_construct1 = {"type":"rh_const", "l_term": "graph.nodes['NODE1']" + "['" + var + "']", "op":op, "r_term": "CONST"}
                var_constructs.append(new_construct1)

        for var in compare:
            for op in operators:
                new_construct2 = {"type":"two_nodes", "l_term": "graph.nodes['NODE1']" + "['" + var + "']", "op":op, "r_term": "graph.nodes['NODE2']" + "['" + var + "']"}
                var_constructs.append(new_construct2)


        #constructs eval to true or false
        node_constructs = []
        construct1 = {"type": "rh_const", "l_term": "len(TERM1)", "op":">=", "r_term":"CONST"}
        construct2 = {"type": "rh_const", "l_term": "len(TERM1)", "op":"<=", "r_term":"CONST"}
        construct3 = {"type": "rh_const", "l_term": "len(TERM1)", "op":"==", "r_term":"CONST"}
        construct4 = {"type": "two_nodes", "l_term": "len(TERM1)", "op":">", "r_term":"len(TERM2)"}
        construct5 = {"type": "two_nodes", "l_term": "len(TERM1)", "op":"<", "r_term":"len(TERM2)"}
        construct6 = {"type": "two_nodes", "l_term": "len(TERM1)", "op":"==", "r_term":"len(TERM2)"}
        construct7 = {"type": "two_nodes", "l_term": "set(TERM1)", "op": ".issubset", "r_term": "(set(TERM2))"}
        construct7 = {"type": "two_nodes", "l_term": "set(TERM1)", "op": ".issuperset", "r_term": "(set(TERM2))"}
        construct8 = {"type": "two_nodes", "l_term": "'NODE1'", "op": "in", "r_term":"TERM2"}

        terms2 = []
        terms = []

        if distinction == True:
            for region in vars[entity]['distinctions']:
                terms2.append("nutils.getNeighbors(graph, 'NODE1', '" + region + "')")
                terms2.append("nutils.getNeighborhood(graph, 'NODE1', '" + region + "')")
        else:
            terms2.append("nutils.getNeighbors(graph, 'NODE1')")
            terms2.append("nutils.getNeighborhood(graph, 'NODE1')")

        rh_const_structs = [construct1, construct2, construct3]
        two_node_structs = [construct4, construct5, construct6, construct8]

        count = start_val

        # finalize templates by adding in final terms
        # var constructs are already done, so we can add those
        for st in var_constructs:
            templates[entity]['TPL_' + str(count)] = st
            count += 1

        # one node const
        for st in rh_const_structs:
            for term in terms:
                st_construct = copy.deepcopy(st)
                st_construct["l_term"] = st_construct["l_term"].replace("TERM1", term)
                templates[entity]['TPL_' + str(count)] = st_construct
                count += 1
            if st['op'] == '==':
                for term in terms2:
                    st_construct = copy.deepcopy(st)
                    st_construct["l_term"] = st_construct["l_term"].replace("TERM1", term)
                    templates[entity]['TPL_' + str(count)] = st_construct
                    count += 1

        # two nodes
        for st in two_node_structs:
            cs = permutations(list(range(len(terms))), 2)
            # subset is different because we want to compare between terms (neighbors, formations, neighborhoods) and not just compare two neighbors
            if(st["op"] == ".issubset"):
                for c in cs:
                    st_construct = copy.deepcopy(st)
                    st_construct["l_term"] = st_construct["l_term"].replace("TERM1", terms[c[0]])
                    st_construct["r_term"] = st_construct["r_term"].replace("TERM2", terms[c[1]].replace("NODE1", "NODE2"))
                    templates[entity]['TPL_' + str(count)] = st_construct
                    count += 1
            else:
                for term in terms:
                    st_construct = copy.deepcopy(st)
                    st_construct["l_term"] = st_construct["l_term"].replace("TERM1", term)
                    st_construct["r_term"] = st_construct["r_term"].replace("TERM2", term.replace("NODE1", "NODE2"))
                    templates[entity]['TPL_' + str(count)] = st_construct
                    count += 1
                for term in terms2:
                    st_construct = copy.deepcopy(st)
                    st_construct["l_term"] = st_construct["l_term"].replace("TERM1", term)
                    st_construct["r_term"] = st_construct["r_term"].replace("TERM2", term.replace("NODE1", "NODE2"))
                    templates[entity]['TPL_' + str(count)] = st_construct
                    count += 1

        if quantifiers:
            # quantifiers
            for group in terms2:
                for prop in var_constructs:
                    if prop['type'] == 'rh_const':
                        tmp = {"type": "forall", "alias": "/ALIAS/", "members":'"' + copy.deepcopy(group) + '"', "property": copy.deepcopy(prop)}
                        tmp['property']['l_term'] = tmp['property']['l_term'].replace("NODE1","/ALIAS/")
                        templates[entity]['TPL_' + str(count)] = tmp
                        count += 1

                        tmp2 = {"type": "exists", "alias": "/ALIAS/", "members":'"' + copy.deepcopy(group) + '"', "property": copy.deepcopy(prop)}
                        tmp2['property']['l_term'] = tmp2['property']['l_term'].replace("NODE1","/ALIAS/")
                        templates[entity]['TPL_' + str(count)] = tmp2
                        count += 1

    return templates
