import ast
import uuid
import sys
import re
import json
from io import StringIO
from graphviz import Digraph
from typing import Optional, Dict
from IPython.display import display, Image, clear_output
import ipywidgets as widgets

class ASTVisualizer(ast.NodeVisitor):
    """
    A custom AST visitor that creates a visual representation of the Abstract Syntax Tree.
    Inherits from ast.NodeVisitor which provides the basic traversal algorithm.
    """
    def __init__(self):
        # Initialize a new directed graph using graphviz
        self.graph = Digraph('AST')
        # Set graph direction to Top-to-Bottom
        self.graph.attr(rankdir='TB')
        # Keep track of the current parent node during traversal
        self.parent_node = None
    
    def get_node_id(self):
        """
        Generate a unique identifier for each node in the graph.
        This ensures no two nodes have the same ID, even if they represent similar code elements.
        """
        return str(uuid.uuid4())
    
    def get_node_label(self, node):
        """
        Create a readable label for each node based on its type and attributes.
        Different node types have different relevant attributes to display.
        
        Args:
            node (ast.AST): The AST node to create a label for
        
        Returns:
            str: A formatted label showing the node type and relevant attributes
        """
        node_type = type(node).__name__
        
        # Handle different types of nodes with their specific attributes
        if isinstance(node, ast.Name):
            # Name nodes represent variables and function names
            # id attribute contains the actual name
            return f"{node_type}\nid={node.id}"
        elif isinstance(node, ast.Constant):
            # Constant nodes represent literal values (numbers, strings, etc.)
            # value attribute contains the actual value
            return f"{node_type}\nvalue={node.value}"
        elif isinstance(node, ast.FunctionDef):
            # FunctionDef nodes represent function definitions
            # name attribute contains the function name
            return f"{node_type}\nname={node.name}"
        elif isinstance(node, ast.arg):
            # arg nodes represent function arguments
            # arg attribute contains the parameter name
            return f"{node_type}\narg={node.arg}"
        elif isinstance(node, ast.operator):
            # operator nodes represent mathematical or logical operations
            return node_type
        else:
            # For all other nodes, just show their type
            return node_type
    
    def add_edge(self, parent_id, node):
        """
        Add a new node to the graph and connect it to its parent.
        This creates the tree structure of the AST.
        
        Args:
            parent_id: ID of the parent node (None for root)
            node (ast.AST): The AST node to add
        
        Returns:
            str: ID of the newly created node
        """
        # Generate unique ID for this node
        node_id = self.get_node_id()
        # Add the node to the graph with its label
        self.graph.node(node_id, self.get_node_label(node))
        # If this node has a parent, connect them with an edge
        if parent_id:
            self.graph.edge(parent_id, node_id)
        return node_id
    
    def generic_visit(self, node):
        """
        Visit a node in the AST and create its visual representation.
        This method is called for every node in the tree during traversal.
        
        The visiting process:
        1. Adds the current node to the graph
        2. Recursively visits all children of the node
        3. Maintains proper parent-child relationships
        
        Args:
            node (ast.AST): The node being visited
        """
        parent_id = self.parent_node
        
        # Add this node and get its ID
        current_parent = self.add_edge(parent_id, node)
        # Save the previous parent to restore after visiting children
        old_parent = self.parent_node
        
        # Set current node as parent for its children
        self.parent_node = current_parent
        
        # Visit all child nodes
        # ast.iter_fields yields tuples of (field_name, field_value)
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                # Some fields contain lists of nodes (e.g., function body)
                for item in value:
                    if isinstance(item, ast.AST):
                        self.visit(item)
            elif isinstance(value, ast.AST):
                # Single node fields
                self.visit(value)
        
        # Restore the previous parent for correct sibling relationships
        self.parent_node = old_parent

def visualize_ast(code):
    """
    Parse Python code and create a visual representation of its AST.
    
    Args:
        code (str): Python source code to visualize
    
    Returns:
        Image or str: Either the visualization as an Image object,
                     or an error message if parsing fails
    """
    try:
        # Parse the code string into an AST
        tree = ast.parse(code)
        
        # Create visualizer and traverse the tree
        visualizer = ASTVisualizer()
        visualizer.visit(tree)
        
        # Generate and display the visualization
        visualizer.graph.render('ast_output', format='png', cleanup=True)
        return Image('ast_output.png')
    except SyntaxError as e:
        return f"Syntax Error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

