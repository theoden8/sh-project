#!/usr/bin/env python3


from graph_utils import *
from lattice_utils import *


if __name__ == '__main__':
    plt.switch_backend('agg')
    for lattice_frame in sys.argv[1:]:
        if not os.path.exists(lattice_frame):
            continue
        g = None
        with open(lattice_frame, 'r') as f:
            g = deserialize_digraph(f.read())
        frame_name = lattice_frame.replace('lattice_', '').replace('.json', '.png')
        plot_lattice(g, frame_name)
        print('generated frame', frame_name)