import os
import sys
import subprocess
import pathlib
import math

from networkx.drawing.nx_agraph import graphviz_layout
import cairo

from graph_utils import *
from homomorphism_solver import *


def get_graph_size(gfile):
    fname = os.path.basename(gfile)
    return int(fname.split('_')[1])


def get_graph_id(gfile):
    fname = os.path.basename(gfile).replace('.json', '')
    return int(fname.split('_')[2])


class LatticePathFinder:
    def __init__(self, lattice, nonedges, cores):
        self.lattice = lattice
        if len(cores) == 0:
            self.representatives = [nd for nd in self.lattice.g.nodes() if self.check_representativeness(nd)]
        else:
            self.representatives = cores
        self.core_graph = None
        self.core_graph_c = None
        self.update_core_graph(nonedges)
        for c in cores:
            self.update_representativeness(c)

    def update_core_graph(self, nonedges):
        subgraph = self.lattice.g.subgraph(self.representatives)

        self.core_graph = nx.DiGraph(subgraph.edges())
        self.core_graph.add_nodes_from(self.representatives)

        self.core_graph_c = nx.DiGraph()
        self.core_graph_c.add_nodes_from(self.representatives)
        for a in nonedges:
            a = self.get_equivalent_node(a)
            for b in nonedges[a]:
                b = self.get_equivalent_node(b)
                #if not self.is_known_non_homomorphism(a, b):
                self.core_graph_c.add_edge(a, b)

    def update_representativeness(self, nd):
        should_contain = self.check_representativeness(nd)
        if should_contain and not self.is_representative(nd):
            self.representatives += [nd]

            self.core_graph.add_node(nd)
            for candidate in self.representatives:
                if self.lattice.g.has_edge(candidate, nd):
                    self.core_graph.add_edge(candidate, nd)
                if self.lattice.g.has_edge(nd, candidate):
                    self.core_graph.add_edge(nd, candidate)
            self.core_graph_c.add_node(nd)
        elif not should_contain and self.is_representative(nd):
            index = self.representatives.index(nd)
            del self.representatives[index]
            self.core_graph.remove_node(nd)
            self.core_graph_c.remove_node(nd)

    def get_equivalent_node(self, nd):
        g = self.lattice.g
        if self.is_representative(nd):
            return nd
        for nb in g.neighbors(nd):
            if self.is_representative(nb):
                return nb
        return nd

    def is_representative(self, nd):
        return nd in self.representatives

    def check_representativeness(self, nd):
        g = self.lattice.g
        if g.in_degree(nd) == 0 or g.out_degree(nd) == 0:
            return True
        for nb in g.neighbors(nd):
            if not g.has_edge(nb, nd):
                return True
        for nb in g.predecessors(nd):
            if not g.has_edge(nd, nb):
                return True
        if get_graph_size(nd) == 2:
            return True
        return False

    def is_known_homomorphism(self, a, b):
        a = self.get_equivalent_node(a)
        b = self.get_equivalent_node(b)
        return a == b or self.core_graph.has_edge(a, b) or nx.has_path(self.core_graph, a, b)

    def is_known_non_homomorphism(self, a, b):
        a = self.get_equivalent_node(a)
        b = self.get_equivalent_node(b)
        if a == b:
            return False
        if self.core_graph_c.has_edge(a, b):
            return True
        for nh in self.core_graph_c.neighbors(a):
            if self.is_known_homomorphism(b, nh):
                return True
        return False

    def is_known_relation(self, a, b):
        return self.is_known_homomorphism(a, b) or self.is_known_non_homomorphism(a, b)

    def memoize_relation(self, a, b, relation):
        if self.is_known_relation(a, b):
            return
        a = self.get_equivalent_node(a)
        b = self.get_equivalent_node(b)
        #print('memoized', a, b, relation)
        if relation:
            self.core_graph.add_edge(a, b)
        else:
            self.core_graph_c.add_edge(a, b)

    def normalize_memoization(self, a):
        if self.is_representative(a):
            return
        #print('normalizing', a)
        equiv = self.get_equivalent_node(a)
        if a == equiv:
            return
        if a in self.core_graph.nodes():
            self.core_graph.remove_node(a)
            self.core_graph_c.remove_node(a)

    def has_path(self, a, b):
        # replace nodes with their equivalents
        if self.is_known_homomorphism(a, b):
            return True
        elif self.is_known_non_homomorphism(a, b):
            return False
        raise Exception("unexpected scenareo")
        # a = self.get_equivalent_node(a)
        # b = self.get_equivalent_node(b)
        # return nx.has_path(self.core_graph, a, b)

    def can_remove_edge(self, a, b):
        #print('trying to remove edge', a, b)
        if self.lattice.g.out_degree(a) == 1 or self.lattice.g.in_degree(b) == 1:
            return False
        self.core_graph.remove_edge(a, b)
        result = nx.has_path(self.core_graph, a, b)
        self.core_graph.add_edge(a, b)
        return result
        #for path in nx.all_simple_paths(self.core_graph, a, b):
            #if len(path) > 2:
                ##print('succeeded removing edge')
                #return True
        #return False


