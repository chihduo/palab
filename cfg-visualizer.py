import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Set, Union
import ipywidgets as widgets
from IPython.display import display, clear_output
import graphviz

def draw_cfg(cfg):
    """
    Draw the control flow graph using Graphviz.

    Args:
        cfg (ControlFlowGraph): Control flow graph object with nodes and edges

    Returns:
        graphviz.Digraph: The generated graph object
    """
    dot = graphviz.Digraph(comment='Control Flow Graph')
    dot.attr(rankdir='TB', size='10,8', label='Control Flow Graph', labelloc='t', fontsize='16')
    dot.attr('node', shape='box', style='filled', fillcolor='lightblue', color='darkblue', fontsize='10')
    dot.attr('edge', color='gray', fontsize='10')

    # Add nodes
    for node in cfg.nodes:
        # Escape HTML in the content to ensure proper rendering
        content = node.content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        # Replace newlines with HTML breaks for proper display
        content = content.replace('\n', '<br/>')
        node_id = str(node.id)

        # Special styling for initial and terminal states
        if node.special == "initial":
            # Initial state as a circle with green color
            dot.node(node_id, f"<{content}>", shape='circle', fillcolor='lightgreen', color='darkgreen')
        elif node.special == "terminal":
            # Terminal state as a doublecircle with red color
            dot.node(node_id, f"<{content}>", shape='doublecircle', fillcolor='mistyrose', color='darkred')
        else:
            # Regular node
            dot.node(node_id, f"<{content}>")

    # Add edges
    for edge in cfg.edges:
        source = str(edge.source)
        target = str(edge.target)
        condition = edge.condition
        if condition:
            dot.edge(source, target, label=condition)
        else:
            dot.edge(source, target)

    display(dot)
