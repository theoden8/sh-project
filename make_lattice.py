#!/usr/bin/env python3


import os
import sys
import subprocess

from graph_utils import *
from lattice_utils import *
from lattice_visualization_utils import *


if __name__ == '__main__':
    plt.switch_backend('agg')
    dbfile = './lattice.json'
    lattice = Lattice()
    if os.path.exists(dbfile):
        lattice = Lattice.load(dbfile)

    for graph_file in sys.argv[1:]:
        graph_file = graph_file.replace('./', '')
        lattice.add_object(graph_file)

    if len(sys.argv) > 2:
        lattice.unload(dbfile)
    lattice.transitive_reduction()
    if len(lattice.path_finder.representatives) > 0:
        export_as_vivagraph(lattice, 'visualizations')
        plot_lattice(lattice, 'hasse_diagram.png')
