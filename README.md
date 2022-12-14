# Spatial Relation Inference Generator (SpRInG)

A framework for the unsupervised inference of system specifications that characterize the spatial relationships under which robots operate.

## Table of Contents:
- [Getting Started](#getting-started)
- [Usage](#Usage)
  - [Trace](#Trace)
  - [Patterns](#Patterns)
  - [Neighbor Definitions](#neighbor-definitions)
  - [Filtering](#Filtering)
  - [Parameters](#Parameters)
- [Acknowledgements](#Acknowledgements)
## Getting Started:
SpRInG requires Python3 (version 3.7-3.10) and has been tested on Linux and MacOS. First, run the following commands to clone the SpRInG repository and install its requirements:
```
git clone https://github.com/morse165/SpRInG.git
cd SpRInG
./install.sh
```

## Usage:

The only input required by the user is an inputted trace, however we highly recommend the use of the other available parameters.

```
usage: main.py [-h] [--trace TRACE] [--patterns PATTERNS] [--withhold_gen_patterns] [--ndefs DEFINITIONS]
               [--athresh ATHRESH] [--acthresh ACTHRESH] [--classonly] [--tautmodel TAUTMODEL]
               [--start START] [--end END]

optional arguments:
  -h, --help            show this help message and exit
  --trace TRACE         Path to trace file (.json).
  --patterns PATTERNS   Path to patterns file (.json).
  --withhold_gen_patterns
                        Do not generate patterns
  --ndefs DEFINITIONS   Path to entity neighbor definitions file (.json).
  --athresh ATHRESH     Absence threshold.
  --acthresh ACTHRESH   Consecutive absence threshold.
  --classonly           Specify that the neighbor definitions are defined by CLASS (default is by NAME)
  --tautmodel TAUTMODEL
                        Load a tautological model.
  --start START         First desired observation.
  --end END             Last desired observation.
  ```




### Trace

The inputted trace is a JSON file that is structured as a sequence of observations. The key for each observation must be labeled as “T[n]”, where [n] ranges from [0..total_observations]. Each observation contains system state variables (“State”) and entity variables (“Entities”). The entities are labeled as “Entity[m]”, where [m] ranges from [0…total_entities]. Each entity will hold variable-value pairs regarding its current state. It is required for each entity to have a name (*“name”*) and class (*“class”*). Unless otherwise defined by the neighbor definitions file, each entity must also have *“pos_x”* and *“pos_y”* variables to satisfy the default neighbor definitions.

An example is provided below:
```
{
    "T0": {
        "State": {},
        "Entities": {
            "Entity0": {
                "name": “car1”,
                "class": “vehicle”,
		“vel_z”: 2.1
		“pos_x”: 43.2
		“pos_y”: 33.0
            },
            "Entity1”: {
                "name": “car2”,
                "class": “vehicle”,
		“vel_z”: 2.4
		“pos_x”: 86.3
		“pos_y”: 26.6
            },
            "Entity2": {
                "name": “person1”,
                "class": “pedestrian”,
		“vel_z”: 0.6
		“pos_x”: 23.1
		“pos_y”: 14.1
            }
        }
    },
    "T1": {
…
```


### Patterns

The goal of the relation patterns is to provide the basic structure of spatial relations. When complete, they contain tokens (e.g. CONST, NODE1, NODE2) that are later filled during the inference step. The user may elect to provide their own patterns (via a JSON file), have them automatically generated, or a hybrid of the two. Note that patterns are generated by default. Since available information may differ between entities, each entity is entity assigned its own set of patterns. The patterns file must have the following structure:

Each entity contains a hashtable of templates: The key for each entry is of the form ‘TPL_[n]’, where [n] ranges from [0..num_templates]. Each entry contains a dictionary with the following keys:
- Type (“rh_const”, “two_nodes”, “forall”, or “exists”)
- Left Term (“l_term”)
- Operator (“op”)
- Right Term (“r_term”)

An example is provided below:
```
{
“car1”: {
	“TPL_0”:{
		“type”:”rh_const”,
		“l_term”: “graph.nodes[‘NODE1’][‘vel_z’]”
		“op”:”>=“
		“r_term”: “CONST”
	}
	“TPL_1”:{
		“type”:”two_nodes”,
		“l_term”: “nutils.getNeighbors(graph, 'NODE1’)”
		“op”:”>=“
		“r_term”: “nutils.getNeighbors(graph, 'NODE2’)”
	}
}
“Car2”:{
…
```

These templates, whether they are provided by the user or generated, must provide the structure for relations that are consistent with the following grammar:

<img src="./images/grammar.png" width="400" />




### Neighbor Definitions

A neighbor definitions file (*.json*) may be provided by the user, but are otherwise generated by default. For best results, is highly recommended that the user provides the system with their own neighbor definitions. These definitions may be defined for each individual entity (default) or by class (with the flag *“—classonly”*). Each entity name or class will contain a set of neighbor definitions (e.g. AboveNeighbor and BelowNeighbor). The file also includes variable definitions (*"var_defs"*), which are used to relate nodes when first constructing the spatial models. This also requires the variables (*"vars"*) that are required to relate such nodes.

An example is provided below:

```
{
    "robot_manipulator": {
        "AboveNeighbor": "(rel_dist < 0.055) and (rel_z < 0)",
	"BelowNeighbor": "(rel_dist < 0.055) and (rel_z > 0)"
            }
    },
    "tissue": {
        "AboveNeighbor": "(rel_dist < 0.055)"
            }
    },
    "var_defs": {
        "rel_dist": "math.sqrt((NODE1['pos_x'] - NODE2['pos_x'])**2 + (NODE1['pos_x'] - NODE2['pos_x'])**2 + (NODE1['pos_x'] - NODE2['pos_x'])**2)",
        "rel_z": "NODE1['pos_z'] - NODE2['pos_z']"
    },
    "vars": ["pos_x", "pos_y", "pos_z"]
}
```


### Filtering

If the user elects to filter relations based on neighborship distinctions, then they may provide a tautological model for filtering. This model is a JSON file that holds lattice ancestor/descendent relationships for each neighborship distinction. An example is provided below:
```
{
    "lattice": {
        "Neighborhood":[],
        "LeftNeighborhood":["Neighborhood"],
        "RightNeighborhood":["Neighborhood"],
        "FrontNeighborhood":["Neighborhood"],
        "BackNeighborhood":["Neighborhood"],
        "Neighbors":["Neighborhood"],
        "LeftNeighbor":["Neighbors", "Neighborhood", "LeftNeighborhood"],
        "RightNeighbor":["Neighbors", "Neighborhood", "RightNeighborhood"],
        "FrontNeighbor":["Neighbors", "Neighborhood", "FrontNeighborhood"],
        "BackNeighbor":["Neighbors", "Neighborhood", "BackNeighborhood"]
    }
}
```

<img src="./extras/tautmodel2.png" width="800" />


Prior to reporting, the single entity-level predicates and generalized relations are filtered by means of a *tautological model* and through *logical subsumption*. The tautological model of an entity is of the form of a lattice that outlines which classifications of neighborship are contained within one another through \emph{ancestor/descendant relationships}. By default, this model would inform the engine that $ENTITY.Neighbors \subseteq ENTITY.Neighborhood$.

If the user provides complex distinctions between sets of neighbors, it is beneficial for the user to provide the filter with extra context to remove relations that would not be caught by standard logical subsumption. For example, in the traffic scenario, if the user makes the distinction between *Leader*, *Follower*, *Left*, and *Right* neighbors within *All* neighbors, then the implication that $(CAR.LeaderNeighbors.size) \leq (CAR.AllNeighbors.size)$ is tautological, since the former (a *descendant*) is a subset of the latter (an *ancestor*).

For implications of the pattern $(N.Neighbors.size$ $OP$ $CONST)$ $\Rightarrow$ $(N.Neighbors.size$ $OP$ $CONST)$, the filtering step examines restrictions on the predicates that were set by the tautological model. This process is guided by three rules to remove tautological implications. First, if an ancestor is in the antecedent and a descendant is in the consequent (i.e. $Ancestor \Rightarrow Descendant$), both predicates use the same operator $\leq$ as $OP$, and their $CONST$ values are the same, then the implication is removed. Second, if the implication is of the form $Ancestor \Rightarrow Descendant$ and the antecedent has a $CONST$ value of $0$, then it is removed. Third, if the implication has the form $Descendant \Rightarrow Ancestor$, the predicates share the same operator $OP$ (== or $\geq$), and their $CONST$ values are equal but not zero, then it is removed. 

In the traffic scenario, the relation $(CAR.AllNeighbors.size = 0) \Rightarrow (CAR.LeaderNeighbors.size = 0)$ would be removed by the second rule, since the descendant's value is restricted by the ancestor.
Conversely, the relation $(CAR.LeaderNeighbors.size \geq 1) \Rightarrow (CAR.AllNeighbors.size \geq 1)$ would be removed by the third rule, since the ancestor's value is restricted by the descendant.




### Parameters:

The users may set the parameters —athresh and —acthresh to define the proportion of total absences and consecutive absences, consecutively, that are allowed before future absences are counted as failures. The user may also select the start and end observations with the *--start* and *--end* flags, respectively.


## Acknowledgements:
This work was funded in part by NSF Awards #1924777 and AFOSR #FA9550-21-1-0164

