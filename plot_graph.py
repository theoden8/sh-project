#!/usr/bin/env python3


import sys
from graph_utils import *


if __name__ == '__main__':
    plt.switch_backend('agg')
    gfile = sys.argv[1]
    g = load_graph(gfile)
    plot_graph(g, 'graph.png', title=gfile)
