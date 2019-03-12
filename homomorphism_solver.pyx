#!python
#cython: language_level=3
#distutils: language=c++


from random import randint
from random import choice
import networkx as nx


from libcpp.vector cimport vector
from libcpp cimport bool


cdef class Puppet:
    cdef readonly int UNDEFINED
    cdef readonly int FORWARD
    cdef readonly int BACKTRACK

    cdef public int i
    cdef public int action
    cdef public vector[vector[int]] possibles
    cdef public vector[int] srcs
    cdef public vector[int] soln_inds
    cdef public vector[int] soln

    def __init__(self, no_gnodes, no_hnodes):
        self.UNDEFINED = -1
        self.FORWARD = 0
        self.BACKTRACK = 1

        self.i = 0
        self.possibles = vector[vector[int]](no_gnodes, vector[int](no_gnodes, 0))
        for i in range(no_gnodes):
            for j in range(no_hnodes):
                self.possibles[i][j] = j
        self.srcs = vector[int](no_gnodes, self.UNDEFINED)
        for i in range(no_gnodes):
            self.srcs[i] = i
        self.soln_inds = vector[int](no_gnodes, self.UNDEFINED)
        self.soln = vector[int](no_gnodes, self.UNDEFINED)
        self.action = self.FORWARD

    cpdef bool is_last_option(self):
        cdef int i
        cdef unsigned hcolor
        i = 0 if self.i < 0 else self.i
        hcolor = self.srcs[i]
        return self.soln_ind() == len(self.possibles[hcolor]) - 1

    cpdef bool is_valid_option(self, val=-1):
        cdef int i
        cdef unsigned hcolor
        i = 0 if self.i < 0 else self.i
        if val == -1:
            val = self.soln_ind()
        hcolor = self.srcs[i]
        return val in range(len(self.possibles[hcolor]))

    cpdef void forward_node(self, mapto):
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

    cpdef void set_rollback(self):
        cdef int i
        cdef unsigned ind
        i = 0 if self.i == -1 else self.i
        ind = self.srcs[i]
        # self.error_g[ind] += 1
        self.action = self.BACKTRACK
        # self.srcs[i] = Solver.UNDEFINED
        self.soln_inds[ind] = self.UNDEFINED
        self.soln[ind] = self.UNDEFINED
        self.i -= 1

    cpdef int soln_ind(self):
        cdef int i, ind
        i = 0 if self.i < 0 else self.i
        ind = self.srcs[i]
        return self.soln_inds[ind]


