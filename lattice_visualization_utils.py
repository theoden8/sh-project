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
    is_small = 'small_graphs' in os.path.dirname(label)
    n, id = get_graph_size(label), get_graph_id(label)
    if is_small:
        g = load_graph(fname)
        if is_path(g):
            return '$P_%s$' % n
        elif is_cycle(g):
            return '$C_%s$' % n
        elif is_complete(g):
            return '$K_%s$' % n
    return '${%s}^{%s}$' % (n, id % 1000)


def node_color_func(label):
    fname = label
    is_small = 'small_graphs' in os.path.dirname(label)
    if is_small:
        n = int(os.path.basename(label).split('_')[1])
        g = load_graph(fname)
        if is_path(g):
            return '#CCCCCC'
        elif is_cycle(g):
            return '#FFFFCC'
        elif is_complete(g):
            return '#66FF66'
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


def filter_significant_nodes(g, label):
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


def plot_node(lattice, nd, **kwargs):
    imgname = 'graph_images/' + os.path.basename(nd).replace('.json', '.png')
    alpha = kwargs['alpha'] if 'alpha' in kwargs else .2
    if not os.path.exists(imgname):
        plot_graph(load_graph(nd), imgname,
                   title=graph_label_rename(nd) + ' : ' + str(lattice.g.degree(nd)),
                   maxsize=8,
                   node_size=7000,
                   colors=[node_color_func(nd)],
                   edge_width=20.,
                   edge_color='w',
                   facecolor=node_color_func(nd),
                   fig_alpha=alpha)
        print('plot graph', nd)
    return imgname


def get_file_url(filename):
    abs_fname = os.path.abspath(filename)
    return pathlib.Path(abs_fname).as_uri()


# def is_interesting_node(lattice, nd):
#     if not lattice.path_finder.is_significant_node(nd):
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


def export_to_vivagraphjs(lattice, filename):
    g = lattice.path_finder.core_graph
    # g = nx.transitive_reduction(g)
    # for nd in list(g.nodes()):
    #     if not is_interesting_node(lattice, nd):
    #         g = contracted_node(g, nd)
    g = nx.transitive_reduction(g)
    with open(filename, 'w') as f:
        vivagraphjs = 'vivagraph.js'
        if not os.path.exists(vivagraphjs):
            subprocess.check_call(['wget', 'https://raw.githubusercontent.com/anvaka/VivaGraphJS/master/dist/vivagraph.js', '-qO', vivagraphjs])
        vivagraph_uri = get_file_url(vivagraphjs)
        f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Graph Homomorphisms</title>
    <script type="text/javascript" src="%s"></script>
    <script type="text/javascript">
        function main () {
            var graph = Viva.Graph.graph();\n""" % vivagraph_uri)
        total = max([lattice.g.degree(nd) for nd in g.nodes()])
        if os.path.exists('graph_images'):
            for fname in os.listdir('graph_images/'):
                os.remove('graph_images/' + fname)
                print('removed file graph_images/%s' % fname)
        else:
            os.mkdir('graph_images')
        for nd in g.nodes():
            degree = float(lattice.g.degree(nd))
            importance = (degree / total) ** .3
            imgname = plot_node(lattice, nd, alpha=0.05 + (0.6 * importance))
            f.write("            graph.addNode('%s', {url : '%s'})\n" % (nd, get_file_url(imgname)))
        f.write('\n')
        for (u, v) in g.edges():
            f.write("            graph.addLink('%s', '%s')\n" % (u, v))
        f.write("""
            var graphics = Viva.Graph.View.svgGraphics(),
                nodeSize = 24;
            graphics.node(function(node) {
                return Viva.Graph.svg('image')
                     .attr('width', nodeSize)
                     .attr('height', nodeSize)
                     .link(node.data.url);
            }).placeNode(function(nodeUI, pos) {
                nodeUI.attr('x', pos.x - nodeSize / 2).attr('y', pos.y - nodeSize / 2);
            });
            // To render an arrow we have to address two problems:
            //  1. Links should start/stop at node's bounding box, not at the node center.
            //  2. Render an arrow shape at the end of the link.
            // Rendering arrow shape is achieved by using SVG markers, part of the SVG
            // standard: http://www.w3.org/TR/SVG/painting.html#Markers
            var createMarker = function(id) {
                    return Viva.Graph.svg('marker')
                               .attr('id', id)
                               .attr('viewBox', "0 0 10 10")
                               .attr('refX', "10")
                               .attr('refY', "5")
                               .attr('markerUnits', "strokeWidth")
                               .attr('markerWidth', "10")
                               .attr('markerHeight', "5")
                               .attr('orient', "auto");
                },
                marker = createMarker('Triangle');
            marker.append('path').attr('d', 'M 0 0 L 10 5 L 0 10 z');
            // Marker should be defined only once in <defs> child element of root <svg> element:
            var defs = graphics.getSvgRoot().append('defs');
            defs.append(marker);
            var geom = Viva.Graph.geom();
            graphics.link(function(link){
                // Notice the Triangle marker-end attribe:
                return Viva.Graph.svg('path')
                           .attr('stroke', 'gray')
                           .attr('background-color', 'white')
                           .attr('marker-end', 'url(#Triangle)');
            }).placeLink(function(linkUI, fromPos, toPos) {
                // Here we should take care about
                //  "Links should start/stop at node's bounding box, not at the node center."
                // For rectangular nodes Viva.Graph.geom() provides efficient way to find
                // an intersection point between segment and rectangle
                var toNodeSize = nodeSize,
                    fromNodeSize = nodeSize;
                var from = geom.intersectRect(
                        // rectangle:
                                fromPos.x - fromNodeSize / 2, // left
                                fromPos.y - fromNodeSize / 2, // top
                                fromPos.x + fromNodeSize / 2, // right
                                fromPos.y + fromNodeSize / 2, // bottom
                        // segment:
                                fromPos.x, fromPos.y, toPos.x, toPos.y)
                           || fromPos; // if no intersection found - return center of the node
                var to = geom.intersectRect(
                        // rectangle:
                                toPos.x - toNodeSize / 2, // left
                                toPos.y - toNodeSize / 2, // top
                                toPos.x + toNodeSize / 2, // right
                                toPos.y + toNodeSize / 2, // bottom
                        // segment:
                                toPos.x, toPos.y, fromPos.x, fromPos.y)
                            || toPos; // if no intersection found - return center of the node
                var data = 'M' + from.x + ',' + from.y +
                           'L' + to.x + ',' + to.y;
                linkUI.attr("d", data);
            });

            var renderer = Viva.Graph.View.renderer(graph, {
                graphics : graphics
            });
            renderer.run();
        }
        </script>

    <style type="text/css" media="screen">html, body, svg { width: 100%; height: 100%; }</style>
