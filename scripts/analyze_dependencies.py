import os
import ast
import json
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path
import re
import pathspec
import uuid
import importlib.util
import subprocess

# Standard library modules to exclude from external dependencies
standard_lib = {
    'os', 'sys', 'json', 'ast', 'pathlib', 're', 'time', 'datetime', 'logging', 'sqlite3', 'fastapi', 'uvicorn'
}

def setup_logging(output_dir, verbose=False):
    """Set up logging with the specified verbosity."""
    level = logging.DEBUG if verbose else logging.WARNING
    log_file = os.path.join(output_dir, 'dependency_scan.log')
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8', mode='w'),  # Overwrite log file each run
            logging.StreamHandler(sys.stdout)  # Also print to console
        ]
    )
    return log_file

def check_and_install_dependencies():
    """Check if required dependencies are installed, and install them if missing with user confirmation."""
    required_packages = {
        'esprima': 'esprima',
        'beautifulsoup4': 'beautifulsoup4'
    }
    missing_packages = []

    for pkg_name, module_name in required_packages.items():
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            missing_packages.append(pkg_name)

    if missing_packages:
        logging.warning(f"The following required packages are missing: {', '.join(missing_packages)}")
        response = input("Would you like to install the missing packages now? (yes/no): ").lower().strip()
        if response == 'yes':
            for pkg in missing_packages:
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg])
                    logging.info(f"Successfully installed {pkg}")
                except subprocess.CalledProcessError as e:
                    logging.error(f"Failed to install {pkg}: {e}")
                    sys.exit(1)
        else:
            logging.error("Cannot proceed without required packages. Please install them manually using 'pip install esprima beautifulsoup4' and rerun the script.")
            sys.exit(1)

    # Import the modules to ensure they work after installation
    try:
        import esprima
        from bs4 import BeautifulSoup
    except ImportError as e:
        logging.error(f"Failed to import dependencies after installation attempt: {e}")
        sys.exit(1)

# --- Dependency Map Building Functions ---

def load_gitignore(root_dir):
    """Load .gitignore patterns using pathspec for accurate exclusion."""
    gitignore_path = os.path.join(root_dir, '.gitignore')
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            patterns = f.readlines()
        return pathspec.PathSpec.from_lines('gitwildmatch', [p.strip() for p in patterns if p.strip() and not p.startswith('#')])
    return None

def should_ignore(path, root_dir, spec):
    """Check if a path should be ignored based on .gitignore."""
    if spec is None:
        return False
    rel_path = os.path.relpath(path, start=root_dir).replace(os.sep, '/')
    return spec.match_file(rel_path)

# Language-specific parsers
def parse_python_file(file_path):
    """Parse a Python file for imports, provides, uses, and external dependencies."""
    if not file_path.lower().endswith('.py'):
        return {"provides": [], "imports": [], "uses": [], "external": [], "description": "Non-Python file skipped"}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
    except SyntaxError as e:
        logging.warning(f"Syntax error in {file_path}: {e}")
        return {"provides": [], "imports": [], "uses": [], "external": [], "description": f"Syntax error detected: {e}"}

    imports = []
    uses = set()
    external = set()
    provides = set()
    imported_names = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                alias = name.asname or name.name
                imported_names[alias] = name.name
                imports.append({"import": name.name, "as": name.asname})
                top_level = name.name.split('.')[0]
                if top_level not in standard_lib:
                    external.add(top_level)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for name in node.names:
                alias = name.asname or name.name
                full_name = f"{module}.{name.name}" if module else name.name
                imported_names[alias] = full_name
                imports.append({"from": module, "import": name.name, "as": name.asname})
                top_level = module.split('.')[0] if module else ''
                if top_level and top_level not in standard_lib:
                    external.add(top_level)

        if isinstance(node, ast.ClassDef):
            provides.add(node.name)
        elif isinstance(node, ast.FunctionDef):
            provides.add(node.name)

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                value = node.func.value
                attr = node.func.attr
                if isinstance(value, ast.Name) and value.id in imported_names:
                    uses.add(f"{imported_names[value.id]}.{attr}")
            elif isinstance(node.func, ast.Name) and node.func.id in imported_names:
                uses.add(imported_names[node.func.id])

    description = "No docstring"  # Default if no docstring found
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Str):
        description = tree.body[0].value.s.strip() or description
    if description == "No docstring":
        file_name = os.path.basename(file_path).split('.')[0]
        description = f"Handles {file_name} functionality in the {os.path.basename(os.path.dirname(file_path))} module."

    return {
        "provides": list(provides),
        "imports": imports,
        "uses": list(uses),
        "external": list(external),
        "description": description
    }

