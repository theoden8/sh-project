#!/usr/bin/env python3
#coding: utf-8


import subprocess
import json


from graph_utils import *


if __name__ == '__main__':
    if not os.path.exists('./small_graphs/'):
        os.mkdir('small_graphs')
    for i in range(2, 9+1):
        filename = './graph%sc.g6' % i
        # link = 'http://users.cecs.anu.edu.au/~bdm/data/graph%sc.g6' % i
        # print('downloading dataset for graph_size=%s...' % i)
        # download_dataset(link, filename)
        # if not os.path.exists(filename):
        #     command = ['wget', '-q', link, '-O', filename]
        #     subprocess.check_call(command)
        with open(filename, 'r', encoding='utf-8') as f:
            index = 0
            for line in f:
                index += 1
                line = line.strip()
                # g = nx.from_graph6_bytes(line)
                graph_fname = 'small_graphs/graph_%d_%d.g6' % (i, index)
                with open(graph_fname, 'w', encoding='utf-8') as fw:
                    fw.write(line.strip())
                # unload_graph(g, graph_fname)
                if index % 1000 == 0:
                    print('unloading to', graph_fname)
        # os.remove(filename)
