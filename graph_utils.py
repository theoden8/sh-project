import os
import json
import math
from random import choice
from random import randint
from random import shuffle
import matplotlib as mpl
import matplotlib.pyplot as plt
import networkx as nx


def shuffled(lst):
    shuffle(lst)
    return lst


def shifted(lst, steps=1):
    for i in range(steps):
        lst = [lst[-1]] + lst[:-1]
    return lst


def plot_graphs(Gs, ssizes, filename, **kwargs):
    layout = kwargs['layout'] if 'layout' in kwargs else nx.kamada_kawai_layout
    colors = kwargs['colors'] if 'colors' in kwargs else ['r']
    title_font_size = kwargs['title_font_size'] if 'title_font_size' in kwargs else 40
    label_font_size = kwargs['label_font_size'] if 'label_font_size' in kwargs else 20
    node_size = kwargs['node_size'] if 'node_size' in kwargs else 1800
    label_rename_func = kwargs['label_func'] if 'label_func' in kwargs else str
    facecolor = kwargs['facecolor'] if 'facecolor' in kwargs else 'w'
    fig_alpha = kwargs['fig_alpha'] if 'fig_alpha' in kwargs else 1.
    edge_width = kwargs['edge_width'] if 'edge_width' in kwargs else .3
    edge_color = kwargs['edge_color'] if 'edge_color' in kwargs else 'k'
    nr, nc = ssizes
    maxsize = kwargs['maxsize'] if 'maxsize' in kwargs else 24.
    totalsize = float(float(maxsize) / math.sqrt(nc * nr))
    fig = plt.figure(1, figsize=(int(totalsize * nc), int(totalsize * nr)))
    fig.patch.set_facecolor(facecolor)
    mpl.rcParams['savefig.facecolor'] = facecolor
    fig.patch.set_alpha(fig_alpha)
    plt.clf()
    splts = fig.subplots(nrows=nr, ncols=nc)
    if nr == 1:
        splts = [splts]
    if nc == 1:
        splts = [splts]
    for i, j in [[y, x] for y in range(nr) for x in range(nc)]:
        G, title = Gs[i * nc + j]
        pos = layout(G, dim=2)
        ax = splts[i][j]
        plt.sca(ax)
        if len(G) < 100:
            nx.draw_networkx_labels(G, pos,
                                    labels={i : label_rename_func(i) for i in list(G.nodes)},
                                    font_size=label_font_size,
                                    #font_family='arial-black',
                                    font_weight='bold',
                                    font_color='w',
                                    alpha=1.,
                                    ax=ax)
        nx.draw_networkx_nodes(G, pos,
                               node_color=colors[(i * nc + j) % len(colors)],
                               node_size=node_size,
                               ax=ax)
        nx.draw_networkx_edges(G, pos,
                               edge_color=edge_color,
                               width=[edge_width for (u, v, d) in G.edges(data=True)],
                               arrowstyle='-|>',
                               arrowsize=12,
                               ax=ax,)
        ax.set_title(title, fontsize=title_font_size)
        ax.set_axis_off()
    if os.path.exists(filename):
        os.remove(filename)
    fig.savefig(filename)
    plt.clf()
    plt.cla()


def plot_graph(G, filename, **kwargs):
    title = kwargs['title'] if 'title' in kwargs else str(G)
    plot_graphs(Gs=[(G, title)],
                ssizes=(1, 1),
                filename=filename,
                **kwargs)


# def make_random_graph():
#     graphs = [
#         (nx.tutte_graph(), 'Tutte Graph'),
#         (nx.barbell_graph(randint(5, 10), randint(5, 10)), 'Barbell Graph'),
#         (nx.turan_graph(20, 5), 'Turan Graph'),
#         (nx.lollipop_graph(20, 10), 'Lollipop Graph'),

#         (nx.circular_ladder_graph(20), 'Circular Ladder Graph'),
#         (nx.caveman_graph(5, 10), 'Caveman Graph'),
#         (nx.desargues_graph(), 'Desargues Graph'),
#         (nx.barabasi_albert_graph(20, 3), 'Barabasi Albert Graph'),

#         (nx.newman_watts_strogatz_graph(40, 5, .1), 'Newman-Watts-Strogatz Graph'),
#         (nx.erdos_renyi_graph(40, .1), 'Erdos Renyi Graph'),
#         (nx.karate_club_graph(), 'Karate Club Graph'),
#         (nx.hoffman_singleton_graph(), 'Hoffman-Singleton Graph')
#     ]
#     # return choice(graphs)
#     return nx.cycle_graph(10), 'cycle (10)'


def make_random_graph(n):
    p = (1. / n) * math.log(n)
    return nx.binomial_graph(n, p)


def make_random_isomorphism(G):
    phi = shuffled(list(G.nodes()))
    edges = [(phi[a], phi[b]) for (a, b) in list(G.edges())]
    H = nx.Graph(edges)
    assert nx.is_isomorphic(G, H)
    return H, phi


def make_random_homomorphism(G):
    H = nx.Graph(G)
    r = randint(1, int(max(5, len(list(G.nodes())) / 5)))
    phi = list(range(len(G.nodes())))
    for i in range(randint(1, r)):
        u = choice(list(G.nodes()))
        v = [v for v in list(G.nodes()) if v != u and (u, v) not in list(G.edges())]
        v = choice(v)
        H.add_edge(v, u)
        edge = (v, u)
        H = nx.contracted_edge(H, edge, self_loops=False)
        phi[u] = v
    for i in range(randint(1, r)):
        u = choice(list(G.nodes()))
        v = [v for v in list(G.nodes()) if v != u and (u, v) not in list(G.edges())]
        v = choice(v)
        H.add_edge(u, v)
    return H, phi


def plot_homomorphism(G, H, phi, filename):
    plot_graphs(Gs=[(G, '$ Dom(\phi) $' + str(phi)), (H, '$ Im(\phi) $')],
                ssizes=(1, 2),
                filename=filename,
                colors=['r', 'b'],
                title_font_size=20,
                label_font_size=20)

def serialize_graph(g):
    return {
        'nodes': list(g.nodes()),
        'edges': list(g.edges())
    }


def deserialize_graph(s):
    s = json.loads(s)
    nodes = s['nodes']
    edges = s['edges']
    g = nx.Graph()
    g.add_edges_from(edges)
    return g


def load_graph(fname):
    with open(fname, 'r') as f:
        return deserialize_graph(f.read())


def deserialize_digraph(s):
    s = json.loads(s)
    nodes = s['nodes']
    edges = s['edges']
    g = nx.DiGraph()
    for nd in nodes:
        g.add_node(nd)
    g.add_edges_from(edges)
    return g


def is_complete(g):
    for u in range(len(g.nodes())):
        for v in range(len(g.nodes())):
            if u != v and not g.has_edge(u, v):
                return False
    return True


def is_path(g):
    # we know it's connected
    leaves = 0
    for nd in g.nodes():
        if g.degree(nd) == 1:
            leaves += 1
        elif g.degree(nd) != 2:
            return False
        if leaves > 2:
            return False
    return nx.is_tree(g) and leaves == 2


def is_cycle(g):
    for nd in g.nodes():
        if g.degree(nd) != 2:
            return False
    return True