def parse_js_file(file_path):
    """Parse a JavaScript file for imports and requires using esprima."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = esprima.parseModule(content, {'loc': True})
        imports = []
        requires = []
        external = set()

        for node in tree.body:
            if node.type == 'ImportDeclaration':
                source = node.source.value
                imports.append(source)
                external.add(source)
            elif node.type == 'ExpressionStatement' and node.expression.type == 'CallExpression':
                if node.expression.callee.name == 'require':
                    source = node.expression.arguments[0].value
                    requires.append(source)
                    external.add(source)

        return {
            "provides": [],  # Could parse for exports if needed
            "imports": imports,
            "requires": requires,
            "external": list(external),
            "description": f"Handles {os.path.basename(file_path).split('.')[0]} functionality in the {os.path.basename(os.path.dirname(file_path))} module."
        }
    except Exception as e:
        logging.warning(f"Error parsing {file_path}: {e}")
        return {"provides": [], "imports": [], "requires": [], "external": [], "description": "Parse error"}

def parse_html_file(file_path):
    """Parse an HTML file for script dependencies using BeautifulSoup."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        soup = BeautifulSoup(content, 'html.parser')
        scripts = [tag['src'] for tag in soup.find_all('script') if tag.get('src')]
        return {
            "provides": [],
            "imports": scripts,
            "requires": [],
            "external": scripts,
            "description": f"HTML entry point for {os.path.basename(file_path).split('.')[0]}"
        }
    except Exception as e:
        logging.warning(f"Error parsing {file_path}: {e}")
        return {"provides": [], "imports": [], "requires": [], "external": [], "description": "Parse error"}

# Map file extensions to parsers
FILE_PARSERS = {
    '.py': parse_python_file,
    '.js': parse_js_file,
    '.html': parse_html_file
}

