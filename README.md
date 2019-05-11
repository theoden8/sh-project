# about

This repository contains files related to the SH project called "Graph Homomorphisms".

![homomorphism](/images/homomorphism.png)

# files

* graph_utils.py: simple graph utilities, such as generating, drawing etc

* homomorphism_solver.pyx: mediocre homomorphism solver (rewritten in Cython)

* solve_homomorphism.py: tries to find a homomorphism between two given graphs

* plot_homomorphism.py: generates an image of a given graph homomorphism

* profile_homomorphism.py: generates an overview of python profiling information on the solver

* setup.py: compile homomorphism solver into a shared library

  ---

* generate_small_graphs.py: a script to download a [dataset of graphs][5] and write them into **small_graphs/** folder in g6/json formats

* generate_connected_graph.py: a python program that generates a connected graph of given size and puts it into **graphs/** folder

  ---

* gap_test_solver: compares GAP solver's result with the solver

* gap_homomorphism_finder: uses GAP graph homomorphism finder to find a homomorphism between two graphs

* gap_is_homomorphic_gh: uses GAP solver to print "YES" or "NO" if two graphs are homomorphic

* gap_test_lattice_relations: uses local solver to verify that some randomly chosen relations are correct, and might use GAP solver to provide diagnostics

* test_important_lattice_relations: fully verifies that all important nodes are connected correctly

* gap_find_automorphism_group: uses GAP to find an automorphism group for a graph

* gap_find_cores_automorphisms: uses GAP to list automorphism groups for found cores

  ---

* make_lattice.py: incrementally constructs a partial order graph out of given files, and produces an image

* lattice_utils.py: utilities for lattice operations

* lattice_visualization_utils.py: utilities for visualizing lattice graph


# prerequisites

### setup

For full functionality, you will need:

- **gap**
- **graphviz**

```bash
env python3 -m pip install -r --user requirements.txt
env python3 setup.py build_ext --inplace
# edit gap_config.sh and set GAP=/path/to/gap
```

### usage

#### generating/downloading graphs

```bash
# download small graphs:
./generate_small_graphs.py
# generate some bigger graphs (15 being the size of the graph):
./generate_connected_graph.py 15
# plot a specific graph G
./plot_graph.py <gfile>
# find automorphism group of G
./gap_find_automorphism_group <gfile>
```

#### homomorphism solver

```bash
# use GAP to check if G -> H:
./gap_is_homomorphic_gh <gfile> <hfile>
# use python solver to check if G -> H:
time ./solve_homomorphism.py <gfile> <hfile>
# use python solver that makes use of the lattice interface:
time ./solve_homomorphism_with_lattice.py <gfile> <hfile>
# plot homomorphism G -> H (side by side):
./plot_homomorphism.py <gfile> <hfile>
# profile homomorphism solver G -> H:
./profile_homomorphism.py <gfile> <hfile>
# test the solver:
./gap_test_solver
```

#### lattice

```bash
# make lattice out of given graphs, by specifying graphs in the argument list, e.g.:
./make_lattice.py small_graphs/graph_{1,2,3,4,5}_*.json
# verify relations
./gap_test_lattice_relations
# verify the most important relations
./test_important_lattice_relations
# find automorphism groups of the cores
./gap_find_cores_automorphisms
# open visualization/index.html or visualization/index_d3.html for interactive graph
```



[1]: https://neerc.ifmo.ru/wiki/index.php?title=%D0%A2%D0%B5%D0%BE%D1%80%D0%B8%D1%8F_%D0%B3%D1%80%D0%B0%D1%84%D0%BE%D0%B2
[2]: http://www.lsi.upc.es/~valiente/abs-wsp-1997.pdf
[3]: http://www.math.tu-dresden.de/~bodirsky/Graph-Homomorphisms.pdf
[4]: https://link.springer.com/article/10.1023/A:1008647514949
[5]: http://users.cecs.anu.edu.au/~bdm/data/graphs.htm	"Brendan McKay's combinatorial data: graphs"