class InteractiveASTVisualizer:
    def __init__(self):
        # Create widgets
        self.code_input = widgets.Textarea(
            value='',
            description='Code:',
            layout=widgets.Layout(width='100%', height='200px')
        )
        
        self.visualize_button = widgets.Button(
            description='Visualize AST',
            button_style='primary',
            layout=widgets.Layout(width='200px')
        )
        
        self.output = widgets.Output()
        
        # Example selector
        self.example_dropdown = widgets.Dropdown(
            options=[
                ('Variable Contexts', 'variable'),
                ('Simple Function', 'simple_function'),
                ('If-Else Statement', 'if_else'),
                ('For-Loop Statement', 'loop'),
                ('Complex Function', 'complex')
            ],
            value='variable',
            description='Examples:',
            layout=widgets.Layout(width='300px')
        )
        
        self.load_example_button = widgets.Button(
            description='Load Example',
            button_style='info',
            layout=widgets.Layout(width='200px')
        )
        
        # Bind button clicks to handlers
        self.visualize_button.on_click(self._on_visualize_click)
        self.load_example_button.on_click(self._on_load_example_click)
        
        # Example code templates
        self.examples = {
            'variable': '''x = 42        # 'x' has Store context
y = x + 1     # First 'x' has Load context, 'y' has Store context
del x         # 'x' has Del context''',
            'simple_function': '''def add(a, b):
    return a + b

result = add(5, 3)''',
            
            'if_else': '''x = 10
if x > 5:
    print("Greater")
else:
    print("Lesser")''',
            
            'loop': '''for i in range(3):
    if i % 2 == 0:
        print("Even")
    else:
        print("Odd")''',
            
            'complex': '''def calculate_factorial(n):
    if n <= 1:
        return 1
    else:
        return n * calculate_factorial(n - 1)

result = calculate_factorial(5)'''
        }
        self.code_input.value = self.examples['variable']
    
    def _on_visualize_click(self, b):
        """Handle visualize button click"""
        with self.output:
            clear_output()
            result = visualize_ast(self.code_input.value)
            if isinstance(result, str):  # Error message
                print(result)
            else:  # Image
                display(result)
    
    def _on_load_example_click(self, b):
        """Handle load example button click"""
        example_code = self.examples[str(self.example_dropdown.value)]
        self.code_input.value = example_code
    
    def display(self):
        """Display the interactive interface"""
        # Create layout
        example_controls = widgets.HBox([self.example_dropdown, self.load_example_button])
        controls = widgets.VBox([
            example_controls,
            self.code_input,
            self.visualize_button,
            self.output
        ])
        display(controls)

# Color codes for different node types
class Colors:
    # ANSI escape codes for terminal colors
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Node type colors
    STATEMENT = '\033[92m'      # bright green
    EXPRESSION = '\033[94m'     # bright blue
    CONTROL_FLOW = '\033[95m'   # bright magenta
    DEFINITION = '\033[96m'     # bright cyan
    OPERATOR = '\033[93m'       # bright yellow
    LITERAL = '\033[91m'        # bright red
    ATTRIBUTE = '\033[97m'      # bright white
    
    # For HTML output
    HTML_COLORS = {
        'STATEMENT': '#2ecc71',    # green
        'EXPRESSION': '#3498db',   # blue
        'CONTROL_FLOW': '#9b59b6', # purple
        'DEFINITION': '#00bcd4',   # cyan
        'OPERATOR': '#f1c40f',     # yellow
        'LITERAL': '#e74c3c',      # red
        'ATTRIBUTE': '#ecf0f1',    # white
    }

# Node type categorization
NODE_CATEGORIES = {
    # Definitions
    'FunctionDef': 'DEFINITION',
    'ClassDef': 'DEFINITION',
    'AsyncFunctionDef': 'DEFINITION',
    
    # Control Flow
    'If': 'CONTROL_FLOW',
    'For': 'CONTROL_FLOW',
    'While': 'CONTROL_FLOW',
    'Try': 'CONTROL_FLOW',
    'Break': 'CONTROL_FLOW',
    'Continue': 'CONTROL_FLOW',
    
    # Expressions
    'Call': 'EXPRESSION',
    'Name': 'EXPRESSION',
    'Attribute': 'EXPRESSION',
    'Subscript': 'EXPRESSION',
    
    # Statements
    'Assign': 'STATEMENT',
    'AugAssign': 'STATEMENT',
    'Return': 'STATEMENT',
    'Import': 'STATEMENT',
    
    # Operators
    'Add': 'OPERATOR',
    'Sub': 'OPERATOR',
    'Mult': 'OPERATOR',
    'Div': 'OPERATOR',
    
    # Literals
    'Constant': 'LITERAL',
    'List': 'LITERAL',
    'Dict': 'LITERAL',
    'Set': 'LITERAL',
}

