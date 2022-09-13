import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from itertools import *
from relation import Relation
from graphfuncs import *
from neighbors import *
from pattern_generator import *
from infengine import *

def convertInvariantToString(invariant):
    type = invariant['type']
    left = ""
    right = ""
    str_invariant = ""
    if(type == 'rh_const' or type == 'two_nodes' or type == 'unary'):
        left = invariant["l_term"]
        right = invariant["r_term"]
        str_invariant = left + " " + invariant['op'] + " " + right
    '''
    elif(type == 'imp'):
        if (isinstance(invariant["l_term"], dict)):
            left = "(" + invariant["l_term"]["l_term"] + " " + invariant['l_term']['op'] + " " + invariant["l_term"]["r_term"] + ")"
        if (isinstance(invariant["r_term"], dict)):
            right = "(" + invariant["r_term"]["l_term"] + " " + invariant['r_term']['op'] + " " + invariant["r_term"]["r_term"] + ")"
        if (not isinstance(invariant["l_term"], dict)):
            left = "(" + invariant["l_term"] + ")"
        if (not isinstance(invariant["r_term"], dict)):
            right = invariant["r_term"]
        str_invariant = "not " + left + " or " +  right
    elif(type == 'forall' or 'exists'):
        str_invariant = invariant['type'] + " " + invariant['entities'] + ": " + invariant['property']['l_term'] + " " + invariant['property']['op'] + " " + invariant['property']['r_term']
        str_invariant = str_invariant.replace("getClassMembers(","").replace(", node_info)", "").replace("node_info[NODE][", "").replace("]","")
    '''
    return str_invariant

# removes redundant invariants
def filterInvariants(invariants, thresh):
    newd = {}
    for key in list(invariants.keys()):
        flag = False
        if invariants[key]['type'] == 'forall' or invariants[key]['type'] == 'exists':
            pass
        elif invariants[key]['op'] == ">=" or invariants[key]['op'] == "<=":
            for key2 in list(invariants.keys()):
                if invariants[key2]['type'] == 'forall' or invariants[key2]['type'] == 'exists' or key == key2:
                    continue
                if invariants[key]['l_term'] == invariants[key2]['l_term'] and invariants[key]['r_term'] == invariants[key2]['r_term'] and invariants[key2]['op'] == "==" and invariants[key2]['fail'] == 0:
                    flag = True
                    break
        if flag == False:
            newd[key] = invariants[key]
    return newd


def printInvariants(invariants, node_info):
    # print node info
    for node in node_info:
        node_info[node]["avg_neighbors"] = round(node_info[node]["avg_neighbors"] / node_info[node]['present'], 3)
        node_info[node]["avg_neighborhood"] = round(node_info[node]["avg_neighborhood"] / node_info[node]['present'], 3)
        node_info[node]["avg_formation"] = round(node_info[node]["avg_formation"] / node_info[node]['present'], 3)

    for entity in node_info:
        node = node_info[entity]
        print(entity)
        print("Neighbors: " + str(node['neighbors']).replace("'", ""))
        print("   Min: " + str(node['min_neighbors']) + ", Max: " + str(node['max_neighbors']) + ", Avg: " + str(node['avg_neighbors']))
        print("Neighborhood: " + str(node['neighborhood']).replace("'", ""))
        print("   Min: " + str(node['min_neighborhood']) + ", Max: " + str(node['max_neighborhood']) + ", Avg: " + str(node['avg_neighborhood']))
        print("Formations: " + str(node['formation']).replace("'", ""))
        print("   Min: " + str(node['min_formation']) + ", Max: " + str(node['max_formation']) + ", Avg: " + str(node['avg_formation']))
        print("")
    print("")

    # print all other invariants
    invs = {'Single-Entity': [], 'Double-Entity':[], 'Implication':[], 'Single-Quantifier':[]}
    for inv in invariants:
        # do not report invariant if it failed at any state observation
        if invariants[inv]['fail'] > 0:# or "Formation" in invariants[inv]['string']:
            continue
        invariants[inv]['string'] += ' '
        if invariants[inv]['type'] == 'rh_const':
            if "Formation" in invariants[inv]['string'] or "Neighborhood" in invariants[inv]['string'] or "Neighbors" in invariants[inv]['string']:
                out_string = invariants[inv]['string'].replace('get', '').replace('graph, ','').replace('find','').replace('not ', '').replace(' or ', ' => ').replace("graph.nodes", "").replace('][', '.').replace("'", '').replace('[', '').replace(']','').replace(")0)",")")
                #out_string += "[pass: " + str(invariants[inv]['pass']) + "] " + "[absent: " + str(invariants[inv]['absent']) + "]" + " [uncertainty: " + str(invariants[inv]['uncertain']) + "]"
                invs['Single-Entity'].append(out_string)
        elif invariants[inv]['type'] == 'two_nodes':
            out_string = invariants[inv]['string'].replace('get', '').replace('graph, ','').replace('find','').replace('not ', '').replace(' or ', ' => ').replace("graph.nodes", "").replace('][', '.').replace("'", '').replace('[', '').replace(']','').replace(")0)",")")
            #out_string += "[pass: " + str(invariants[inv]['pass']) + "] " + "[absent: " + str(invariants[inv]['absent']) + "]"+ " [uncertainty: " + str(invariants[inv]['uncertain']) + "]"
            invs['Double-Entity'].append(out_string)
        elif invariants[inv]['type'] == 'imp':
            out_string = invariants[inv]['string'].replace('get', '').replace('graph, ','').replace('find','').replace('not ', '').replace(' or ', ' => ').replace("graph.nodes", "").replace('][', '.').replace("'", '').replace('[', '').replace(']','').replace(")0)",")")
            #out_string += "[both_true: " + str(invariants[inv]['both_true']) + "] " + "[both_false: " + str(invariants[inv]['both_false']) + "]"
            invs['Implication'].append(out_string)
        elif invariants[inv]['type'] == 'forall' or invariants[inv]['type'] == 'exists':
            #out_string = invariants[inv]['string'].replace("][", ".").replace("]","").replace("[","").replace('"',"").replace("forall(", "forall[" + invariants[inv]['class'] + ", " + invariants[inv]['alias'] + "]: ").replace(", " + invariants[inv]['alias'] + "," , "").replace(", node_info)","").replace("exists(", "exists[").replace("node_info", "").replace("'", "")
            out_string = invariants[inv]['string']# + " " + str(invariants[inv]['pass']) + " " + str(invariants[inv]['fail'])
            invs['Single-Quantifier'].append(out_string)

    for cls in invs:
        if len(invs[cls]) > 0:
            invs[cls].sort()
            print("~~ " + cls + " Invariants ~~")
            for j in invs[cls]:
                print(j)
            print("")
