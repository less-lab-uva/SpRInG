from re import L
from tkinter import S
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import math
from itertools import *

# retrieves all entities adjacent to the current node
def getNeighbors(graph, node, rel="default"):
    neighbors = []
    if rel == 'default':
        neighbors = [n for n in graph.neighbors(node)]
    else:
        for n in graph.neighbors(node):
            if graph[node][n]['type'] == rel:
                neighbors.append(n)
    return neighbors

def retrieveNodes(graph, node, rel, tautmodel):
    visited = []
    queue = []
    queue.append(node)
    visited.append(node)
    while queue:
        s = queue.pop(0)
        for i in getNeighbors(graph, s, rel):
            if i not in visited:
                queue.append(i)
                visited.append(i)
    return visited

# runs a BFS on a node to retrieve list of entities in Neighborhood
# entities are retrieved between two depths, min_depth and max_depth
def getNeighborhood(graph, node, rel = "default", tautmodel = None, min_depth = 1, max_depth = 1000):
    neighborhood = []
    if rel == 'default':
        depth = min_depth
        nodes = nx.descendants_at_distance(graph, node, depth)
        while (depth <= max_depth) and len(nodes) > 0:
            neighborhood += nodes
            depth += 1
            nodes = nx.descendants_at_distance(graph, node, depth)
    else:
        neighborhood = retrieveNodes(graph, node, rel, tautmodel)

    if node in neighborhood:
        neighborhood.remove(node)

    return neighborhood
