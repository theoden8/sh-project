#!/usr/bin/env python3


import subprocess
import json


from graph_utils import *
from graph_dataset_utils import *


if __name__ == '__main__':
    if not os.path.exists('./small_graphs/'):
        os.mkdir('small_graphs')
        for i in range(2, 8+1):
            filename = './graph%sc.g6' % i
            link = 'http://users.cecs.anu.edu.au/~bdm/data/graph%sc.g6' % i
            print('downloading dataset for graph_size=%s...' % i)
            download_dataset(link, filename)
            def write_graph(g, index):
                s = serialize_graph(g)
                with open('small_graphs/graph_%s_%s.json' % (len(list(g.nodes())), index), 'w') as f:
                    print('parsed #%s into json' % index)
                    json.dump(s, f)
            apply_dataset(filename, write_graph)
            os.remove(filename)