class LatticeGraphCache:
    def __init__(self, lattice):
        self.lattice = lattice
        self.cache = {}

    def update(self):
        for fname in list(self.cache.keys()):
            if fname not in self.lattice.path_finder.representatives:
                del self.cache[fname]
        for fname in self.lattice.path_finder.representatives:
            if fname not in self.cache:
                self.cache[fname] = self.load(fname)

    def load(self, fname):
        if fname in self.cache:
            return self.cache[fname]
        return load_graph(fname)


class Lattice:
    def __init__(self, g, nonedges={}, cores=[]):
        self.g = g
        self.path_finder = LatticePathFinder(self, nonedges, cores)
        self.cache = LatticeGraphCache(self)

    @staticmethod
    def load(filename):
        with open(filename, 'r') as f:
            return deserialize_lattice(f.read())

    def add_object(self, filename):
        nodename = filename
        #print()
        print('adding object', nodename)
        nodes = list(self.g.nodes())
        if nodename in nodes:
            print('already exists', nodename)
            return
        self.g.add_node(nodename)
        self.path_finder.update_representativeness(nodename)
        self.cache.update()
        sorted_representatives = sorted(self.path_finder.representatives, key=lambda nd: self.g.degree(nd), reverse=True)
        for other_graph in sorted_representatives:
            if nodename == other_graph:
                continue
            #print('\t<?>', other_graph)
            self.establish_homomorphism(nodename, other_graph)
            self.establish_homomorphism(other_graph, nodename)
            # we found an equivalence to an existing node
            if self.g.has_edge(nodename, other_graph) and self.g.has_edge(other_graph, nodename):
                for nb in list(self.g.neighbors(nodename)):
                    if nb == other_graph:
                        continue
                    self.g.remove_edge(nodename, nb)
                for nb in list(self.g.predecessors(nodename)):
                    if nb == other_graph:
                        continue
                    self.g.remove_edge(nb, nodename)
                self.path_finder.update_representativeness(nodename)
                self.path_finder.normalize_memoization(nodename)
                break

    def is_homomorphic(self, gfile, hfile):
        print('eval %s -> %s' % (gfile, hfile))
        if gfile == hfile:
            return True
        g_known, h_known = gfile in self.g.nodes(), hfile in self.g.nodes()
        if g_known and h_known:
            if self.path_finder.is_known_relation(gfile, hfile):
                return self.path_finder.has_path(gfile, hfile)
        elif g_known and not h_known:
            nonedges = []
            equiv = self.path_finder.get_equivalent_node(equiv)
            if equiv in self.core_graph_c.nodes():
                nonedges = list(self.path_finder.core_graph_c.neighbors(equiv))
            nonedges = [nd for nd in nonedges if get_graph_size(nd) <= get_graph_size(gfile)]
            for nh in nonedges:
                print('test %s -> %s' % (nh, hfile))
                if self.find_homomorphism(nh, hfile) is not None:
                    return False
        elif not g_known and h_known:
            return self.find_homomorphism(gfile, self.path_finder.get_equivalent_node(hfile)) is not None
        else:
            sorted_cores = self.path_finder.representatives
            g_core = None
            for core in sorted_cores:
                gc_result = self.find_homomorphism(gfile, core) is not None
                if gc_result:
                    if g_core is None or self.path_finder.has_path(g_core, core):
                        g_core = core
                        ch_result = self.find_homomorphism(g_core, hfile) is not None
                        if not ch_result:
                            return False
                        hc_result = self.find_homomorphism(hfile, core) is not None
                        if hc_result:
                            return self.is_homomorphic(gfile, core)
            if g_core is not None:
                cg_result = self.find_homomorphism(g_core, gfile) is not None
                if cg_result:
                    return self.is_homomorphic(g_core, hfile)
        print('test %s -> %s' % (gfile, hfile))
        return self.find_homomorphism(gfile, hfile) is not None

    def is_homomorphic_eq(self, gfile, hfile):
        return self.is_homomorphic(gfile, hfile) and self.is_homomorphic(hfile, gfile)

    def find_homomorphism(self, gfile, hfile):
        G, H = self.cache.load(gfile), self.cache.load(hfile)
        return is_homomorphic(G, H)

    def add_edge(self, gfile, hfile):
        #print('add edge', gfile, hfile)
        self.g.add_edge(gfile, hfile)
        if self.g.has_edge(hfile, gfile):
            self.path_finder.update_representativeness(gfile)
            self.path_finder.update_representativeness(hfile)

    def remove_edge(self, gfile, hfile):
        if self.path_finder.can_remove_edge(gfile, hfile):
            self.g.remove_edge(gfile, hfile)
            self.path_finder.update_representativeness(gfile)
            self.path_finder.update_representativeness(hfile)
            #print('\t%s /-> %s' % (gfile, out))

    def establish_homomorphism(self, gfile, hfile):
        if self.path_finder.is_known_relation(gfile, hfile):
            return self.path_finder.has_path(gfile, hfile)

        if not self.path_finder.is_representative(gfile) or not self.path_finder.is_representative(hfile):
            return None
        assert self.path_finder.is_representative(hfile)
        #print('establish homomorphism', gfile, hfile)

        phi = self.find_homomorphism(gfile, hfile)
        if phi is None:
            self.path_finder.memoize_relation(gfile, hfile, False)
            return False
        reach_nodes = [nd for nd in nx.dfs_tree(self.path_finder.core_graph, hfile).nodes()
                       if nd != hfile and self.path_finder.has_path(hfile, nd)]
        self.add_edge(gfile, hfile)
        #print('%s -> %s' % (gfile, hfile))
        for out in reach_nodes:
            if self.g.has_edge(gfile, out):
                self.remove_edge(gfile, out)
        self.path_finder.memoize_relation(gfile, hfile, True)
        return True

    def transitive_reduction(self):
        self.path_finder.core_graph = nx.transitive_reduction(self.path_finder.core_graph)
        for (u, v) in list(self.g.subgraph(self.path_finder.core_graph.nodes()).edges()):
            if not self.path_finder.core_graph.has_edge(u, v):
                self.g.remove_edge(u, v)


def serialize_lattice(lattice):
    j = serialize_graph(lattice.g)
    j['nonedges'] = {
        u : [v for v in lattice.path_finder.core_graph_c.neighbors(u)]
            for u in lattice.path_finder.core_graph_c.nodes()

    }
    j['cores'] = lattice.path_finder.representatives
    return j


def deserialize_lattice(s):
    j = json.loads(s)
    g = deserialize_digraph(json.dumps({'nodes':j['nodes'],'edges':j['edges']}))
    nonedges = j['nonedges']
    cores = j['cores'] if 'cores' in j else []
    return Lattice(g, nonedges, cores)