</head>
<body onload='main()' bgcolor='#555566'></body>
</html>""")
    print('exported graph as vivagraphjs to', filename)


def export_to_d3(lattice, filename):
    g = lattice.g
    with open(filename, 'w') as f:
        json.dump(serialize_graph(g), f)
    with open('lattice_d3_template.html', 'r') as fr:
        with open('lattice_d3.html', 'w') as fw:
            fw.write(fr.read().replace('lattice_graph_d3.json', os.path.abspath(filename)))
    print('exported graph as d3 to', filename)


def plot_lattice(lattice, filename, **kwargs):
    plt.figure(figsize=(16, 16))
    plt.suptitle('lattice',
                 size=35,
                 family='monospace',
                 weight='bold')

    g = lattice.g
    ax = plt.subplot(111)
    nodelist = list(g.nodes())
    nodelist_neighborhood = nodelist
    new_g = g

    if len(nodelist) > 100:
        #nodelist = [nd for nd in g.nodes() if filter_significant_nodes(g, nd)]
        nodelist = lattice.path_finder.significant_nodes
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
                     font_size=9,
                     # font_family='arial',
                     font_weight='bold',
                     font_color='k',
                     alpha=1.,
                     node_color=[node_color_func(nd) for nd in nodelist_neighborhood],
                     # node_size=[500 for nd in nodelist_neighborhood],
                     node_size = [(500 if nd in nodelist else 30) for nd in nodelist_neighborhood],
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


def graph_color(fname):
    red = (1, 0, 0)
    green = (0, 1, 0)
    blue = (0, 0, 1)
    yellow = (1, 1, 0)
    purple = (1, 0, 1)
    cyan = (0, .7, .7)
    black = (0, 0, 0)
    gray = (.5, .5, .5)
    white = (1, 1, 1)
    g = load_graph(fname)
    if is_path(g):
        return gray
    elif is_cycle(g):
        return yellow
    elif is_complete(g):
        return green
    elif len(g.nodes()) <= 5:
        return cyan
    return black


def plot_adjacency_matrix(g, filename):
    red = (1, 0, 0)
    green = (0, 1, 0)
    blue = (0, 0, 1)
    yellow = (1, 1, 0)
    purple = (1, 0, 1)
    cyan = (0, .7, .7)
    black = (0, 0, 0)
    gray = (.5, .5, .5)
    white = (1, 1, 1)

    colors = [
        # (1, 0, 0),
        # (0, 1, 0),
        # (0, 0, 1),
        # (0, 0, 0),
        # (1, 0, 1),
        # (0, 1, 1)
        black
    ]
    get_color = lambda n: colors[n % len(colors)]
    size = len(g.nodes())
    svg_fname = filename.replace('.png', '.svg')
    with cairo.SVGSurface(svg_fname, size, size) as surface:
        ctx = cairo.Context(surface)

        ctx.rectangle(0, 0, float(size), float(size))
        ctx.set_source_rgba(1., 1., 1., 1.)
        ctx.fill()

        n = len(g)
        rectsize = float(size) / n
        g_nodes = list(g.nodes())
        color_priority = [gray, yellow, green, cyan, black]
        def sort_func(gfile):
            with open(gfile, 'r') as f:
                g = deserialize_digraph(f.read())
            n = get_graph_size(gfile)
            e = len(g.edges())
            return n * 10000 + e
        g_nodes.sort(key=sort_func)
        for i in range(n):
            row_color = graph_color(g_nodes[i])
            for j in range(n):
                col_color = graph_color(g_nodes[j])
                cell_color = row_color
                if col_color in color_priority and color_priority.index(col_color) < color_priority.index(cell_color):
                    cell_color = col_color

                if g.has_edge(g_nodes[i], g_nodes[j]) or nx.has_path(g, g_nodes[i], g_nodes[j]):
                    cr, cg, cb = cell_color
                    ctx.rectangle(i * rectsize, j * rectsize, rectsize, rectsize)
                    ctx.set_source_rgba(cr, cg, cb, 1.)
                    ctx.fill()
            ctx.stroke()
    print('finished creating a diagram')
    subprocess.check_call(['rsvg-convert', svg_fname, '-o', filename])
    os.remove(svg_fname)
    print('generated adjacency matrix', filename)
