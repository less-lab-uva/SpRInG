import imp
from re import S
import numpy as np
import math
import os
import matplotlib.pyplot as plt
import networkx as nx
import json
import itertools
import copy
from itertools import *
from relation import Relation
from quantrelation import QuantRelation
from implicationrelation import ImplicationRelation
from generalizedrelation import GeneralizedImplicationRelation
from tqdm import tqdm
import graphfuncs as gr
import neighbors as nutils
import outputfuncs as output
import pattern_generator as template

# Loads trace input from user to dictionary
def openJSON(file_path):
    if file_path == None:
        return None
    json_file = open(file_path)
    data = json.load(json_file)
    return data


# initializes node_info dictionary
# nodeinfo contains accumulated node information about each node
# Info about: Node class, accumulated neighbor info, presence, current neighbor/neighborhood/formation info
def initializeNodeInfo(graph, node_info, node):
    info = {"class":graph.nodes[node]['class'],"min_neighbors":math.inf, "max_neighbors":0, "avg_neighbors":0, "min_neighborhood":math.inf, "present":1, "max_neighborhood":0, "avg_neighborhood":0, "min_formation":math.inf, "max_formation":0, "avg_formation":0, "neighbors":nutils.getNeighbors(graph,node), "neighborhood":nutils.getNeighborhood(graph,node)}
    return info


# updates dictionary; marks node as present in current obervation
def updateNodeInfo(info, neighbors, neighborhood):
    if len(neighbors) < info["min_neighbors"]:
        info["min_neighbors"] = len(neighbors)
    elif len(neighbors) > info["max_neighbors"]:
        info["max_neighbors"] = len(neighbors)
    info["avg_neighbors"] += len(neighbors)

    if len(neighborhood) < info["min_neighborhood"]:
        info["min_neighborhood"] = len(neighborhood)
    elif len(neighborhood) > info["max_neighborhood"]:
        info["max_neighborhood"] = len(neighborhood)
    info["avg_neighborhood"] += len(neighborhood)

    info["neighbors"] = list(set(info["neighbors"]).intersection(set(neighbors)))
    info["neighborhood"] = list(set(info["neighborhood"]).intersection(set(neighborhood)))

    # this accumulated "present" value is really only used to compute the average number of neighbors for the node in the output
    info["present"] += 1
    return info



def instantiateRelations(graph, timestep, nodepairs, nodes, count, node_info, templates, tautmodel, se):
    relations, new_evals = {}, {}
    sep = 'class' if se else 'name'
    for node in nodes:
        c = graph.nodes[node]['name']
        for t_id in templates[c]:
            if(templates[c][t_id]['type'] == 'rh_const'):
                template = templates[c][t_id]
                n = [graph.nodes[node]]

                inv = Relation(template, n, count, template['l_term'], template['op'], template['r_term'], timestep)
                inv.setTerms(graph, tautmodel)
                val = 1 if eval(inv.getString()) else -1
                new_evals[inv.getID()] = val
                inv.setEval(timestep, val)
                relations[inv.getID()] = inv
                count += 1
            if(templates[c][t_id]['type'] == 'forall' or templates[c][t_id]['type'] == 'exists'):
                template = templates[c][t_id]
                n = [graph.nodes[node]]
                inv = QuantRelation(template, n, count, graph, template['property']['l_term'], template['property']['op'], template['property']['r_term'], timestep)
                inv.setTerms(graph, tautmodel)
                val = 1 if inv.evaluate(graph, tautmodel) else -1
                new_evals[inv.getID()] = val
                inv.setEval(timestep, val)
                relations[inv.getID()] = inv
                count += 1


    for pair in nodepairs:
        c = graph.nodes[node]['name']
        for t_id in templates[c]:
            if(templates[c][t_id]['type'] == 'two_nodes'):
                template = templates[c][t_id]
                n = [graph.nodes[pair[0]], graph.nodes[pair[1]]]
                inv = Relation(template, n, count, template['l_term'], template['op'], template['r_term'], timestep)
                inv.setTerms(graph, tautmodel)
                val = 1 if eval(inv.getString()) else -1
                new_evals[inv.getID()] = val
                inv.setEval(timestep, val)
                relations[inv.getID()] = inv
                count += 1

    return relations, new_evals, count



