#!/usr/bin/env python3


import sys
from graph_utils import *


if __name__ == '__main__':
    plt.switch_backend('agg')
    g = None
    with open(sys.argv[1], 'r') as f:
        g = deserialize_graph(f.read())
    plot_graph(g, 'graph.png', title=sys.argv[1])
