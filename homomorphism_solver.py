#!/usr/bin/env python3


from random import randint
from random import choice


from graph_utils import *


class Solver:
    UNDEFINED = -1
    FORWARD, BACKTRACK = range(2)
    def __init__(self, g, h):
        self.g = g
        self.h = h
        self.possibles = [
            # sorted(list(self.h.nodes()), key=lambda x: abs(self.g.degree()[nd] - self.h.degree()[x]))
            shifted(list(h.nodes()), nd)
            # sorted(list(self.h.nodes()))
                for nd in range(len(self.g.nodes()))
        ]
        # self.srcs = [Solver.UNDEFINED for nd in self.g.nodes()]
        # self.srcs = shuffled(list(range(len(self))))
        self.srcs = list(range(len(self)))
        # self.srcs = sorted(list(self.g.nodes()), key=lambda nd: self.g.degree()[nd], reverse=True)
        self.soln_inds = [Solver.UNDEFINED for nd in self.g.nodes()]
        self.soln = [Solver.UNDEFINED for nd in self.g.nodes()]
        self.i = 0
        self.action = Solver.FORWARD
        self.no_solns = 0

    def is_valid_solution(self):
        dbg = (self.soln == [0, 0, 0, 1, 3, 5, 6])
        assert self.i == len(self)
        gnodes = list(self.g.nodes())
        for e in list(self.g.edges()):
            u, v = e
            u, v = gnodes.index(u), gnodes.index(v)
            hu, hv = (self.soln[u], self.soln[v])
            if (hu, hv) not in self.h.edges():
                return False
        return True

    def choose_best_node(self):
        option, rating = -1, -1
        available = [x for x in range(len(self)) if x not in self.srcs[:self.i]]
        for ind in available:
            new_rating = 0
            new_rating += 100 * len([nd for nd in list(self.g.neighbors(ind)) if nd in self.srcs[:self.i]])
            new_rating += 50 * len([nd for nd in list(self.g.neighbors(ind)) if nd not in self.srcs[:self.i]])
            if new_rating > rating:
                option = ind
                rating = new_rating
        if option != -1:
            return option
        return self.srcs[self.i]

    def is_last_option(self, val=None):
        i = 0 if self.i < 0 else self.i
        ind = self.srcs[i]
        if val is None:
            val = self.soln_ind()
        return val == len(self.possibles[ind]) - 1

    def is_valid_option(self, val=None):
        i = 0 if self.i < 0 else self.i
        ind = self.srcs[i]
        if val is None:
            val = self.soln_ind()
        return val in range(len(self.possibles[ind]))

    def choose_target_order(self):
        i = 0 if self.i < 0 else self.i
        ind = self.srcs[i]
        def rating_func(h_ind):
            map_image = [self.soln[idx] for idx in self.srcs[:self.i]]
            rating = 0
            rating += 100 * len([nd for nd in list(self.h.neighbors(h_ind)) if nd in map_image])
            rating += 10 * len([nd for nd in list(self.h.neighbors(h_ind)) if nd not in map_image])
            return rating
        self.possibles[ind] = sorted(self.possibles[ind], key=rating_func, reverse=True)

    def find_possible_map(self):
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
                    if (gu, gv) in self.g.edges() and (hu, hv) not in self.h.edges():
                        approved = False
                        break
            if approved:
                break
            mapto += 1
        return mapto

    def forward_node(self, mapto):
        i = 0 if self.i == -1 else self.i
        ind = self.srcs[i]
        self.action = Solver.FORWARD
        self.soln_inds[ind] = mapto
        self.soln[ind] = self.possibles[ind][self.soln_inds[ind]]
        self.i += 1

    def set_rollback(self):
        i = 0 if self.i == -1 else self.i
        ind = self.srcs[i]
        self.action = Solver.BACKTRACK
        # self.srcs[i] = Solver.UNDEFINED
        self.soln_inds[ind] = Solver.UNDEFINED
        self.soln[ind] = Solver.UNDEFINED
        self.i -= 1

    def soln_ind(self):
        i = 0 if self.i < 0 else self.i
        ind = self.srcs[i]
        return self.soln_inds[ind]

    def find_solutions(self, function=None):
        if function is None:
            def func(soln):
                self.no_solns += 1
            function = func
        while True:
            while self.i in range(len(self)):
                if self.i < 3:
                    print(self)
                if self.action == Solver.FORWARD:
                    self.srcs[self.i] = self.choose_best_node()
                    if self.is_last_option():
                        self.set_rollback()
                assert self.i >= -1
                if self.action == Solver.BACKTRACK and self.soln_ind() != Solver.UNDEFINED:
                    if self.i < len(self) / 2:
                        self.choose_target_order()
                    pass
                mapto = self.find_possible_map()
                if self.is_valid_option(mapto):
                    self.forward_node(mapto)
                else:
                    self.set_rollback()
            if self.i < 0:
                break
            if self.is_valid_solution():
                function(self.soln)
            # deal with result
            self.i -= 1
            self.action = Solver.BACKTRACK
        if self.i != -1:
            function(self.soln)

    def __str__(self):
        s = 'backtrack' if self.action else 'forward'
        s += ' ' + str(self.i) + ' soln:' + str([self.soln_inds[x] for x in self.srcs])
        return s

    def __len__(self):
        return len(self.g.nodes())


def find_homomorphisms(g, h):
    s = Solver(g, h)
    s.find_solutions()
    return s.no_solns
