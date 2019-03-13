#!python
#cython: language_level=3
#cython: profile=True
#cython: linetrace=True
#distutils: language=c++


from random import randint
from random import choice
import networkx as nx


from libcpp.vector cimport vector
from libcpp cimport bool


cdef class Solver:
    cdef readonly int UNDEFINED
    cdef readonly int FORWARD
    cdef readonly int BACKTRACK

    cdef public object g
    cdef public object h
    cdef public int no_gnodes
    cdef public int no_hnodes
    cdef public vector[bool] adjacency_g
    cdef public vector[bool] adjacency_h

    cdef public int i
    cdef public int action
    cdef public vector[vector[int]] possibles
    cdef public vector[int] srcs
    cdef public vector[int] soln_inds
    cdef public vector[int] soln

    # heuristics
    cdef public vector[int] error_g #
    cdef public vector[int] pruned_h

    cdef int no_solns
    cdef object solution

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
        self.srcs = vector[int](self.no_gnodes, self.UNDEFINED)
        for i in range(self.no_gnodes):
            self.srcs[i] = i
        self.soln_inds = vector[int](self.no_gnodes, self.UNDEFINED)
        self.soln = vector[int](self.no_gnodes, self.UNDEFINED)
        self.action = self.FORWARD

        self.error_g = vector[int](self.no_gnodes, 0)
        self.pruned_h = vector[int](self.no_hnodes, 0)

        self.no_solns = 0
        self.solution = None

    cdef bool is_last_option(self):
        cdef int i
        cdef unsigned hcolor
        i = 0 if self.i < 0 else self.i
        hcolor = self.srcs[i]
        return self.soln_ind() == len(self.possibles[hcolor]) - 1

    cdef bool is_valid_option(self, int val=-1):
        cdef int i
        cdef unsigned hcolor
        i = 0 if self.i < 0 else self.i
        hcolor = self.srcs[i]
        if val == -1:
            val = self.soln_ind()
        return val >= 0 and val < len(self.possibles[hcolor])

    cdef void forward_node(self, int mapto):
        cdef int i
        cdef unsigned ind
        cdef unsigned hcolor
        i = 0 if self.i == -1 else self.i
        ind = self.srcs[i]
        self.action = self.FORWARD
        self.soln_inds[ind] = mapto
        hcolor = self.soln_inds[ind]
        self.soln[ind] = self.possibles[ind][hcolor]
        self.i += 1

    cdef void set_rollback(self):
        cdef int i
        cdef unsigned ind
        i = 0 if self.i == -1 else self.i
        ind = self.srcs[i]
        self.error_g[ind] += 1
        self.action = self.BACKTRACK
        # self.srcs[i] = Solver.UNDEFINED
        self.soln_inds[ind] = self.UNDEFINED
        self.soln[ind] = self.UNDEFINED
        self.i -= 1

    cdef int soln_ind(self):
        cdef int i, ind
        i = 0 if self.i < 0 else self.i
        ind = self.srcs[i]
        return self.soln_inds[ind]

    cdef bool g_has_edge(self, u, v):
        return self.adjacency_g[u * self.no_gnodes + v]

    cdef bool h_has_edge(self, u, v):
        return self.adjacency_h[u * self.no_hnodes + v]

    cdef int find_possible_map(self):
        cdef int i, ind, mapto
        i = 0 if self.i < 0 else self.i
        ind = self.srcs[i]
        mapto = self.soln_ind() + 1
        # print(self.soln)
        while self.is_valid_option(mapto):
            approved = True
            if i > 0:
                gu = ind
                hu = self.possibles[ind][mapto]
                for j in range(i):
                    gv = self.srcs[j]
                    hv = self.soln[gv]
                    if self.g_has_edge(gu, gv) and not self.h_has_edge(hu, hv):
                        approved = False
                        self.pruned_h[mapto] += 1
                        break
            if approved:
                break
            mapto += 1
        return mapto

    cpdef is_valid_solution(self):
        assert self.i == len(self)
        phi = [self.soln[i] for i in range(len(self.soln))]
        for e in list(self.g.edges()):
            u, v = e
            hu, hv = phi[u], phi[v]
            if not self.h_has_edge(hu, hv):
                return False
        return True

    # heuristics
    cpdef choose_best_node(self):
        cdef int option, rating
        option, rating = -1, -1
        srcs_visited = [self.srcs[i] for i in range(self.i)]
        for ind in range(len(self)):
            if ind in srcs_visited:
                continue
            new_rating = 0
            new_rating += 100 * len([nd for nd in list(self.g.neighbors(ind)) if nd in srcs_visited])
            new_rating += 50 * len([nd for nd in list(self.g.neighbors(ind)) if nd not in srcs_visited])
            if new_rating > rating:
                option, rating = ind, new_rating
            elif new_rating == rating and self.error_g[ind] > self.error_g[option]:
                option, rating = ind, new_rating
        if option != -1:
            return option
        return self.srcs[self.i]

    # heuristics
    def choose_target_order(self):
        i = 0 if self.i < 0 else self.i
        ind = self.srcs[i]
        def rating_func(h_ind):
            hnd = self.possibles[ind][h_ind]
            map_image = [self.soln[idx] for idx in self.srcs[:self.i]]
            rating = 0.
            rating += 10000 * len([nb for nb in list(self.h.neighbors(hnd)) if nb in map_image])
            rating += 1000 * len([nb for nb in list(self.h.neighbors(hnd)) if nb not in map_image])
            rating -= self.pruned_h[h_ind]
            return rating
        hcolors = [x for x in self.possibles[ind]]
        hcolors.sort(key=rating_func, reverse=True)
        self.possibles[ind] = hcolors

    cpdef find_solutions(self, stopfunc):
        while True:
            while self.i in range(len(self)):
                # print(self)
                if self.action == self.FORWARD:
                    # choose g-node
                    self.srcs[self.i] = self.choose_best_node()
                    if self.is_last_option():
                        self.set_rollback()
                assert self.i >= -1
                if self.action == self.BACKTRACK and self.soln_ind() != self.UNDEFINED:
                    if self.i < len(self) / 2:
                        # select order in which h-colors will be tested
                        self.choose_target_order()
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
        # s += str([self.soln_ind[x] for x in self.srcs])
        s += str([self.soln[i] for i in range(len(self.soln))])
        return s

    def __len__(self):
        return len(self.soln)


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
