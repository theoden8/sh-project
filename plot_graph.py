#!/usr/bin/env python3


import sys
import os
from graph_utils import *
from lattice_visualization_utils import graph_label_rename


if __name__ == '__main__':
    plt.switch_backend('agg')
    gfile = sys.argv[1]
    output = os.path.basename(gfile).replace('.json', '.png').replace('.g6', '.png')
    g = load_graph(gfile)
    plot_graph(g, output,
               title=graph_label_rename(gfile),
               title_font_size=50,
               label_font_size=50,
               maxsize=16,
               node_size=10000)
    print('generated image', output)
