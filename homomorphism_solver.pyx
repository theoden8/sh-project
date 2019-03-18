#!python
#cython: language_level=3
#cython: profile=True
#cython: linetrace=True
#distutils: language=c++


from random import randint
from random import choice
import networkx as nx


from libcpp.vector cimport vector
from libcpp.set cimport set
from libcpp cimport bool


cdef class Solver:
    cdef readonly int UNDEFINED
    cdef readonly int FORWARD
    cdef readonly int BACKTRACK

    cdef object g
    cdef object h
    cdef int no_gnodes
    cdef int no_hnodes
    cdef vector[bool] adjacency_g
    cdef vector[bool] adjacency_h

    cdef int i
    cdef int action
    cdef vector[vector[int]] possibles
    cdef vector[int] g_nodes
    cdef vector[int] hcolor_inds
    cdef vector[int] soln

    # heuristics
    cdef vector[int] error_g
    cdef vector[int] pruned_h

    cdef public int no_solns
    cdef public object solution

    def __init__(self, object g, object h):
        self.UNDEFINED = -1
        self.FORWARD = 0
        self.BACKTRACK = 1

        self.g = g
        self.no_gnodes = len(g.nodes())
        self.adjacency_g = vector[bool](self.no_gnodes ** 2, 0)
        for e in g.edges():
            self.adjacency_g[e[0] * self.no_gnodes + e[1]] = 1
            self.adjacency_g[e[1] * self.no_gnodes + e[0]] = 1

        self.h = h
        self.no_hnodes = len(h.nodes())
        self.adjacency_h = vector[bool](self.no_hnodes ** 2, 0)
        for e in h.edges():
            self.adjacency_h[e[0] * self.no_hnodes + e[1]] = 1
            self.adjacency_h[e[1] * self.no_hnodes + e[0]] = 1

        self.i = 0
        self.possibles = vector[vector[int]](self.no_gnodes, vector[int](self.no_hnodes, 0))
        for i in range(self.no_gnodes):
            for j in range(self.no_hnodes):
                self.possibles[i][j] = j
        self.g_nodes = vector[int](self.no_gnodes, self.UNDEFINED)
        for i in range(self.no_gnodes):
            self.g_nodes[i] = i
        self.hcolor_inds = vector[int](self.no_gnodes, self.UNDEFINED)
        self.soln = vector[int](self.no_gnodes, self.UNDEFINED)
        self.action = self.FORWARD

        self.error_g = vector[int](self.no_gnodes, 0)
        self.pruned_h = vector[int](self.no_hnodes, 0)

        self.no_solns = 0
        self.solution = None

    cdef bool is_last_option(self) nogil:
        cdef int i
        cdef unsigned hcolor
        i = 0 if self.i < 0 else self.i
        hcolor = self.g_nodes[i]
        return self.hcolor_ind() == self.possibles[hcolor].size() - 1

    cdef bool is_valid_option(self, int val=-1) nogil:
        cdef int i
        cdef unsigned hcolor
        i = 0 if self.i < 0 else self.i
        hcolor = self.g_nodes[i]
        if val == -1:
            val = self.hcolor_ind()
        return val >= 0 and val < self.possibles[hcolor].size()

    cdef void forward_node(self, int mapto) nogil:
        cdef int i
        cdef unsigned ind
        cdef unsigned hcolor
        i = 0 if self.i == -1 else self.i
        ind = self.g_nodes[i]
        self.action = self.FORWARD
        self.hcolor_inds[ind] = mapto
        hcolor = self.hcolor_inds[ind]
        self.soln[ind] = self.possibles[ind][hcolor]
        self.i += 1

    cdef void set_rollback(self) nogil:
        cdef int i
        cdef unsigned ind
        i = max(0, self.i)
        ind = self.g_nodes[i]
        self.error_g[ind] += 1
        self.action = self.BACKTRACK
        # self.g_nodes[i] = Solver.UNDEFINED
        self.hcolor_inds[ind] = self.UNDEFINED
        self.soln[ind] = self.UNDEFINED
        self.i -= 1

    cdef int hcolor_ind(self) nogil:
        cdef int i
        i = max(0, self.i)
        return self.hcolor_inds[self.g_nodes[i]]

    cdef inline bool g_has_edge(self, int u, int v) nogil:
        return self.adjacency_g[u * self.no_gnodes + v]

    cdef inline bool h_has_edge(self, int u, int v) nogil:
        return self.adjacency_h[u * self.no_hnodes + v]

    cdef inline int find_possible_map(self) nogil:
        cdef int i, ind, mapto
        i = 0 if self.i < 0 else self.i
        ind = self.g_nodes[i]
        mapto = self.hcolor_ind() + 1
        # print(self.soln)
        while self.is_valid_option(mapto):
            approved = True
            if i > 0:
                gu = ind
                hu = self.possibles[gu][mapto]
                for j in range(i):
                    gv = self.g_nodes[j]
                    hv = self.soln[gv]
                    if self.g_has_edge(gu, gv) and not self.h_has_edge(hu, hv):
                        approved = False
                        self.pruned_h[mapto] += 1
                        break
            if approved:
                break
            mapto += 1
        return mapto

    cdef is_valid_solution(self):
        assert self.i == self.soln.size()
        for e in list(self.g.edges()):
            u, v = e
            hu, hv = self.soln[u], self.soln[v]
            if not self.h_has_edge(hu, hv):
                return False
        return True

    cdef int count_g_neighbors_in_set(self, int node, vector[int] nodes) nogil:
        cdef int ret
        ret = 0
        for out in nodes:
            if self.g_has_edge(node, out):
                ret += 1
        return ret

    cdef int count_h_neighbors_in_set(self, int node, vector[int] nodes) nogil:
        cdef int ret
        ret = 0
        for out in nodes:
            if self.h_has_edge(node, out):
                ret += 1
        return ret

    # heuristics
    cdef choose_best_node(self):
        cdef int option, rating, new_rating, ind
        cdef vector[int] g_nodes_visited
        cdef set[int] visited
        option, rating = -1, -1
        g_nodes_visited = self.g_nodes[:self.i]
        visited = set[int](self.g_nodes[:self.i])
        for ind in range(len(self)):
            if visited.count(ind):
                continue
            new_rating = 0
            new_rating += 100 * self.count_g_neighbors_in_set(ind, g_nodes_visited)
            new_rating += 50 * self.count_h_neighbors_in_set(ind, g_nodes_visited)
            if new_rating > rating:
                option, rating = ind, new_rating
            elif new_rating == rating and self.error_g[ind] > self.error_g[option]:
                option, rating = ind, new_rating
        if option != -1:
            return option
        return self.g_nodes[self.i]

    cdef int choose_target_rating_func(self, int g_ind, int h_ind) nogil:
        cdef int i, target, nb_count, rating
        cdef vector[int] map_image
        i = max(0, self.i)
        target = self.possibles[g_ind][h_ind]
        map_image = vector[int](i)
        for idx in range(i):
            map_image[idx] = self.soln[self.g_nodes[idx]]
        # map_image = [self.soln[idx] for idx in self.g_nodes[:i]]
        rating = 0
        nb_count = self.count_h_neighbors_in_set(target, map_image)
        rating += 10000 * nb_count
        rating += 1000 * (map_image.size() - nb_count)
        rating += self.pruned_h[h_ind]
        return rating

    # heuristics
    cdef void choose_target_order(self):
        cdef int i, g_ind
        i = max(0, self.i)
        g_ind = self.g_nodes[i]
        hcolors = [x for x in self.possibles[g_ind]]
        hcolors.sort(key=lambda h_ind: self.choose_target_rating_func(g_ind, h_ind), reverse=True)
        self.possibles[g_ind] = hcolors
        # print(self.i, [x for x in self.possibles[g_ind]])

    cpdef find_solutions(self, stopfunc):
        while True:
            while self.i in range(len(self)):
                # print(self)
                if self.action == self.FORWARD:
                    # choose g-node
                    self.g_nodes[self.i] = self.choose_best_node()
                    # select order in which h-colors will be tested
                    if self.i + 5 < self.soln.size():
                        self.choose_target_order()
                assert self.i >= -1
                if self.action == self.BACKTRACK and self.hcolor_ind() != self.UNDEFINED:
                    pass
                mapto = self.find_possible_map()
                if self.is_valid_option(mapto):
                    self.forward_node(mapto)
                else:
                    self.set_rollback()
            if self.i < 0:
                break
            # print(self)
            assert self.is_valid_solution()
            if not stopfunc([self.soln[i] for i in range(len(self.soln))]):
                return
            self.i -= 1
            self.action = self.BACKTRACK
        if self.i != -1 and not stopfunc([self.soln[i] for i in range(len(self.soln))]):
            return


    def __str__(self):
        s = 'backtrack' if self.action else 'forward'
        s += ' ' + str(self.i) + ' soln:'
        # s += str([self.hcolor_inds[x] for x in self.g_nodes])
        s += str([self.soln[i] for i in range(len(self.soln))])
        return s

    def __len__(self):
        return self.no_gnodes


def find_homomorphisms(g, h):
    s = Solver(g, h)
    def stopfunc(soln):
        s.no_solns += 1
        return True
    s.find_solutions(stopfunc)
    return s.no_solns

def is_homomorphic(g, h):
    s = Solver(g, h)
    def func(soln):
        s.no_solns = 1
        s.solution = [s.soln[i] for i in range(len(s.soln))]
        return False
    s.find_solutions(stopfunc=func)
    if s.no_solns == 1:
        return s.solution
    return None