def updateRelations(graph, timestep, relations, count, node_info, athresh, acthresh, all_evals, tautmodel):
    #inv_copy = copy.deepcopy(relations)
    idxs = list(relations.keys())
    new_invs = {}
    evals = {}

    existing = []
    existing2 = []
    for x in relations:
        if relations[x].getType() != 'exists' and relations[x].getType() != 'forall':
            existing.append(relations[x].getString())
        else:
            existing2.append(relations[x].getLTerm() + " " + relations[x].getOp() + " " + str(relations[x].getRTerm()))

    # iterate through all relations
    for i in range(len(idxs)):
        idx = idxs[i]

        relation = relations[idx]

        string = relation.getString()
        type = relation.getType()

        absent = False
        # the entity may not be in the world (we try and fail to evaluate the string)... and if so we mark them as temporarily absent

        for node in relation.getNodes():
            if node['name'] not in graph.nodes:
                absent = True

        # if the entity is not in the world, the invariant's status cannot be evaluated
        if absent == True:
            relation.setEval(timestep, 2)

        else:
            # if invariant fails, we either mark it as failed or, if it has const, update it
            if relation.getType() == 'forall' or relation.getType() == 'exists':
                res = relation.evaluate(graph, tautmodel)
            else:
                res = eval(string)
            if not res:
                relation.setEval(timestep, -1)
                evals[idx] = -1

                if type == 'rh_const':
                    # we only want to replicate it one time
                    s = relation.getLTerm() + " " + relation.getOp() + " " + str(eval(relation.getLTerm()))
                    if(relation.isParent() == False and (s not in existing)):
                        new_relation = relation.initChild(graph, timestep, count, tautmodel)

                        relations[new_relation.getID()] = new_relation
                        evals[new_relation.getID()] = 1
                        count += 1

                elif type == 'forall' or type == 'exists':
                    s = relation.getLTerm() + " " + relation.getOp() + " " + str(eval(relation.getLTerm().replace(relation.getToken(), relation.getNodeNames()[0])))
                    if(relation.isParent() == False and (s not in existing2)):
                        new_relation = relation.initChild(graph, timestep, count, tautmodel)

                        relations[new_relation.getID()] = new_relation
                        evals[new_relation.getID()] = 1
                        count += 1

            # otherwise it passes, so add pass
            else:
                if relation.getUncertainty() > 0:
                    relation.setEval(timestep, 0)
                    evals[idx] = 0
                else:
                    relation.setEval(timestep, 1)
                    evals[idx] = 1

    return relations, count, evals, all_evals


# Finds all variables associated with each class
# Returns dictionary: {class: [variables]}
def computeVars(trace, entityparams, classonly):
    vars = {}
    sep = 'class' if classonly else 'name'
    for so in trace:
        for e in trace[so]['Entities']:
            entity = trace[so]["Entities"][e]
            if entity['name'] not in vars:
                vars[entity['name']] = {'vars': [k for k,v in entity.items() if v != None], 'distinctions': list(entityparams[entity[sep]].keys())}
    return vars


'''
def findNewPairings(graph, seen_nodes, seen_pairs):
    new_nodes = []
    old_nodes = []
    for n in list(graph.nodes()):
        if n not in seen_nodes:
            new_nodes.append(n)
            seen_nodes.append(n)
        else:
            old_nodes.append(n)

    all_pairs = []
    # add all pairings between new nodes
    all_pairs += list(permutations(new_nodes, 2))

    # add all pairs between new and old nodes
    pairs = list(itertools.product(new_nodes, old_nodes))
    for p in pairs:
        all_pairs.append(p)
    return new_nodes, all_pairs, seen_nodes, []

'''

def findNewPairings(graph, seen_nodes, seen_pairs):
    new_nodes = []
    new_pairs = []

    for n in list(graph.nodes()):
        if n not in seen_nodes:
            seen_nodes.append(n)
            new_nodes.append(n)

    for p in list(permutations(list(graph.nodes()), 2)):
        if p not in seen_pairs:
            new_pairs.append(p)
            seen_pairs.append(p)

    return new_nodes, new_pairs, seen_nodes, seen_pairs


