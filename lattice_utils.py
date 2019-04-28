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
    fname = os.path.basename(gfile).replace('.json', '').replace('.g6', '')
    return int(fname.split('_')[2])


def iterate_edges(dval):
    for k in dval:
        for v in dval[k]:
            yield [k, v]


class LatticePathFinder:
    def __init__(self, lattice, g, nonedges, cores):
        self.lattice = lattice
        self.representatives = cores
        self.repr_set = set(self.representatives)
        # set core graph and its complement
        self.core_graph = g
        self.core_graph_c = nx.DiGraph()
        self.core_graph_c.add_nodes_from(self.representatives)
        self.core_graph_c.add_edges_from(iterate_edges(nonedges))
        # check everything is how it is expected
        for c in cores:
            self.update_representativeness(c)

    def add_representative(self, nd):
        self.representatives += [nd]
        self.repr_set.add(nd)

        self.core_graph.add_node(nd)
        # for rpr in self.representatives:
        #     if self.lattice.g.has_edge(rpr, nd):
        #         self.core_graph.add_edge(rpr, nd)
        #     if self.lattice.g.has_edge(nd, rpr):
        #         self.core_graph.add_edge(nd, rpr)
        self.core_graph_c.add_node(nd)

    def remove_representative(self, nd):
        index = self.representatives.index(nd)
        del self.representatives[index]
        self.repr_set.remove(nd)
        self.core_graph.remove_node(nd)
        self.core_graph_c.remove_node(nd)

    def update_representativeness(self, nd):
        should_contain = self.check_representativeness(nd)
        if should_contain and not self.is_representative(nd):
            self.add_representative(nd)
        elif not should_contain and self.is_representative(nd):
            self.remove_representative(nd)

    def get_equivalent_node(self, nd):
        if self.is_representative(nd):
            return nd
        # for nb in self.lattice.g.neighbors(nd):
        #     if self.is_representative(nb):
        #         return nb
        for rpr in self.representatives:
            if rpr in self.lattice.classes and nd in self.lattice.classes[rpr]:
                return rpr
        return nd

    def is_representative(self, nd):
        return nd in self.repr_set

    def check_representativeness(self, nd):
        if self.core_graph.in_degree(nd) == 0 or self.core_graph.out_degree(nd) == 0:
            return True
        for nb in self.core_graph.neighbors(nd):
            if not self.core_graph.has_edge(nb, nd):
                return True
        for nb in self.core_graph.predecessors(nd):
            if not self.core_graph.has_edge(nd, nb):
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

    def has_path(self, a, b):
        # replace nodes with their equivalents
        if self.is_known_homomorphism(a, b):
            return True
        elif self.is_known_non_homomorphism(a, b):
            return False
        # raise Exception("unexpected scenareo")
        a = self.get_equivalent_node(a)
        b = self.get_equivalent_node(b)
        return nx.has_path(self.core_graph, a, b)

    def can_remove_edge(self, a, b):
        #print('trying to remove edge', a, b)
        if self.core_graph.out_degree(a) == 1 or self.core_graph.in_degree(b) == 1:
            return False
        self.core_graph.remove_edge(a, b)
        result = nx.has_path(self.core_graph, a, b)
        self.core_graph.add_edge(a, b)
        return result

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
    def __init__(self, g=None, nonedges={}, cores=[], classes={}):
        g = nx.DiGraph() if g is None else g
        self.path_finder = LatticePathFinder(self, g, nonedges, cores)
        self.classes = classes
        for k in classes:
            self.classes[k] = set(classes[k])
        self.cache = LatticeGraphCache(self)

    @staticmethod
    def load(filename):
        with open(filename, 'r') as f:
            return deserialize_lattice(f.read())

    def unload(self, filename):
        with open(filename, 'w') as f:
            json.dump(serialize_lattice(self), f)

    def has_node(self, nd):
        for rpr in self.classes:
            if rpr == nd or nd in self.classes[rpr]:
                return True
        return False

    def class_size(self, nd):
        if nd not in self.classes:
            return 1
        return len(self.classes[nd])

    def add_element_to_class(self, rpr, nd):
        if rpr not in self.classes:
            self.classes[rpr] = set()
        self.classes[rpr].add(nd)

    def add_object(self, filename):
        nodename = filename
        #print()
        print('adding object', nodename)
        if self.has_node(nodename):
            print('already exists', nodename)
            return
        self.path_finder.add_representative(nodename)
        self.cache.update()
        sorted_representatives = sorted(self.path_finder.representatives, key=lambda nd: self.class_size(nd), reverse=True)
        for other_graph in sorted_representatives:
            if nodename == other_graph:
                continue
            #print('\t<?>', other_graph)
            self.establish_homomorphism(nodename, other_graph)
            self.establish_homomorphism(other_graph, nodename)
            if self.path_finder.core_graph.has_edge(nodename, other_graph) and self.path_finder.core_graph.has_edge(other_graph, nodename):
                # we found an equivalence to an existing node
                for nb in list(self.path_finder.core_graph.neighbors(nodename)):
                    if nb == other_graph:
                        continue
                    self.path_finder.core_graph.remove_edge(nodename, nb)
                for nb in list(self.path_finder.core_graph.predecessors(nodename)):
                    if nb == other_graph:
                        continue
                    self.path_finder.core_graph.remove_edge(nb, nodename)
                self.path_finder.remove_representative(nodename)
                self.add_element_to_class(other_graph, nodename)
                break

    def is_homomorphic(self, gfile, hfile):
        print('eval %s -> %s' % (gfile, hfile))
        if gfile == hfile:
            return True
        g_known, h_known = self.has_node(gfile), self.has_node(hfile)
        if g_known and h_known:
            if self.path_finder.is_known_relation(gfile, hfile):
                return self.path_finder.is_known_homomorphism(gfile, hfile)
        elif g_known and not h_known:
            nonedges = []
            equiv = self.path_finder.get_equivalent_node(gfile)
            # print('found equivalent', equiv)
            if equiv in self.path_finder.core_graph_c.nodes():
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
            g_core_cand = None
            for core in sorted_cores:
                gc_result = self.find_homomorphism(gfile, core) is not None
                if gc_result and (g_core_cand is None or self.path_finder.has_path(g_core_cand, core)):
                    g_core_cand = core
                    ch_result = self.find_homomorphism(g_core_cand, hfile) is not None
                    if not ch_result:
                        return False
                    hc_result = self.find_homomorphism(hfile, core) is not None
                    if hc_result:
                        return self.is_homomorphic(gfile, core)
            if g_core_cand is not None:
                cg_result = self.find_homomorphism(g_core_cand, gfile) is not None
                if cg_result:
                    return self.is_homomorphic(g_core_cand, hfile)
        print('test %s -> %s' % (gfile, hfile))
        return self.find_homomorphism(gfile, hfile) is not None

    def is_homomorphic_eq(self, gfile, hfile):
        return self.is_homomorphic(gfile, hfile) and self.is_homomorphic(hfile, gfile)

    def find_homomorphism(self, gfile, hfile):
        G, H = self.cache.load(gfile), self.cache.load(hfile)
        return is_homomorphic(G, H)

    def establish_homomorphism(self, gfile, hfile):
        if self.path_finder.is_known_relation(gfile, hfile):
            return self.path_finder.is_known_homomorphism(gfile, hfile)

        if not self.path_finder.is_representative(gfile) or not self.path_finder.is_representative(hfile):
            return None
        assert self.path_finder.is_representative(hfile)
        #print('establish homomorphism', gfile, hfile)

        phi = self.find_homomorphism(gfile, hfile)
        if phi is None:
            self.path_finder.memoize_relation(gfile, hfile, False)
            # self.path_finder.update_representativeness(gfile)
            # self.path_finder.update_representativeness(hfile)
            return False
        # reach_nodes = [nd for nd in nx.dfs_tree(self.path_finder.core_graph, hfile).nodes()
        #                if nd != hfile and self.path_finder.is_known_homomorphism(hfile, nd)]
        # print('%s -> %s' % (gfile, hfile))
        # for out in reach_nodes:
        #     if self.path_finder.core_graph.has_edge(gfile, out) and self.path_finder.can_remove_edge(gfile, out):
        #         self.path_finder.core_graph.remove_edge(gfile, out)
                # self.path_finder.update_representativeness(gfile)
                # self.path_finder.update_representativeness(hfile)
        self.path_finder.memoize_relation(gfile, hfile, True)
        # self.path_finder.update_representativeness(gfile)
        # self.path_finder.update_representativeness(hfile)
        return True

    def transitive_reduction(self):
        self.path_finder.core_graph = nx.transitive_reduction(self.path_finder.core_graph)


def serialize_lattice(lattice):
    j = serialize_graph(lattice.path_finder.core_graph)
    j['nonedges'] = {
        u : [v for v in lattice.path_finder.core_graph_c.neighbors(u)]
            for u in lattice.path_finder.core_graph_c.nodes()
    }
    j['cores'] = lattice.path_finder.representatives
    j['classes'] = lattice.classes
    for k in lattice.classes:
        j['classes'][k] = list(lattice.classes[k])
    return j


def deserialize_lattice(s):
    j = json.loads(s)
    g = deserialize_digraph(json.dumps({'nodes':j['nodes'],'edges':j['edges']}))
    nonedges = j['nonedges']
    cores = j['cores'] if 'cores' in j else []
    classes = j['classes'] if 'classes' in j else {}
    return Lattice(g, nonedges, cores, classes)
