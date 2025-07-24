import json
import ast
import os
import sys
import logging
from datetime import datetime

# Set up logging to focus on errors/warnings with instructional messages
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dependency_scan.log')
logging.basicConfig(
    level=logging.WARNING,  # Only log WARNING and ERROR levels
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),  # Log to file with UTF-8 encoding
        logging.StreamHandler(sys.stdout)  # Also print to console
    ]
)

# Visitor to extract import statements from the AST
class ImportVisitor(ast.NodeVisitor):
    def __init__(self):
        self.imports = []
        self.file_path = ""

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append({"import": alias.name, "as": alias.asname})
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            if alias.name == '*':
                logging.warning(f"{self.file_path}: You need to avoid wildcard imports from {node.module} for clarity.")
            self.imports.append({"from": node.module, "import": alias.name, "as": alias.asname})
        self.generic_visit(node)

# Visitor to extract used names and attribute accesses from the AST
class UsageVisitor(ast.NodeVisitor):
    def __init__(self):
        self.names = set()
        self.attributes = set()

    def visit_Name(self, node):
        self.names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        full_name = self.get_full_name(node)
        self.attributes.add(full_name)
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            full_name = self.get_full_name(node.func)
            self.attributes.add(full_name)
        self.generic_visit(node)

    def get_full_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self.get_full_name(node.value)}.{node.attr}"
        return ""

# Function to check if a file aligns with its dependency map details
def check_file_alignment(file_path, file_details):
    # Check if the file exists
    if not os.path.exists(file_path):
        dir_path = os.path.dirname(file_path)
        expected_file = os.path.basename(file_path)
        # Suggest correction for potential typo (e.g., test_test_ -> test_)
        if expected_file.startswith('test_test_'):
            possible_file = expected_file.replace('test_test_', 'test_')
            possible_path = os.path.join(dir_path, possible_file)
            if os.path.exists(possible_path):
                logging.error(f"{file_path}: You need to update the dependency map to reference {possible_file} instead of {expected_file}.")
            else:
                logging.error(f"{file_path}: You need to create the file {expected_file} as it does not exist.")
        else:
            logging.error(f"{file_path}: You need to create the file {expected_file} as it does not exist.")
        return

    # Read and parse the file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        logging.error(f"{file_path}: You need to fix the file access issue: {e}")
        return

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        logging.error(f"{file_path}: You need to correct the syntax error: {e}")
        return

    # Extract imports
    import_visitor = ImportVisitor()
    import_visitor.file_path = file_path
    import_visitor.visit(tree)
    actual_imports = import_visitor.imports

    # Extract definitions (classes and functions)
    defined_classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
    defined_functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    defined = defined_classes.union(defined_functions)

    # Extract used names and attribute accesses
    usage_visitor = UsageVisitor()
    usage_visitor.visit(tree)
    used_names = usage_visitor.names
    attributes = usage_visitor.attributes

    # Check specified imports
    expected_imports = file_details.get("imports", [])
    for exp_imp in expected_imports:
        if not any(all(imp.get(key) == exp_imp.get(key) for key in exp_imp) for imp in actual_imports):
            logging.warning(f"{file_path}: You need to reference the import {exp_imp}.")

    # Check external dependencies
    external = set(file_details.get("external", []))
    for ext in external:
        if not any(imp.get("import") == ext or (imp.get("from") or '').startswith(ext) for imp in actual_imports):
            logging.warning(f"{file_path}: You need to reference the external library {ext}.")

    # Check provided definitions
    provides = set(file_details.get("provides", []))
    for prov in provides:
        if prov not in defined:
            logging.warning(f"{file_path}: You need to define the class or function {prov}.")

    # Check specified uses
    uses = file_details.get("uses", [])
    for use in uses:
        if '.' not in use:
            if use not in used_names:
                logging.warning(f"{file_path}: You need to use the name {use}.")
        else:
            if use not in attributes:
                logging.warning(f"{file_path}: You need to use the attribute access {use}.")

# Main function to process the dependency map and check the codebase
def main(dependency_map_path, codebase_root):
    # Load the dependency map
    try:
        with open(dependency_map_path, 'r', encoding='utf-8') as f:
            dependency_map = json.load(f)
    except Exception as e:
        logging.error(f"You need to fix the dependency map loading issue for {dependency_map_path}: {e}")
        sys.exit(1)

    # Process backend modules and files
    backend_dir = os.path.join(codebase_root, 'backend')
    if not os.path.exists(backend_dir):
        logging.error(f"You need to create the backend directory at {backend_dir}.")
        sys.exit(1)

    for module, module_details in dependency_map['backend']['modules'].items():
        # Validate module name to avoid using filenames as modules
        if module.endswith('.py'):
            logging.warning(f"Invalid module name '{module}' in dependency map: You need to use a directory name (e.g., 'code_generation'), not a filename like '{module}'. Consider moving '{list(module_details['files'].keys())[0]}' to a root module (e.g., '') if it’s a top-level file.")
            continue
        # Handle root-level files (e.g., main.py, __init__.py) under an empty module
        module_path = os.path.join(backend_dir, module) if module else backend_dir
        if not os.path.exists(module_path) and module:
            logging.warning(f"You may need to create the module directory {module_path}.")
            continue
        for file, file_details in module_details['files'].items():
            file_path = os.path.join(module_path, file)
            check_file_alignment(file_path, file_details)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python check_alignment.py <dependency_map.json> <codebase_root>")
        sys.exit(1)

    dependency_map_path = sys.argv[1]
    codebase_root = sys.argv[2]
    main(dependency_map_path, codebase_root)