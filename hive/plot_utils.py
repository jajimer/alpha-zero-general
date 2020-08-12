import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon
import numpy as np

def hex_to_cartesian(list_coords):
    """"""
    hcoord = [c[0] for c in list_coords]
    vcoord = [2. * np.sin(np.radians(60)) * (c[1] - c[2]) /3. for c in list_coords]
    return hcoord, vcoord

def plot_grid(state):
    
    coords = list(state.grid.keys())
    hcoord, vcoord = hex_to_cartesian(coords)
    
    colors = [v[-1][0].name for c, v in state.grid.items()]
    labels = [v[-1][1].name.upper()[0] for c, v in state.grid.items()]
    dict_colors = {'Q': 'yellow', 'B': 'purple', 'G': 'green', 'S': 'brown', 'A': 'blue'}
    
    fig, ax = plt.subplots(1)
    ax.set_aspect('equal')

    # Add some coloured hexagons
    for x, y, c, l in zip(hcoord, vcoord, colors, labels):
        color = 'k' if c == 'black' else 'white'
        hex = RegularPolygon((x, y), numVertices=6, radius=2. / 3., orientation=np.radians(30), 
                             facecolor=color, alpha=0.5, edgecolor='k')
        ax.add_patch(hex)
        # Also add a text label
        ax.text(x, y+0.2, l[0], ha='center', va='center', size=10, color = dict_colors[l])

    # Also add scatter points in hexagon centres
    ax.scatter(hcoord, vcoord, c=[c[0].lower() for c in colors], alpha=0.01)

    return fig, ax