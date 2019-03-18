#!/usr/bin/env python3


import sys
import os
from graph_utils import *
from lattice_visualization_utils import graph_label_rename


if __name__ == '__main__':
    plt.switch_backend('agg')
    gfile = sys.argv[1]
    output = os.path.basename(gfile).replace('.json', '.png')
    g = load_graph(gfile)
    plot_graph(g, output,
               title=graph_label_rename(gfile),
               maxsize=16,
               node_size=3500)
    print('generated image', output)
