import os
import sys
import subprocess
import pathlib
import math

from networkx.drawing.nx_agraph import graphviz_layout
import cairo

from graph_utils import *
from homomorphism_solver import *
from lattice_utils import *


def graph_label_rename(label):
    fname = label
    n, id = get_graph_size(label), get_graph_id(label)
    if 'small_graphs' in os.path.dirname(fname) or 'special_graphs' in os.path.dirname(fname):
        g = load_graph(fname)
        if is_path(g):
            return '$P_{%s}$' % n
        elif is_cycle(g):
            return '$C_{%s}$' % n
        elif is_complete(g):
            return '$K_{%s}$' % n
        elif 'kneser' in os.path.basename(fname):
            kg_n, kg_k = os.path.basename(fname).split('_')[0].split('-')[1:]
            return '$KG_{(%s, %s)}$' % (kg_n, kg_k)
    return '${%s}^{%s}$' % (n, id % 1000000)


def node_color_func(label):
    fname = label
    is_small = 'small_graphs' in os.path.dirname(label)
    if 'small_graphs' in os.path.dirname(fname) or 'special_graphs' in os.path.dirname(fname):
        n = get_graph_size(label)
        g = load_graph(fname)
        if n == 2 or is_cycle(g):
            return '#FFFFCC'
        elif is_complete(g):
            return '#66FF66'
        elif 'kneser' in os.path.basename(fname):
            return '#FFFFFF'
        elif n <= 5:
            return '#00AAAA'
        elif n == 6:
            return '#9999FF'
        elif n == 7:
            return '#FF99FF'
        elif n == 8:
            return '#99FFFF'
        elif n >= 9:
            return '#FF9999'
    return '#FFCCCC'


def node_color_func_alternative(label):
    fname = label
    if 'small_graphs' in os.path.dirname(fname) or 'special_graphs' in os.path.dirname(fname):
        n = get_graph_size(label)
        g = load_graph(fname)
        if n == 2 or is_complete(g):
            return node_color_func(label)
        return '#FF99FF'
    return '#FF9999'


def filter_representatives(g, label):
    if g.in_degree(label) != 1 or g.out_degree(label) != 1:
        return True
    nb = list(g.neighbors(label))[0]
    if g.has_edge(nb, label):
        return False
    return True


def filter_nodes_neighborhood(g, nodelist, label):
    N = get_graph_size(label)
    if N < 8 or N >= 10:
        return True
    return label in nodelist


def plot_node(lattice, nd, graph_images, ndcolorfunc, **kwargs):
    imgname = graph_images + '/' + os.path.basename(nd).replace('.json', '.png').replace('.g6', '.png')
    if os.path.exists(imgname):
        return imgname
    alpha = kwargs['alpha'] if 'alpha' in kwargs else .2
    if not os.path.exists(imgname):
        G = load_graph(nd)
        g = lattice.path_finder.core_graph
        eq_class_size = lattice.class_size(nd)
        plot_graph(G, imgname,
                   title=graph_label_rename(nd) + ' : ' + str(eq_class_size),
                   title_font_size=12,
                   title_color='w',
                   label_func=lambda x: '',
                   maxsize=2,
                   node_size=(500 if get_graph_size(nd) <= 10 else 300),
                   colors=[ndcolorfunc(nd)],
                   edge_width=(5. if get_graph_size(nd) <= 10 else 3.),
                   edge_color='w',
                   facecolor=node_color_func(nd),
                   fig_alpha=alpha)
        print('plot graph', nd)
    return imgname


def get_file_url(filename):
    abs_fname = os.path.abspath(filename)
    return pathlib.Path(abs_fname).as_uri()


# def is_interesting_node(lattice, nd):
#     if not lattice.path_finder.is_representative(nd):
#         return False
#     for nb in lattice.g.neighbors(nd):
#         if nb not in lattice.path_finder.core_graph.nodes():
#             return True
#     return False
#
#
# def contracted_node(g, nd):
#     preds = list(g.predecessors(nd))
#     succs = list(g.neighbors(nd))
#     for p in preds:
#         for s in succs:
#             g.add_edge(p, s)
#     g.remove_node(nd)
#     return g


def plot_graph_icons(lattice, graph_images, ndcolorfunc=node_color_func, **kwargs):
    # if os.path.exists(graph_images):
    #     subprocess.check_call(['rm', '-rvf', output_folder])
    if not os.path.exists(graph_images):
        os.mkdir(graph_images)
    g = lattice.path_finder.core_graph
    max_size = max([lattice.class_size(nd) for nd in g.nodes()])
    image_names = {}
    for nd in g.nodes():
        eq_class_size = float(lattice.class_size(nd))
        importance = (eq_class_size / float(max_size)) ** .3
        imgname = plot_node(lattice, nd, graph_images, ndcolorfunc=ndcolorfunc, alpha=0.05 + (0.6 * importance))
        image_names[nd] = imgname
    return image_names


