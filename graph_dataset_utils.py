import json
import subprocess


from graph_utils import *


def download_dataset(link, filename):
    if not os.path.exists(filename):
        command = ['wget', '-q', link, '-O', filename]
        subprocess.check_call(command)


def apply_dataset(filename, apply_func):
    tempfile = 'tempfile_%s' % randint(1, 100000000)
    with open(tempfile, 'w') as f:
        command = ['nauty-showg', '-A', filename]
        subprocess.check_call(command, stdout=f)
    def make_graph_from_adj(adj):
        g = nx.Graph()
        for u in range(len(adj)):
            for v in range(len(adj)):
                if adj[u][v] == 1:
                    g.add_edge(u, v)
        return g
    count = 0
    with open(tempfile, 'r') as f:
        adj = []
        next_is_decl = False
        for line in f:
            line = line.strip()
            if len(line) == 0:
                print('line isspace', line)
                if len(adj) > 0:
                    apply_func(make_graph_from_adj(adj), count)
                count += 1
                adj = []
                next_is_decl = True
            elif next_is_decl:
                print('next decl cancelled at', line)
                next_is_decl = False
            else:
                print('line', line)
                adj += [[int(x) for x in line.split()]]
        if len(adj) > 0:
            apply_func(make_graph_from_adj(adj), count)
    os.remove(tempfile)
