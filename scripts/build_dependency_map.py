import os
import ast
import json
from pathlib import Path
import re
import pathspec

# Standard library modules to exclude from external dependencies
standard_lib = {
    'os', 'sys', 'json', 'ast', 'pathlib', 're', 'time', 'datetime', 'logging', 'sqlite3', 'fastapi', 'uvicorn'
}

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

def parse_python_file(file_path):
    """Parse a Python file for imports, provides, uses, and external dependencies."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Warning: Syntax error in {file_path}: {e}")
        return {"provides": [], "imports": [], "uses": [], "external": [], "description": "Syntax error detected"}

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
    """Parse a JavaScript file for imports and requires."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        imports = re.findall(r"from\s+['\"]([^'\"]+)['\"]", content)
        requires = re.findall(r"require\(['\"]([^'\"]+)['\"]\)", content)
        return {
            "provides": [],  # Requires JS parser for accuracy
            "imports": imports,
            "requires": requires,
            "external": list(set(imports + requires)),
            "description": f"Handles {os.path.basename(file_path).split('.')[0]} functionality in the {os.path.basename(os.path.dirname(file_path))} module."
        }
    except Exception as e:
        print(f"Warning: Error parsing {file_path}: {e}")
        return {"provides": [], "imports": [], "requires": [], "external": [], "description": "Parse error"}

def parse_html_file(file_path):
    """Parse an HTML file for script dependencies."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        scripts = re.findall(r'<script\s+src=["\'](.*?)["\']', content)
        return {
            "provides": [],
            "imports": scripts,
            "requires": [],
            "external": scripts,
            "description": f"HTML entry point for {os.path.basename(file_path).split('.')[0]}"
        }
    except Exception as e:
        print(f"Warning: Error parsing {file_path}: {e}")
        return {"provides": [], "imports": [], "requires": [], "external": [], "description": "Parse error"}

def build_dependency_map(root_dir):
    """Build a dependency map from the codebase, excluding ignored files."""
    spec = load_gitignore(root_dir)
    dependency_map = {
        "backend": {"modules": {}, "routes": {}},
        "frontend": {"files": {}},
        "inter_component_dependencies": []
    }

    # Ensure we're looking in the right directories
    backend_dir = os.path.join(root_dir, 'backend')
    frontend_dir = os.path.join(root_dir, 'frontend')

    if not os.path.exists(backend_dir):
        print(f"Warning: Backend directory not found at {backend_dir}")
    if not os.path.exists(frontend_dir):
        print(f"Warning: Frontend directory not found at {frontend_dir}")

    # Walk through the directory
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if not should_ignore(os.path.join(dirpath, d), root_dir, spec)]
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if should_ignore(file_path, root_dir, spec):
                print(f"Skipping ignored file: {file_path}")
                continue

            rel_path = os.path.relpath(file_path, root_dir).replace(os.sep, '/')
            print(f"Processing file: {rel_path}")

            # Handle backend Python files
            if 'backend' in rel_path.split('/') and filename.endswith('.py'):
                # Determine the module (e.g., 'code_generation', 'task_management')
                parts = rel_path.split('/')
                module_index = parts.index('backend') + 1
                module = parts[module_index] if module_index < len(parts) else 'root'
                if module not in dependency_map["backend"]["modules"]:
                    dependency_map["backend"]["modules"][module] = {"files": {}, "depends_on": []}
                file_data = parse_python_file(file_path)
                dependency_map["backend"]["modules"][module]["files"][filename] = file_data
                # Infer depends_on
                for imp in file_data["imports"]:
                    if imp.get("from"):
                        module_dep = imp["from"].split('.')[0]
                        if module_dep in dependency_map["backend"]["modules"] and module_dep != module:
                            dependency_map["backend"]["modules"][module]["depends_on"].append(module_dep)
                # Detect FastAPI routes
                if 'fastapi' in file_data["external"]:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        routes = re.findall(r'@app\.(get|post|put|delete)\(["\'](/[^"\']+)["\']\)', content)
                        for method, path in routes:
                            handler_func = "unknown_handler"
                            for node in ast.walk(ast.parse(content)):
                                if isinstance(node, ast.FunctionDef):
                                    handler_func = node.name
                                    break
                            dependency_map["backend"]["routes"][path] = {
                                "method": method.upper(),
                                "handler": f"{module}.{filename.split('.')[0]}.{handler_func}",
                                "description": f"{method.upper()} endpoint for {path}"
                            }

            # Handle frontend files
            elif 'frontend' in rel_path.split('/'):
                if filename.endswith('.js'):
                    dependency_map["frontend"]["files"][rel_path] = parse_js_file(file_path)
                elif filename.endswith('.html'):
                    dependency_map["frontend"]["files"][rel_path] = parse_html_file(file_path)

    # Build inter-component dependencies
    dependency_map["inter_component_dependencies"] = [
        {
            "from": "frontend",
            "to": "backend",
            "via": "HTTP API calls",
            "endpoints": [{"path": path, "method": data["method"], "description": data["description"]}
                         for path, data in dependency_map["backend"]["routes"].items()]
        }
    ]

    # Save the dependency map
    output_path = os.path.join(root_dir, 'dependency_map.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dependency_map, f, indent=4, ensure_ascii=False)
    print(f"Dependency map generated and saved as {output_path}")

if __name__ == "__main__":
    # Use the parent directory of the script to find my_ide_project
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.join(script_dir, 'my_ide_project') if os.path.basename(script_dir) != 'my_ide_project' else script_dir
    if not os.path.exists(root_dir):
        print(f"Error: Root directory {root_dir} does not exist. Please ensure the script is in or above my_ide_project.")
        exit(1)
    build_dependency_map(root_dir)