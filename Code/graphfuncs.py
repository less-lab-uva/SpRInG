import math
import networkx as nx
from tqdm import tqdm
import copy
# Generates graph from state observation and params (list of neighbor definition types)
# Uses params so it knows which edge information to calculate
def generateFCGraph(data, neighbor_params, distinctions, cls):
    G = nx.DiGraph()
    e_data = data["Entities"]
    # if only one entity, add the single node to the graph
    if len(e_data) == 1:
        G.add_node(e_data["Entity0"]["name"])
        return G
    elif len(e_data) == 0:
        return G

    #otherwise, create edges between all pairs of nodes
    for entity1 in e_data.keys():
        for entity2 in e_data.keys():
            if entity1 == entity2:
                continue

            edge_dict = {}
            node1 = e_data[entity1]
            node2 = e_data[entity2]

            for d in neighbor_params['recipes']:
                edge_dict[d] = eval(neighbor_params['recipes'][d].replace("NODE1", "e_data['" + entity1 + "']").replace("NODE2", "e_data['" + entity2 + "']"))

            edge_dict['type'] = None
            G.add_edges_from([(str(node1['name']), str(node2['name']), edge_dict)])

    # fill nodes with state observation data
    for entity in data["Entities"]:
        keys = data["Entities"][entity].keys()
        node = G.nodes[data["Entities"][entity]["name"]]
        for key in keys:
            node[key] = data["Entities"][entity][key]
    return G


def generateNeighborGraph(graph, neighbor_defs, resolve, distinctions, cls):
    arr = {}
    edges = {}
    sep = 'class' if cls else 'name'
    graphcopy = graph.copy()
    for i in range(len(graph.edges())):
        edges[list(graph.edges())[i]] = {}
        edge = edges[list(graph.edges())[i]]
        n1, n2 = list(graph.edges())[i]

        # for each neighbor definition
        for id in neighbor_defs[graph.nodes[n1][sep]]:
            edge[id] = {}
            ndef = copy.deepcopy(neighbor_defs[graph.nodes[n1][sep]][id])
            for keyword in neighbor_defs['recipes']:
                if keyword in ndef:
                    ndef = ndef.replace(keyword, str(graph.get_edge_data(n1, n2)[keyword]))

            if eval(ndef):
                graphcopy.add_edge(n1, n2, type = id)
        # if no neighborhood definition is satisfied, the edge is removed
        if graphcopy.edges[n1, n2]['type'] == None:
            graphcopy.remove_edge(n1, n2)
    return graphcopy


# Generates list of neighbor graphs (one per state observation)
def generateGraphs(trace, neighbor_defs, resolve, tautmodel, cls):
    print("Generating spatial encodings...")
    # generate for each state observation
    observation_keys = list(trace.keys())
    graphs = []
    for i in tqdm(range(len(observation_keys))):
        # generate graph of current state observation
        state_observation = trace[observation_keys[i]]
        fc_graph = generateFCGraph(state_observation, neighbor_defs, tautmodel, cls)

        # apply neighborship definition
        graph = generateNeighborGraph(fc_graph.copy(), neighbor_defs, resolve, tautmodel, cls)
        graphs.append(graph)

    return graphs