def build_dependency_map(root_dir, output_path=None):
    """Build a dependency map from the codebase, excluding ignored files."""
    logging.info(f"Building dependency map for codebase at {root_dir}...")
    spec = load_gitignore(root_dir)
    dependency_map = {
        "files": {},  # Store all files with their relative paths
        "inter_component_dependencies": []  # Can be populated if needed
    }

    # Walk the entire project and parse files
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if not should_ignore(os.path.join(dirpath, d), root_dir, spec)]
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if should_ignore(file_path, root_dir, spec):
                logging.debug(f"Skipping ignored file: {file_path}")
                continue

            rel_path = os.path.relpath(file_path, root_dir).replace(os.sep, '/')
            logging.debug(f"Processing file: {rel_path}")

            # Determine the parser based on file extension
            ext = os.path.splitext(filename)[1].lower()
            parser = FILE_PARSERS.get(ext)
            if parser:
                file_data = parser(file_path)
                dependency_map["files"][rel_path] = file_data
            else:
                logging.debug(f"No parser available for file: {rel_path}")

    # Example: Add inter-component dependencies (can be expanded based on project needs)
    dependency_map["inter_component_dependencies"] = [
        {
            "from": "frontend",
            "to": "backend",
            "via": "HTTP API calls",
            "endpoints": []  # Populate if needed
        }
    ]

    output_path = output_path or os.path.join(root_dir, 'dependency_map.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dependency_map, f, indent=4, ensure_ascii=False)
    logging.info(f"Dependency map generated and saved as {output_path}")
    return output_path

# --- Dependency Scan Functions ---

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

def check_file_alignment(file_path, file_details):
    """Check if a file aligns with its dependency map details."""
    if not os.path.exists(file_path):
        expected_file = os.path.basename(file_path)
        logging.error(f"{file_path}: You need to create the file {expected_file} as it does not exist.")
        return

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

    import_visitor = ImportVisitor()
    import_visitor.file_path = file_path
    import_visitor.visit(tree)
    actual_imports = import_visitor.imports

    defined_classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
    defined_functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    defined = defined_classes.union(defined_functions)

    usage_visitor = UsageVisitor()
    usage_visitor.visit(tree)
    used_names = usage_visitor.names
    attributes = usage_visitor.attributes

    expected_imports = file_details.get("imports", [])
    for exp_imp in expected_imports:
        if isinstance(exp_imp, dict):
            if not any(all(imp.get(key) == exp_imp.get(key) for key in exp_imp) for imp in actual_imports):
                logging.warning(f"{file_path}: You need to reference the import {exp_imp}.")
        else:
            # For frontend files, imports are strings
            if not any(imp.get("import") == exp_imp or (imp.get("from") or '') == exp_imp for imp in actual_imports):
                logging.warning(f"{file_path}: You need to reference the import {exp_imp}.")

    external = set(file_details.get("external", []))
    for ext in external:
        if not any(imp.get("import") == ext or (imp.get("from") or '').startswith(ext) for imp in actual_imports):
            logging.warning(f"{file_path}: You need to reference the external library {ext}.")

    provides = set(file_details.get("provides", []))
    for prov in provides:
        if prov not in defined:
            logging.warning(f"{file_path}: You need to define the class or function {prov}.")

    uses = file_details.get("uses", [])
    for use in uses:
        if '.' not in use:
            if use not in used_names:
                logging.warning(f"{file_path}: You need to use the name {use}.")
        else:
            if use not in attributes:
                logging.warning(f"{file_path}: You need to use the attribute access {use}.")

def scan_dependencies(dependency_map_path, codebase_root, log_file):
    """Process the dependency map and check the codebase for missing/incorrect references."""
    logging.info(f"Starting dependency scan using dependency map at {dependency_map_path}...")
    try:
        with open(dependency_map_path, 'r', encoding='utf-8') as f:
            dependency_map = json.load(f)
    except Exception as e:
        logging.error(f"You need to fix the dependency map loading issue for {dependency_map_path}: {e}")
        sys.exit(1)

    # Scan all files in the dependency map
    for rel_path, file_details in dependency_map.get("files", {}).items():
        file_path = os.path.join(codebase_root, rel_path.replace('/', os.sep))
        if os.path.exists(file_path) and file_path.lower().endswith('.py'):
            check_file_alignment(file_path, file_details)
        else:
            logging.warning(f"Skipping dependency alignment check for non-Python or missing file: {file_path}")

    logging.info(f"Dependency scan completed. Log saved to {log_file}")

# --- Header Update Functions ---

def generate_file_key():
    """Generate a unique random UUID as the file key."""
    return f"header_key_{uuid.uuid4().hex}"

def load_or_create_header_keys(project_root):
    """Load existing header keys or create a new dictionary."""
    keys_file = os.path.join(project_root, 'header_keys.json')
    if os.path.exists(keys_file):
        with open(keys_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_header_keys(project_root, header_keys):
    """Save the header keys to a JSON file."""
    keys_file = os.path.join(project_root, 'header_keys.json')
    with open(keys_file, 'w', encoding='utf-8') as f:
        json.dump(header_keys, f, indent=4)

def format_dependencies(file_details):
    """Format the dependencies into a readable string."""
    output = []
    # Handle imports (different format for Python vs. frontend files)
    if file_details.get("imports"):
        output.append("Imports:")
        imports = file_details["imports"]
        if imports and isinstance(imports[0], dict):  # Python files
            for imp in imports:
                if "from" in imp:
                    output.append(f"  - from {imp['from']} import {imp['import']} as {imp['as'] or imp['import']}")
                else:
                    output.append(f"  - import {imp['import']} as {imp['as'] or imp['import']}")
        else:  # Frontend files (list of strings)
            for imp in imports:
                output.append(f"  - {imp}")

    # Handle uses (same format for all file types)
    if file_details.get("uses"):
        output.append("Uses:")
        for use in file_details["uses"]:
            output.append(f"  - {use}")

    # Handle external dependencies (same format for all file types)
    if file_details.get("external"):
        output.append("External Dependencies:")
        for ext in file_details["external"]:
            output.append(f"  - {ext}")

    return "\n".join(output) if output else "No dependencies found."

def get_comment_syntax(file_path):
    """Determine the appropriate comment block syntax based on file extension."""
    ext = file_path.lower().split('.')[-1]
    comment_syntax = {
        'py': ('"""', '"""'),
        'js': ('/**', '*/'),
        'html': ('<!--', '-->'),
    }
    return comment_syntax.get(ext, (None, None))

def remove_duplicate_headers(full_content, file_key, start_comment, end_comment):
    """Remove all existing header blocks with the given file key, keeping only the last one."""
    start_pattern = f"{re.escape(start_comment)}\\s*#{re.escape(file_key)}_start"
    end_pattern = f"#{re.escape(file_key)}_end\\s*{re.escape(end_comment)}"
    
    # Find all header blocks
    start_matches = list(re.finditer(start_pattern, full_content, re.MULTILINE))
    end_matches = list(re.finditer(end_pattern, full_content, re.MULTILINE))

    if len(start_matches) != len(end_matches):
        logging.warning(f"Mismatched header markers in content (start: {len(start_matches)}, end: {len(end_matches)}). Cleaning up.")
        return full_content  # Skip if markers are mismatched

    if not start_matches:
        return full_content  # No headers to remove

    # If there are multiple headers, keep the last one and remove the others
    new_content = full_content
    for i in range(len(start_matches) - 1):  # Remove all but the last header
        start_pos = start_matches[i].start()
        end_pos = end_matches[i].end()
        new_content = new_content[:start_pos] + new_content[end_pos:]

    return new_content

def add_or_update_header(file_path, rel_path, file_details, header_keys):
    """Add or update a comment block header in the file using a unique UUID key."""
    start_comment, end_comment = get_comment_syntax(file_path)
    if not start_comment or not end_comment:
        logging.warning(f"Skipping {rel_path}: Unsupported file type for header.")
        return

    # Get or generate the unique file key
    file_key = header_keys.get(rel_path)
    if not file_key:
        file_key = generate_file_key()
        header_keys[rel_path] = file_key
        logging.debug(f"Assigned new key {file_key} to {rel_path}")
    else:
        logging.debug(f"Reusing existing key {file_key} for {rel_path}")

    # Format the new header
    deps_formatted = format_dependencies(file_details)
    deps_lines = deps_formatted.split('\n')
    header_lines = [
        f"{start_comment}",
        f"# {file_key}_start",
        f"#",
        f"# File: {rel_path}",
        f"# Dependencies:",
    ] + [f"# {line}" for line in deps_lines] + [
        f"#",
        f"# {file_key}_end",
        f"{end_comment}\n"
    ]
    new_header = [line + "\n" for line in header_lines]

    # Read existing content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.readlines()
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return

    full_content = ''.join(content)

    # Remove any duplicate headers, keeping the last one
    full_content = remove_duplicate_headers(full_content, file_key, start_comment, end_comment)

    # Look for existing header using the file key
    header_start_pattern = re.compile(f"{re.escape(start_comment)}\\s*#{re.escape(file_key)}_start", re.MULTILINE)
    header_end_pattern = re.compile(f"#{re.escape(file_key)}_end\\s*{re.escape(end_comment)}", re.MULTILINE)

    start_match = header_start_pattern.search(full_content)
    end_match = header_end_pattern.search(full_content)

    if start_match and end_match:
        # Replace the existing header
        start_pos = start_match.start()
        end_pos = end_match.end()
        new_content = full_content[:start_pos] + ''.join(new_header) + full_content[end_pos:]
    else:
        # No existing header; prepend the new header
        new_content = ''.join(new_header) + full_content

    # Write the updated content back to the file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        logging.debug(f"Updated header in {rel_path}")
    except Exception as e:
        logging.error(f"Error writing to {file_path}: {e}")

def find_dependency_map(project_root):
    """Search the project root and subdirectories for dependency_map.json."""
    for dirpath, dirnames, filenames in os.walk(project_root):
        if 'dependency_map.json' in [f.lower() for f in filenames]:
            path = os.path.join(dirpath, 'dependency_map.json')
            logging.info(f"Found dependency map at: {path}")
            return path
    logging.error(f"Could not find dependency_map.json in {project_root} or its subdirectories.")
    return None

def list_files_in_directory(directory):
    """List all files in the directory and its subdirectories with supported extensions."""
    supported_extensions = ('.py', '.js', '.html')
    found_files = []
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if filename.lower().endswith(supported_extensions):
                rel_path = os.path.relpath(os.path.join(dirpath, filename), directory).replace(os.sep, '/')
                found_files.append(rel_path)
    return found_files

def process_files(project_root, dependency_map_path=None):
    """Process files and add/update headers based on the dependency map."""
    # Determine the dependency map path
    if not dependency_map_path:
        dependency_map_path = find_dependency_map(project_root)
        if not dependency_map_path:
            return
    else:
        dependency_map_path = os.path.abspath(dependency_map_path)

    # Load the dependency map
    try:
        with open(dependency_map_path, 'r', encoding='utf-8') as f:
            dependency_map = json.load(f)
    except Exception as e:
        logging.error(f"Error loading dependency map {dependency_map_path}: {e}")
        return

    # Load or create header keys
    header_keys = load_or_create_header_keys(project_root)

    # Track processed files to avoid duplicates
    processed_files = set()
    dependency_map_files = set()

    # Process all files from the dependency map
    for rel_path, file_details in dependency_map.get("files", {}).items():
        file_path = os.path.join(project_root, rel_path.replace('/', os.sep))
        if rel_path in processed_files:
            logging.warning(f"Skipping duplicate entry for {rel_path} in dependency map.")
            continue
        processed_files.add(rel_path)
        dependency_map_files.add(rel_path)
        if os.path.exists(file_path):
            logging.debug(f"Processing file: {rel_path}")
            add_or_update_header(file_path, rel_path, file_details, header_keys)
        else:
            logging.warning(f"File not found on disk: {file_path}")

    # Compare dependency map files with actual files in the project root
    all_files = list_files_in_directory(project_root)
    missing_in_dependency_map = set(all_files) - dependency_map_files
    if missing_in_dependency_map:
        logging.warning("The following files are present in the filesystem but missing in dependency_map.json:")
        for file in sorted(missing_in_dependency_map):
            logging.warning(f"  - {file}")

    # Save updated header keys
    save_header_keys(project_root, header_keys)

# --- Main Execution ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build a dependency map, scan the codebase, and update headers.")
    parser.add_argument("project_root", help="Path to the project root directory")
    parser.add_argument("--map-output", help="Path to save the dependency map (default: <project_root>/dependency_map.json)", default=None)
    parser.add_argument("--log-output", help="Path to save the dependency scan log (default: <project_root>/dependency_scan.log)", default=None)
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging for debugging")

    args = parser.parse_args()

    # Resolve project root directory
    project_root = os.path.abspath(args.project_root)
    if not os.path.exists(project_root):
        logging.error(f"Project root directory {project_root} does not exist.")
        sys.exit(1)

    # Set up logging with the specified or default log output
    log_output_dir = os.path.dirname(args.log_output) if args.log_output else project_root
    if log_output_dir and not os.path.exists(log_output_dir):
        os.makedirs(log_output_dir)
    log_file = setup_logging(log_output_dir, verbose=args.verbose)

    # Check and install dependencies
    check_and_install_dependencies()

    # Step 1: Build the dependency map
    dependency_map_path = build_dependency_map(project_root, output_path=args.map_output)

    # Step 2: Scan dependencies using the generated map
    scan_dependencies(dependency_map_path, project_root, log_file)

    # Step 3: Update headers using the generated map
    process_files(project_root, dependency_map_path)