def generateEntityDef(trace, gendef):
    entities = []
    for so in trace:
        for entity in trace[so]["Entities"]:
            if trace[so]["Entities"][entity]['name'] not in entities:
                entities.append(trace[so]["Entities"][entity]['name'])
    d = {}
    for entity in entities:
        d[entity] = {"params": {"dist": {"val": gendef, "str": "dist < val"}}, "def": "dist"}

    return d


# Updates node information for all nodes in current graph
def updateAllNodes(graph, node_info):
    # for each node in the graph, compute its neighbors, neighborhood, formation
    for node in graph.nodes():
        neighbors = nutils.getNeighbors(graph, node)
        neighborhood = nutils.getNeighborhood(graph,node)

        # set node info
        if node not in node_info:
            node_info[node] = initializeNodeInfo(graph, node_info, node)

        node_info[node] = updateNodeInfo(node_info[node], neighbors, neighborhood)
    return node_info


# Retrieves all members from type or behavioral class
def getClassMembers(cls, node_info, key):
    members = []
    for node in node_info:
        if node_info[node][key] == cls:
            members.append(node)
    return members


# Returns all type or behavioral classes in the trace
def getClasses(node_info, key):
    classlist = []
    for c in node_info:
        if node_info[c][key] not in classlist:
            classlist.append(node_info[c][key])
    return classlist



def clusterEval(node_info, trace_name, gen_imps, tautmodel):
    thresh1s = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
    thresh2s = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]

    arr = np.zeros((len(thresh1s),len(thresh2s)))
    imp_invs_copy = copy.deepcopy(gen_imps)

    name3 = "./cont_failed/" + trace_name.replace("../", "").replace("./","").replace("/", "") + "_FAIL.txt"
    f3 = open(name3, 'w')

    for qq in range(len(thresh1s)):
        thresh1 = thresh1s[qq]
        current1 = {}
        for zz in range(len(thresh2s)):
            thresh2 = thresh2s[zz]
            current = {}

            #print(qq, zz)
            id = trace_name.replace("../", "").replace("./","").replace("/", "")

            name = "./files/" + id + "_" + str(thresh1) + "_" + str(thresh2) + ".txt"
            f = open(name, "w")

            name2 = "./failed/" + id + "_" + str(thresh1) + "_" + str(thresh2) + "_FAIL.txt"
            f2 = open(name2, 'w')

            final_invs = []
            fail_invs = []

            # evaluate each generalized implication
            for imp in imp_invs_copy:
                ret2 = False
                #ret = gen_imp.eval(1, 1, thresh1, thresh2)
                ret2 = filterRelations(imp, tautmodel)
                if True:
                    final_invs.append(imp)
                else:
                    fail_invs.append(imp)

            imp_invs2 = final_invs

            count = 0
            for inv in imp_invs2:
                j = inv.getString()
                if "Formation" not in j and '1.' not in j and '2.' not in j and '0.' not in j and '3.' not in j and '4.' not in j and '5.' not in j and '6.' not in j and '7.' not in j and '8.' not in j and '9.' not in j: #and imp_invs[j]['lscore'] > (imp_invs[j]['rscore'] * 0.9):
                    count += 1
                    f.write(j + "\n")
            f.close()

            if qq == 0 and zz == 0:
                for inv in fail_invs:
                    k = inv.getString()
                    if "Formation" not in k and '1.' not in k and '2.' not in k and '0.' not in k and '3.' not in k and '4.' not in k and '5.' not in k and '6.' not in k and '7.' not in k and '8.' not in k and '9.' not in k: #and imp_invs[j]['lscore'] > (imp_invs[j]['rscore'] * 0.9):
                        f3.write(k + "\n")
                f3.close()

            arr[qq][zz] = count

    print(arr)
    exit(0)
    invariants.update(imp_invs)

    return invariants, node_info, graphs, count


