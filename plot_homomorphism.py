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
            shifted(list(h.nodes()), nd)
            # sorted(list(self.h.nodes()))
                for nd in range(len(self.g.nodes()))
        ]
        # self.srcs = [Solver.UNDEFINED for nd in self.g.nodes()]
        self.srcs = shuffled(list(range(len(self))))
        # self.srcs = list(range(len(self)))
        self.soln_inds = [Solver.UNDEFINED for nd in self.g.nodes()]
        self.soln = [Solver.UNDEFINED for nd in self.g.nodes()]
        self.i = 0
        self.action = Solver.FORWARD

    def reset_soln_cell(self):
        i = 0 if self.i == -1 else self.i
        ind = self.srcs[i]
        # self.srcs[i] = Solver.UNDEFINED
        self.soln_inds[ind] = Solver.UNDEFINED
        self.soln[ind] = Solver.UNDEFINED

    def set_soln_ind(self, sln_ind):
        i = 0 if self.i == -1 else self.i
        ind = self.srcs[i]
        self.soln_inds[ind] = sln_ind
        self.soln[ind] = self.possibles[ind][self.soln_inds[ind]]

    def set_next_soln(self):
        self.set_soln_ind(self.soln_ind() + 1)

    def is_valid_soln(self):
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

    def is_final_option(self, val=None):
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

    def soln_ind(self):
        i = 0 if self.i < 0 else self.i
        ind = self.srcs[i]
        return self.soln_inds[ind]

    def __str__(self):
        s = 'backtrack' if self.action else 'forward'
        s += ' ' + str(self.i) + ' soln:' + str(self.soln_inds)
        return s

    def __len__(self):
        return len(self.g.nodes())


def is_homomorphism(g, h):
    s = Solver(g, h)
    print(s.possibles)
    while True:
        while s.i in range(len(s)):
            # print(s)
            if s.action == Solver.FORWARD:
                # s.srcs[s.i] = choice([j for j in range(len(s.soln)) if j not in s.srcs[:s.i]])
                # s.srcs[s.i] = s.i
                if s.is_final_option():
                    # print('used out current cell', s.soln_ind())
                    s.action = Solver.BACKTRACK
                    s.reset_soln_cell()
                    s.i -= 1
            assert s.i >= -1
            # if s.action == Solver.BACKTRACK and s.soln_inds[ind] != Solver.UNDEFINED:
                # update constraint?
            #     print('stmt 1')
            #     s.reset_soln_cell()
            cr = s.soln_ind() + 1
            while not s.is_final_option(cr):
                if True:
                    break
                cr += 1
            if not s.is_final_option():
                s.action = Solver.FORWARD
                # s.srcs[ii] = s.i
                s.set_soln_ind(cr)
                s.i += 1
            else:
                s.action = Solver.BACKTRACK
                s.reset_soln_cell()
                s.i -= 1
            # print(s)
        if s.i < 0:
            break
        if s.is_valid_soln():
            yield s.soln
        # deal with result
        s.i -= 1
        s.action = Solver.BACKTRACK
    if s.i != -1:
        yield s.soln


if __name__ == "__main__":
    plt.switch_backend('agg')
    # G, gname = make_random_graph()
    # G = nx.binomial_graph(7, .4)
    # nx.write_gpickle(G, 'graph.pkl')
    G = nx.read_gpickle('graph.pkl')
    H, phi = make_random_homomorphism(G)
    plot_homomorphism(G, H, phi)
    # nx.write_gpickle(H, 'graph_morph.pkl')
    # H = nx.read_gpickle('graph_morph.pkl')
    # H = make_random_isomorphism(G)
    # for soln in is_homomorphism(G, H):
    #     print('homomorphism', soln)
