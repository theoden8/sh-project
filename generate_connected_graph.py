#!/usr/bin/env python3


import sys
import json


from graph_utils import *


if __name__ == '__main__':
    graph_size = int(sys.argv[1])
    G = None
    while G is None or not nx.is_connected(G):
        G = make_random_graph(graph_size)
    if not os.path.isdir('./graphs'):
        os.mkdir('./graphs')
    filename = './graphs/graph_%s_%s.json' % (graph_size, randint(1, 1000000000))
    with open(filename, 'w') as f:
        print('writing file %s' % filename)
        json.dump(serialize_graph(G), f)