import itertools
def generateImplicationRelations(relations, all_evals, pass_thresh, fail_thresh, count, athresh, acthresh, templates, tautmodel):

    l = list(relations)
    cs = list(permutations(list(range(len(relations))), 2))

    grouping = 'class'
    implications = []
    failimps = []
    #cs = list(itertools.product(antecedents.keys(), consequents.keys()))
    # for each pair...
    print("Generating Implications...")
    for ii in tqdm(range(len(cs))):
        pair = cs[ii]
        if pair[0] == pair[1]:
            continue

        relationA = relations[l[pair[0]]]
        relationB = relations[l[pair[1]]]

        # remove all implication that doesn't include some important spatial abstraction (neighbor/formation/neighborhood)
        if ("Neighbor" not in relationA.getString()) and ("Neighbor" not in relationB.getString()):
            continue

        # if there is no shared entity in implication, generalized form is not helpful so do not report
        n1 = relationA.getNodeNames()
        n2 = relationB.getNodeNames()
        intersection = list(set(n1) & set(n2))
        if len(intersection) == 0:
            continue

        # create implication
        implication = ImplicationRelation(relationA, relationB)

        if implication.getContradiction() == False and implication.getTautologyLeft() == False and implication.getTautologyRight() == False:
            implications.append(implication)
        elif implication.getContradiction() == True:
            failimps.append(implication)

    return implications, failimps



def getPredGeneralForm(relation, grouping):
    s = relation.getString()
    l = {}
    count = 1
    for node in relation.getNodeNames():
        groupname = relation.getEntityInfo()[grouping][node]
        s = s.replace(node, groupname + str(count))
        if groupname in l:
            l[groupname].append(groupname + str(count))
        else:
            l[groupname] = [groupname + str(count)]
        count += 1
    return s, l

def getImpGeneralForm(relationA, relationB, seen_nodes, grouping):
    d = {}
    info = {}

    count = 1
    for node in relationA.getNodeNames():
        if node not in d:
            groupname = relationA.getEntityInfo()[grouping][node]
            d[node] = groupname + str(count)
            if groupname not in info:
                info[groupname] = [d[node]]
            else:
                info[groupname].append(d[node])
            count += 1

    for node in relationB.getNodeNames():
        if node not in d:
            groupname = relationB.getEntityInfo()[grouping][node]
            d[node] = groupname + str(count)
            if groupname not in info:
                info[groupname] = [d[node]]
            else:
                info[groupname].append(d[node])
            count += 1

    newA = relationA.getString()
    newB = relationB.getString()

    for node in d:
        newA = newA.replace(node, d[node])
        newB = newB.replace(node, d[node])
    return newA + " implies " + newB, info, relationA, relationB

def forall(members, token, property, graph):
    spl = property.split(" ")
    l_term = spl[0]
    op = spl[1]
    r_term = spl[2]
    for m in eval(members):
        if not eval(l_term.replace(token, m) + " " + op + " " + r_term):
            return False
    return True

def exists(members, token, property, graph):
    spl = property.split(" ")
    l_term = spl[0]
    op = spl[1]
    r_term = spl[2]
    for m in eval(members):
        if eval(l_term.replace(token, m) + " " + op + " " + r_term):
            return True
    return False