def export_as_vivagraph(lattice, output_folder='visualizations'):
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)
    graph_images = output_folder + '/graph_images'
    graph_images_alt = output_folder + '/graph_images_alt'
    # g = nx.transitive_reduction(g)
    # for nd in list(g.nodes()):
    #     if not is_interesting_node(lattice, nd):
    #         g = contracted_node(g, nd)
    g = lattice.path_finder.core_graph

    g_data = {
        'nodes' : [],
        'links': [
            {
                'source': u,
                'target': v
            }
            for (u, v) in g.edges()
        ]
    }
    image_names = plot_graph_icons(lattice, graph_images)
    image_names_alt = plot_graph_icons(lattice, graph_images_alt, ndcolorfunc=node_color_func_alternative)
    for nd in g.nodes():
        g_data['nodes'] += [{
            'name': nd,
            'img1': image_names[nd][len(output_folder) + 1:],
            'img2': image_names_alt[nd][len(output_folder) + 1:]
        }]
    with open(output_folder + '/lattice_graph_vivagraph.json', 'w') as f:
        json.dump(g_data, f)
    print('exported graph as vivagraph to', output_folder)


def plot_lattice(lattice, filename, **kwargs):
    fig = plt.figure(figsize=(16, 16))
    facecolor = 'w'
    fig.patch.set_facecolor(facecolor)
    mpl.rcParams['savefig.facecolor'] = facecolor
    plt.suptitle('Hasse Diagram',
                 size=35,
                 family='monospace',
                 weight='bold')

    g = lattice.path_finder.core_graph
    ax = plt.subplot(111)
    nodelist = list(g.nodes())
    nodelist_neighborhood = nodelist
    new_g = g

    if len(nodelist) > 100:
        #nodelist = [nd for nd in g.nodes() if filter_representatives(g, nd)]
        nodelist = lattice.path_finder.representatives
        nodelist_neighborhood = [nd for nd in g.nodes() if filter_nodes_neighborhood(g, nodelist, nd)]
        if len(nodelist_neighborhood) > 1000:
            nodelist_neighborhood = nodelist
        new_g = g.subgraph(nodelist_neighborhood)
        if len(nodelist_neighborhood) == len(nodelist):
            new_g = nx.transitive_reduction(new_g)
        # nodelist = [nd for nd in g.nodes() if filter_important_nodes(g, nd)]
        # print('filtered significant nodes')
        # nodelist_neighborhood = [ndm for ndm in g.nodes()
        #                          if ndm in nodelist or (filter_important_nodes_neighborhood(g, nodelist, ndm)
        #                             and 'small_graphs' in ndm)]

#         new_g = g
#         for e in g.edges():
#             u, v = e
#             if v in nodelist_neighborhood:
#                 continue
#             if new_g.has_edge(u, v):
#                 new_g = nx.contracted_edge(new_g, e)
        # print('reduced insignificant loops')

    no_nodes = len(nodelist_neighborhood)
    # fontsize = 9 - int(math.log(no_nodes, 5))
    # nodesize_min = 150 - 20 * int(math.log(no_nodes, 5))
    # nodesize_max = 700 - 100 * int(math.log(no_nodes, 5))
    # nodesize_step = 200 - 10 * int(math.log(no_nodes, 5))
    nx.draw_networkx(new_g,
                     arrows=True,
                     pos=graphviz_layout(new_g),
                     # pos=nx.kamada_kawai_layout(new_g, dim=2),
                     # pos=nx.spring_layout(g, dim=2),
                     nodelist=nodelist_neighborhood,
                     labels={nd : graph_label_rename(nd) for nd in nodelist},
                     font_size=18,
                     # font_family='arial',
                     font_weight='bold',
                     font_color='k',
                     alpha=1.,
                     node_color=[node_color_func(nd) for nd in nodelist_neighborhood],
                     # node_size=[500 for nd in nodelist_neighborhood],
                     node_size = [(2500 if nd in nodelist else 30) for nd in nodelist_neighborhood],
                     # node_size=[(max(nodesize_min, nodesize_max - nodesize_step * (new_g.degree(nd) - 2)) if nd in nodelist else 30)
                     #            for nd in nodelist_neighborhood],
                     edge_color=[('m' if g.has_edge(e[1], e[0]) else 'k') if g.has_edge(e[0], e[1]) else 'b' for e in new_g.edges()],
                     width=[(0.2 if g.has_edge(e[1], e[0]) else 0.4) if g.has_edge(e[0], e[1]) else 0.4 for e in new_g.edges()],
                     arrowstyle='-|>',
                     arrowsize=10,
                     ax=ax)
    # ax.set_title('Lattice', fontsize=40)
    ax.set_axis_off()

    if os.path.exists(filename):
        os.remove(filename)
    plt.savefig(filename)
    plt.clf()
    plt.cla()
    plt.close()
    print('generated plot image', filename)