# Node type explanations
NODE_EXPLANATIONS = {
    'FunctionDef': 'Function definition (def keyword)',
    'ClassDef': 'Class definition (class keyword)',
    'If': 'If statement for conditional execution',
    'For': 'For loop for iteration',
    'While': 'While loop for conditional iteration',
    'Call': 'Function or method call',
    'Name': 'Variable or function name',
    'Constant': 'Literal value (number, string, etc.)',
    'Return': 'Return statement',
    'Assign': 'Assignment statement (=)',
    'BinOp': 'Binary operation (+, -, *, etc.)',
    'Compare': 'Comparison operation (==, !=, etc.)',
    'Attribute': 'Attribute access (obj.attr)',
}

#################

class Colors:
    RESET = '\033[0m'
    STATEMENT = '\033[92m'      # bright green
    EXPRESSION = '\033[94m'     # bright blue
    CONTROL_FLOW = '\033[95m'   # bright magenta
    DEFINITION = '\033[96m'     # bright cyan
    OPERATOR = '\033[93m'       # bright yellow
    LITERAL = '\033[91m'        # bright red
    ATTRIBUTE = '\033[97m'      # bright white

NODE_CATEGORIES = {
    'FunctionDef': 'DEFINITION',
    'ClassDef': 'DEFINITION',
    'AsyncFunctionDef': 'DEFINITION',
    'If': 'CONTROL_FLOW',
    'For': 'CONTROL_FLOW',
    'While': 'CONTROL_FLOW',
    'Call': 'EXPRESSION',
    'Name': 'EXPRESSION',
    'Attribute': 'EXPRESSION',
    'Constant': 'LITERAL',
    'Return': 'STATEMENT',
    'Assign': 'STATEMENT',
    'Add': 'OPERATOR',
    'Sub': 'OPERATOR',
    'Mult': 'OPERATOR',
}

NODE_EXPLANATIONS = {
    'Module': 'Root node of the AST',
    'FunctionDef': 'Function definition (def keyword)',
    'ClassDef': 'Class definition (class keyword)',
    'If': 'If statement for conditional execution',
    'For': 'For loop for iteration',
    'Call': 'Function or method call',
    'Name': 'Variable or function name',
    'Constant': 'Literal value (number, string, etc.)',
    'Return': 'Return statement',
    'Assign': 'Assignment statement (=)',
    'arguments': 'Function arguments definition',
    'arg': 'Single function argument',
}

def colorize(node_type: str, text: str) -> str:
    """Add color to node text based on its type."""
    category = NODE_CATEGORIES.get(node_type, 'ATTRIBUTE')
    color = getattr(Colors, category)
    return f"{color}{text}{Colors.RESET}"

def get_explanation(node_type: str, show_explanations: bool) -> str:
    """Get explanation for node type if enabled."""
    if not show_explanations:
        return ''
    explanation = NODE_EXPLANATIONS.get(node_type, '')
    if explanation:
        return f' # {explanation}'
    return ''

def ast_to_dict(node):
    """Convert AST node to dictionary representation."""
    if isinstance(node, ast.AST):
        fields = {}
        for name, value in ast.iter_fields(node):
            fields[name] = ast_to_dict(value)
        return {'type': node.__class__.__name__, 'fields': fields}
    elif isinstance(node, list):
        return [ast_to_dict(x) for x in node]
    else:
        return node

def prettify_dict(node_dict: dict, indent_level: int = 0, show_explanations: bool = False) -> str:
    """Create a prettified string representation of the AST dictionary."""
    indent = "  " * indent_level
    node_type = node_dict['type']
    fields = node_dict['fields']
    
    # Start the node representation
    result = [colorize(node_type, node_type)]
    explanation = get_explanation(node_type, show_explanations)
    if explanation:
        result[0] += explanation
    
    # If there are no fields, return just the node type
    if not fields:
        return "".join(result)
    
    result[0] += "("
    
    # Process fields
    field_strs = []
    for name, value in fields.items():
        field_str = indent + "  "  # Extra indent for fields
        
        # Handle different types of values
        if isinstance(value, dict):
            field_str += f"{name}={prettify_dict(value, indent_level + 1, show_explanations)}"
        elif isinstance(value, list):
            if not value:
                field_str += f"{name}=[]"
            else:
                items = [prettify_dict(item, indent_level + 2, show_explanations) 
                        if isinstance(item, dict) 
                        else repr(item) 
                        for item in value]
                field_str += f"{name}=[\n{indent}    " + f",\n{indent}    ".join(items) + "\n" + indent + "  ]"
        else:
            field_str += f"{name}={repr(value)}"
        field_strs.append(field_str)
    
    if field_strs:
        result.append("\n" + ",\n".join(field_strs))
        result.append("\n" + indent + ")")
    else:
        result.append(")")
    
    return "".join(result)

def print_ast(code: str, show_explanations: bool = False):
    """Parse and print a prettified AST for the given code."""
    tree = ast.parse(code)
    dict_tree = ast_to_dict(tree)
    print(prettify_dict(dict_tree, show_explanations=show_explanations))