def checkGeneralizations(genimps, genpreds, tautmodel, node_info, trace, neighbor_defs, resolve, graphs):
    f_genimps = {}
    f_genpreds = {}
    f_genimps_fail = {}
    f_genpreds_fail = {}
    print("Checking Generalizations...")

    for j in genpreds:
        flag = True
        for cls in genpreds[j]:
            number = len(genpreds[j][cls])
            members = getClassMembers(cls, node_info, 'class')
            cs = list(itertools.permutations(members,number))
            for pair in cs:
                s = copy.deepcopy(j)
                for entity, repl in zip(pair, genpreds[j][cls]):
                    s = s.replace(repl, entity)

                res = monitor(trace, neighbor_defs, resolve, tautmodel, graphs, s)

                if not res:
                    flag = False
                    f_genpreds_fail[j] = genpreds[j]
                    break

            if flag == True:
                f_genpreds[j] = genpreds[j]
            else:
                break

    for ii in tqdm(range(len(genimps))):
    #for ii in range(len(genimps)):
        flag = True
        g = list(genimps.keys())[ii]
        d = {}
        info = {}
        for cls in genimps[g]['info']:
            number = len(genimps[g]['info'][cls])
            replace_these = genimps[g]['info'][cls]
            members = getClassMembers(cls, node_info, 'class')

            cs = list(itertools.permutations(members,number))
            d[cls] = cs
            info[cls] = {"replace": replace_these, "num":number}

        clss = list(d.keys())
        vals = list(d.values())
        strang = "list(itertools.product("
        for i in range(0, len(d)):
            strang += 'vals[' + str(i) + '], '
        strang = strang[:-2]
        strang += "))"
        all_groupings = eval(strang)

        for group in all_groupings:
            s = copy.deepcopy(g)
            for entities, c in zip(group, clss):
                repl = info[c]["replace"]
                for n, r in zip(entities, repl):
                    s = s.replace(r, n)
            s = "not(" + s.replace(" implies", ") or")
            res = monitor(trace, neighbor_defs, resolve, tautmodel, graphs, s)
            if not res:
                flag = False
                f_genimps_fail[g] = genimps[g]
                break

        if flag == True:
            f_genimps[g] = genimps[g]

    return f_genimps, f_genpreds, f_genimps_fail, f_genpreds_fail





def generalizeRelations(imps, failimps, single_relations, grouping, seen_nodes, seen_pairs, tautmodel):
    general_imps = {}
    general_preds = {}
    print("Generalizing Relations...")
    for i in single_relations:
        relation = single_relations[i]
        type = relation.getType()
        genform, info = getPredGeneralForm(relation, grouping)
        if genform not in general_preds:
            general_preds[genform] = info

    for i in tqdm(range(len(imps))):
        implication = imps[i]
        # add implication to its generalized assignment
        #generalImplication = implication.getGeneralForm(grouping)
        relationA = implication.getLeftRelation()
        relationB = implication.getRightRelation()
        generalImplication = ""
        if relationA.getType() == 'rh_const' or relationB.getType() == 'rh_const':
            generalImplication, info, relA, relB = getImpGeneralForm(relationA, relationB, seen_nodes, grouping)

        if generalImplication not in general_imps and generalImplication != "":
            general_imps[generalImplication] = {"info": info, "relA": relA, "relB":relB}

    return general_imps, general_preds


def filterImplications(imps, tautmodel):
    ret = {}

    for imp in imps:
        valA = ""
        valB = ""
        left = imps[imp]['relA']
        right = imps[imp]['relB']

        for x in tautmodel['lattice']:
            if x in left.getString():
                valA = x
                parentsA = tautmodel['lattice'][x]

            if x in right.getString():
                valB = x
                parentsB = tautmodel['lattice'][x]

        leftOp = left.getOp()
        rightOp = right.getOp()
        s = ""
        if valA != "" and valB != "":
            if (valA in parentsB or valB in parentsA) and (leftOp == rightOp):
                s = str(left.getRTerm()) + " " + right.getOp() + " " + str(right.getRTerm())
            if valA in parentsB and (left.getRTerm() == 0):
                continue
            if s == "" or eval(s):
                continue
        ret[imp] = imps[imp]
    return ret


def filterPreds(gen_preds, tautmodel):
    newg = []
    for g in gen_preds:
        if "Neighbor" in g:
            if "nutils.getNeighbors" in g:
                if g.replace("nutils.getNeighbors", "nutils.getNeighborhood") not in gen_preds:
                    newg.append(g)
            else:
                newg.append(g)
    return newg


def filterRelations(rels, tautmodel):
    imps, gen_imps, preds, gen_preds = rels

    if tautmodel == None:
        return imps, gen_imps, preds, gen_preds

    imps = filterImplications(imps, tautmodel)
    gen_imps = filterImplications(gen_imps, tautmodel)
    gen_preds = filterPreds(gen_preds, tautmodel)

    return imps, gen_imps, preds, gen_preds