class Solver:
    UNDEFINED = -1
    FORWARD, BACKTRACK = range(2)

    def __init__(self, g, h):
        self.g = g
        self.h = h
        # self.possibles = [
        #     # sorted(list(self.h.nodes()), key=lambda x: abs(self.g.degree()[nd] - self.h.degree()[x]))
        #     # shifted(list(h.nodes()), nd)
        #     sorted(list(self.h.nodes()))
        #         for nd in range(len(self.g.nodes()))
        # ]
        # self.srcs = [Solver.UNDEFINED for nd in self.g.nodes()]
        # self.srcs = shuffled(list(range(len(self))))
        # self.srcs = list(range(len(self))) # order in which nodes will be colored
        # self.srcs = sorted(list(self.g.nodes()), key=lambda nd: self.g.degree()[nd], reverse=True)
        # self.soln_inds = [Solver.UNDEFINED for nd in self.g.nodes()] # h-color index within current permutation of possibles
        # self.soln = [Solver.UNDEFINED for nd in self.g.nodes()] # h-color itself
        # self.i = 0 # depth of the recursion
        # self.action = Solver.FORWARD # depth change control indicator
        self.puppet = Puppet(len(list(g.nodes())), len(list(h.nodes())))
        self.no_solns = 0
        self.solution = None
        self.error_g = [0 for nd in self.g.nodes()] # heuristic: how many times we rolled back from a node
        self.pruned_h = [0 for nd in self.h.nodes()] # heuristic: how many times we pruned an h-color off

    def is_valid_solution(self):
        assert self.puppet.i == len(self)
        phi = self.puppet.soln
        for e in list(self.g.edges()):
            u, v = e
            hu, hv = phi[u], phi[v]
            if not self.h.has_edge(hu, hv):
                return False
        return True

    def choose_best_node(self):
        option, rating = -1, -1
        for ind in range(len(self)):
            if ind in self.srcs[:self.i]:
                continue
            new_rating = 0
            new_rating += 100 * len([nd for nd in list(self.g.neighbors(ind)) if nd in self.srcs[:self.i]])
            new_rating += 50 * len([nd for nd in list(self.g.neighbors(ind)) if nd not in self.srcs[:self.i]])
            if new_rating > rating:
                option, rating = ind, new_rating
            elif new_rating == rating and self.error_g[ind] > self.error_g[option]:
                option, rating = ind, new_rating
        if option != -1:
            return option
        return self.srcs[self.i]

    def is_last_option(self):
        return self.puppet.is_last_option()
        # i = 0 if self.i < 0 else self.i
        # return self.soln_ind() == len(self.possibles[self.srcs[i]]) - 1

    def is_valid_option(self, val=None):
        return self.puppet.is_valid_option(val)
        # i = 0 if self.i < 0 else self.i
        # if val is None:
        #     val = self.soln_ind()
        # return val in range(len(self.possibles[self.srcs[i]]))

    def choose_target_order(self):
        i = 0 if self.puppet.i < 0 else self.puppet.i
        ind = self.puppet.srcs[i]
        def rating_func(h_ind):
            hnd = self.puppet.possibles[ind][h_ind]
            srcs_visited = [self.puppet.srcs[idx] for idx in range(self.puppet.i)]
            map_image = [self.puppet.soln[idx] for idx in srcs_visited]
            rating = 0.
            rating += 10000 * len([nb for nb in list(self.h.neighbors(hnd)) if nb in map_image])
            rating += 1000 * len([nb for nb in list(self.h.neighbors(hnd)) if nb not in map_image])
            rating -= self.pruned_h[h_ind]
            return rating
        hcolors = [self.puppet.possibles[ind][i] for i in range(len(self.puppet.possibles[ind]))]
        hcolors = sorted(hcolors, key=rating_func, reverse=True)
        for x in range(len(list(self.h.nodes()))):
            self.puppet.possibles[ind][x] = hcolors[x]
        # self.possibles[ind] = [self.possibles[ind][x] for x in sorted(range(len(self.possibles[ind])), key=rating_func, reverse=True)]

    def find_possible_map(self):
        i = 0 if self.puppet.i < 0 else self.puppet.i
        ind = self.puppet.srcs[i]
        mapto = self.puppet.soln_ind() + 1
        # print(self.soln)
        while self.is_valid_option(mapto):
            approved = True
            if i > 0:
                gu = ind
                hu = self.puppet.possibles[ind][mapto]
                for j in range(i):
                    gv = self.puppet.srcs[j]
                    hv = self.puppet.soln[gv]
                    if self.g.has_edge(gu, gv) and not self.h.has_edge(hu, hv):
                        approved = False
                        # self.pruned_h[mapto] += 1
                        break
            if approved:
                break
            mapto += 1
        return mapto

    def forward_node(self, mapto):
        self.puppet.forward_node(mapto)
        # i = 0 if self.i == -1 else self.i
        # ind = self.srcs[i]
        # self.action = Solver.FORWARD
        # self.soln_inds[ind] = mapto
        # self.soln[ind] = self.possibles[ind][self.soln_inds[ind]]
        # self.i += 1

    def set_rollback(self):
        self.puppet.set_rollback()
        i = 0 if self.i == -1 else self.i
        ind = self.srcs[i]
        self.error_g[ind] += 1
        # self.action = Solver.BACKTRACK
        # # self.srcs[i] = Solver.UNDEFINED
        # self.soln_inds[ind] = Solver.UNDEFINED
        # self.soln[ind] = Solver.UNDEFINED
        # self.i -= 1

    def soln_ind(self):
        return self.puppet.soln_ind()
        # i = 0 if self.i < 0 else self.i
        # ind = self.srcs[i]
        # return self.soln_inds[ind]

    def find_solutions(self, stopfunc=None):
        if stopfunc is None:
            def func(soln):
                self.no_solns += 1
                return True
            stopfunc = func
        while True:
            while self.puppet.i in range(len(self)):
                # if self.i < 3:
                # print(self)
                if self.puppet.action == Puppet.FORWARD:
                    # choose g-node
                    self.puppet.srcs[self.puppet.i] = self.choose_best_node()
                    if self.puppet.is_last_option():
                        self.set_rollback()
                assert self.puppet.i >= -1
                if self.puppet.action == self.puppet.BACKTRACK and self.soln_ind() != self.puppet.UNDEFINED:
                    if self.puppet.i < len(self) / 2:
                        # select order in which h-colors will be tested
                        self.choose_target_order()
                    pass
                mapto = self.find_possible_map()
                if self.is_valid_option(mapto):
                    self.puppet.forward_node(mapto)
                else:
                    self.puppet.set_rollback()
            if self.puppet.i < 0:
                break
            # print(self)
            assert self.is_valid_solution()
            if not stopfunc([self.puppet.soln[i] for i in range(len(self.puppet.soln))]):
                return
            self.puppet.i -= 1
            self.puppet.action = self.puppet.BACKTRACK
        if self.puppet.i != -1 and not stopfunc([self.puppet.soln[i] for i in range(len(self.puppet.soln))]):
            return

    def __str__(self):
        s = 'backtrack' if self.puppet.action else 'forward'
        s += ' ' + str(self.puppet.i) + ' soln:'
        # s += str([self.soln_ind[x] for x in self.srcs])
        s += str([self.puppet.soln[i] for i in range(len(self.puppet.soln))])
        return s

    def __len__(self):
        return len(self.g.nodes())


def find_homomorphisms(g, h):
    s = Solver(g, h)
    s.find_solutions()
    return s.no_solns

def is_homomorphic(g, h):
    s = Solver(g, h)
    def func(soln):
        s.no_solns = 1
        s.solution = [s.puppet.soln[i] for i in range(len(s.puppet.soln))]
        return False
    s.find_solutions(stopfunc=func)
    if s.no_solns == 1:
        return s.solution
    return None