def initFilter(relations, tautmodel):
    l = {}
    names = {}

    for r in relations:
        s = relations[r].getString()
        left = str(relations[r].getLTerm())
        right = str(relations[r].getRTerm())

        if relations[r].getType() == 'two_nodes':
            valA = ""
            valB = ""

            for x in tautmodel['lattice']:
                if x in left:
                    valA = x
                    parentsA = tautmodel['lattice'][x]

                if x in right:
                    valB = x
                    parentsB = tautmodel['lattice'][x]

            if valA != "" and valB != "":
                if valA in parentsB and ">" in r.getOp():
                    continue
                if valB in parentsA and "<" in r.getOp():
                    continue

        if '==' in s and (right + " == " + left) in names:
            continue
        elif '==' in s:
            l[r] = relations[r]
            names[s] = relations[r]

        elif '>=' in s:
            if (s.replace(">=", "==") in names):
                name = s.replace(">=", "==")
                if names[name].getAllEvals() == relations[r].getAllEvals():
                    continue

            elif (right + " <= " + left in names):
                name = right + " <= " + left
                if names[name].getAllEvals() == relations[r].getAllEvals():
                    continue

        elif '<=' in s:
            if s.replace("<=", "==") in names:
                name = s.replace("<=", "==")
                if names[name].getAllEvals() == relations[r].getAllEvals():
                    continue
            elif right + " >= " + left in names:
                name = right + " >= " + left
                if names[name].getAllEvals() == relations[r].getAllEvals():
                    continue

        l[r] = relations[r]
        names[s] = relations[r]


    return l


def inferenceEngine(trace, neighbor_defs, templates, pass_thresh, fail_thresh, athresh, acthresh, resolve, trace_name, tautmodel, cls):

    # Step 1: Generate list of neighbor graphs from each of the state observations
    graphs = gr.generateGraphs(trace, neighbor_defs, resolve, tautmodel, cls)
    node_info = {}
    all_evals = {}
    print(graphs[0])
    updateAllNodes(graphs[0], node_info)
    count = 0

    # find all pairs of nodes and all single nodes for invariant generation
    new_nodes, all_pairs, seen_nodes, seen_pairs = findNewPairings(graphs[0], [], [])
    timestep = 0
    # Step 2: Instantiate relations on the first graph
    relations, evals, count = instantiateRelations(graphs[0], timestep, all_pairs, new_nodes, count, node_info, templates, tautmodel, cls)

    # evals = dict of relations and 1/0 for whether or not they passed or failed. This is used for the evidenced implication
    # all_evals = dict of state observations and their associated eval dictionary
    all_evals["0"] = evals

    # Step 3: Iterate through all other graphs and generate neighbor information
    print("Predicate inference...")
    for timestep in tqdm(range(1, len(graphs))):

        graph = graphs[timestep]
        try:
            print(eval("graph.nodes['ego.0']['siren'] == 1"))
            print(eval("nutils.getNeighbors(graph, 'ego.0', 'FrontNeighbor')"))
        except:
            pass
        new_nodes, all_pairs, seen_nodes, seen_pairs = findNewPairings(graph, seen_nodes, seen_pairs)
        node_info = updateAllNodes(graph, node_info)

        # evaluate relations
        relations, count, evals, all_evals = updateRelations(graph, timestep, relations, count, node_info, athresh, acthresh, all_evals, tautmodel)

        new_relations, new_evals, count = instantiateRelations(graph, timestep, all_pairs, new_nodes, count, node_info, templates, tautmodel, cls)

        evals.update(new_evals)
        relations.update(new_relations)

        all_evals[str(timestep)] = evals

        rels = []
        rs = {}
        for q in relations:
            if relations[q].getString() not in rels:
                rels.append(relations[q].getString())
                rs[q] = relations[q]
        relations = rs

    relations = initFilter(relations, tautmodel)

    qu = []
    relations2 = {}
    for r in relations:
        if relations[r].getType() == 'forall':
            qstr = relations[r].getString()
            if qstr not in qu:
                qu.append(qstr)
                relations2[r] = relations[r]

    for r in relations:
        if relations[r].getType() == 'exists':
            qstr = relations[r].getString().replace("exists","forall")
            if qstr not in qu:
                qu.append(qstr)
                relations2[r] = relations[r]

        elif relations[r].getType() != 'forall':
            qstr = relations[r].getString()
            if qstr not in qu:
                qu.append(qstr)
                relations2[r] = relations[r]

    relations3 = {}
    for r in relations2:
        if "nutils.getNeighbors" in relations2[r].getString():
            if relations2[r].getString().replace("nutils.getNeighbors", "nutils.getNeighborhood") not in qu:
                relations3[r] = relations2[r]
        else:
            relations3[r] = relations2[r]

    relations = relations3
    qu2 = []
    relations4 = {}
    for r in relations:
        st = relations[r].getString()
        if '>=' in st and st.replace(">=","==") in qu:
            continue
        elif '<=' in st and st.replace("<=","==") in qu:
            continue
        elif 'forall(' in st and relations[r].getFailed() == 0:
            continue
        else:
            relations4[r] = relations[r]
    relations = relations4

    predicates = {}
    rtrue = {}
    r_false = {}
    failed_preds = {}
    for r in relations:
        if relations[r].getFailed() > 0:
            failed_preds[r] = relations[r]
        if relations[r].getFailed() == 0:
            rtrue[r] = relations[r]
        elif relations[r].getPassed() == 0:
            r_false[r] = relations[r]
        else:
            predicates[r] = relations[r]

    imps, failimps = generateImplicationRelations(predicates, all_evals, pass_thresh, fail_thresh, count, athresh, acthresh, templates, tautmodel)
    init_genimps, init_genrtrue = generalizeRelations(imps, failimps, rtrue, 'class', seen_nodes, seen_pairs, tautmodel)
    gen_imps, gen_rtrue, gen_imps_fail, gen_preds_fail = checkGeneralizations(init_genimps, init_genrtrue, tautmodel, node_info, trace, neighbor_defs, resolve, graphs)

    new_imps = {}
    new_failimps = {}
    for imp in imps:
        new_imps[imp.getString()] = {'relA':imp.getLeftRelation(), 'relB':imp.getRightRelation()}

    for imp in failimps:
        new_failimps[imp.getString()] = {'relA':imp.getLeftRelation(), 'relB':imp.getRightRelation()}

    new_rfalse = {}
    for r in failed_preds:
        new_rfalse[failed_preds[r].getString()] = failed_preds[r]

    new_imps, gen_imps, rtrue, gen_rtrue = filterRelations([new_imps, gen_imps, rtrue, gen_rtrue], tautmodel)


    new_rtrue = {}
    for r in rtrue:
        if "Neighbor" in rtrue[r].getString():
            new_rtrue[rtrue[r].getString()] = rtrue[r]


    writeResults([gen_imps, gen_imps_fail, gen_rtrue, gen_preds_fail, new_imps, new_failimps, new_rtrue, new_rfalse], trace_name)
    print("")
    print("+", str(len(new_rtrue)),"predicates")
    print("+", str(len(new_imps)),"implications")
    print("+", str(len(gen_rtrue)),"generalized predicates")
    print("+", str(len(gen_imps)),"generalized implications")
    print("")


    for r in gen_rtrue:
        print(r)

    exit(0)

    return relations, node_info, graphs, count, all_evals


def writeResults(arrs, trace_name):
    name = trace_name.replace(".","").replace("/","").replace("json","") +".txt"
    dirs = ["genimps_pass", "genimps_fail", "genpreds_pass", "genpreds_fail", "imps_pass","imps_fail", "preds_pass","preds_fail"]
    for dir, arr in zip(dirs, arrs):
        path = "./evals/" + dir + "/"
        if not os.path.exists(path):
            os.makedirs(path)
        f = open(path + name, "w")
        for flin in arr:
            f.write(flin)
            f.write("\n")
        f.close()

def getAllNodeNames(graphs):
    names = []
    for g in graphs:
        for n in g.nodes:
            if n not in names:
                names.append(n)
    return names

def monitor(trace, neighbor_defs, resolve, tautmodel, graphs, rel):
    for timestep in range(0, len(graphs)):
        graph = graphs[timestep]
        try:
            if not eval(rel):
                return False
        except:
            pass
    return True
