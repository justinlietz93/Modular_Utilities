import os
import json

# Define the project root directory
PROJECT_DIR = "dependency_analyzer"

# Ensure the project directory exists
if not os.path.exists(PROJECT_DIR):
    os.makedirs(PROJECT_DIR)

# Function to write content to a file
def write_file(filepath, content):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print(f"Created {filepath}")

# README.md
readme_content = """
# Dependency Analyzer

A standalone tool that analyzes dependencies in your codebase, updates live as files change, and runs as a background process.

## Setup
1. Download the executable from the releases page (e.g., dependency-analyzer.exe).
2. Run: `dependency-analyzer <project_root> [--verbose] [--background]`

## Features
- Parses Python, JavaScript/TypeScript/JSX, and HTML files.
- Generates `dependency_map.json`, `dependency_metadata.csv`, and logs in `dependency_tracking/`.
- Updates dependency headers in source files in real-time.
- Runs as a background process with live monitoring.

## Building from Source
1. Install Python dependencies: `pip install -r requirements.txt`
2. Add Node.js: Download Node.js (e.g., v20.17.0) and extract to `dependency_analyzer/nodejs`, then run `nodejs/npm install @babel/parser`.
3. Bundle: `pyinstaller --add-data "src/dependency_analyzer/scripts;dependency_analyzer/scripts" --add-data "nodejs;nodejs" --onefile src/dependency_analyzer/cli.py -n dependency-analyzer`
4. Run: `dist/dependency-analyzer <project_root> --verbose`

## Usage
- Foreground: `dependency-analyzer /path/to/codebase --verbose`
- Background: `dependency-analyzer /path/to/codebase --background`
"""
write_file(os.path.join(PROJECT_DIR, "README.md"), readme_content)

# requirements.txt
requirements_content = """
beautifulsoup4
watchdog
"""
write_file(os.path.join(PROJECT_DIR, "requirements.txt"), requirements_content)

# setup.py (for development, not required for standalone but included for completeness)
setup_py_content = """
from setuptools import setup, find_packages

setup(
    name="dependency-analyzer",
    version="0.1.0",
    description="A comprehensive dependency analyzer with live updates",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "dependency_analyzer": ["scripts/parse_js.js", "nodejs/*"]
    },
    include_package_data=True,
    install_requires=[
        "beautifulsoup4",
        "watchdog"
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "dependency-analyzer = dependency_analyzer.cli:main"
        ]
    }
)
"""
write_file(os.path.join(PROJECT_DIR, "setup.py"), setup_py_content)

# src/dependency_analyzer/scripts/parse_js.js
parse_js_content = r"""
const fs = require('fs');
const parser = require('@babel/parser');
const path = require('path');

const filePath = process.argv[2];

if (!filePath) {
    console.error(JSON.stringify({
        provides: [],
        imports: [],
        requires: [],
        uses: [],
        external: [],
        description: "Error: No file path provided"
    }));
    process.exit(1);
}

try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const ast = parser.parse(content, {
        sourceType: 'module',
        plugins: [
            'jsx',
            'typescript',
            'classProperties',
            'objectRestSpread',
            'export/DefaultFrom',
            'dynamicImport',
            'decorators-legacy',
            'classPrivateProperties',
            'optionalChaining',
            'nullishCoalescingOperator'
        ]
    });

    const fileDir = path.dirname(filePath);
    const normalizeImportPath = (importPath) => {
        if (importPath.startsWith('.')) {
            const absolutePath = path.resolve(fileDir, importPath);
            const relativePath = path.relative(process.cwd(), absolutePath).replace(/\\\/g, '/');
            return relativePath.replace(/^frontend\\//, 'frontend.').replace(/\\//g, '.').replace(/\\.js$/, '').replace(/\\.ts$/, '').replace(/\\.tsx$/, '');
        }
        return importPath;
    };

    const imports = [];
    for (const node of ast.program.body) {
        if (node.type === 'ImportDeclaration') {
            const source = node.source.value;
            const normalizedSource = normalizeImportPath(source);
            node.specifiers.forEach(spec => {
                if (spec.type === 'ImportSpecifier' || spec.type === 'ImportDefaultSpecifier' || spec.type === 'ImportNamespaceSpecifier') {
                    if (spec.local) {
                        imports.push({ from: normalizedSource, import: spec.local.name, as: spec.local.name });
                    }
                }
            });
        }
    }

    const requires = [];
    for (const node of ast.program.body) {
        if (node.type === 'ExpressionStatement' &&
            node.expression.type === 'CallExpression' &&
            node.expression.callee.name === 'require' &&
            node.expression.arguments.length > 0 &&
            node.expression.arguments[0].type === 'StringLiteral') {
            const source = node.expression.arguments[0].value;
            requires.push(normalizeImportPath(source));
        }
    }

    const external = new Set([...imports.map(imp => imp.from), ...requires]);

    const provides = [];
    for (const node of ast.program.body) {
        if (node.type === 'ExportNamedDeclaration' && node.declaration) {
            if (node.declaration.type === 'FunctionDeclaration' || node.declaration.type === 'TSEnumDeclaration') {
                provides.push(node.declaration.id.name);
            } else if (node.declaration.type === 'VariableDeclaration') {
                node.declaration.declarations.forEach(decl => {
                    if (decl.id.type === 'Identifier') {
                        provides.push(decl.id.name);
                    }
                });
            } else if (node.declaration.type === 'TSInterfaceDeclaration' || node.declaration.type === 'TSTypeAliasDeclaration') {
                provides.push(node.declaration.id.name);
            }
        } else if (node.type === 'ExportDefaultDeclaration') {
            if (node.declaration.type === 'Identifier') {
                provides.push(node.declaration.name);
            } else if (node.declaration.type === 'FunctionDeclaration' || 
                      node.declaration.type === 'ClassDeclaration' || 
                      node.declaration.type === 'TSInterfaceDeclaration') {
                provides.push('default');
            }
        } else if (node.type === 'ExpressionStatement' &&
                   node.expression.type === 'AssignmentExpression' &&
                   node.expression.left.type === 'MemberExpression' &&
                   node.expression.left.object.name === 'module' &&
                   node.expression.left.property.name === 'exports') {
            if (node.expression.right.type === 'ObjectExpression') {
                node.expression.right.properties.forEach(prop => {
                    if (prop.key.type === 'Identifier') {
                        provides.push(prop.key.name);
                    }
                });
            } else if (node.expression.right.type === 'Identifier') {
                provides.push(node.expression.right.name);
            }
        }
    }

    const uses = new Set();
    const traverse = (node) => {
        if (!node) return;

        if (node.type === 'CallExpression') {
            if (node.callee.type === 'Identifier') {
                uses.add(node.callee.name);
            } else if (node.callee.type === 'MemberExpression') {
                if (node.callee.property.type === 'Identifier') {
                    uses.add(node.callee.property.name);
                }
            }
        }

        if (node.type === 'JSXElement' && node.openingElement.name.type === 'JSXIdentifier') {
            uses.add(node.openingElement.name.name);
        }

        if (node.type === 'TSCallSignatureDeclaration' && node.typeAnnotation) {
            traverse(node.typeAnnotation);
        }

        if (node.type === 'VariableDeclaration') {
            node.declarations.forEach(decl => {
                if (decl.init && decl.init.type === 'CallExpression') {
                    if (decl.init.callee.type === 'Identifier') {
                        uses.add(decl.init.callee.name);
                    } else if (decl.init.callee.type === 'MemberExpression') {
                        if (decl.init.callee.property.type === 'Identifier') {
                            uses.add(decl.init.callee.property.name);
                        }
                    }
                }
            });
        }

        if (node.type === 'AssignmentExpression') {
            const expr = node.right;
            if (expr && expr.type === 'CallExpression') {
                if (expr.callee.type === 'Identifier') {
                    uses.add(expr.callee.name);
                } else if (expr.callee.type === 'MemberExpression') {
                    if (expr.callee.property.type === 'Identifier') {
                        uses.add(expr.callee.property.name);
                    }
                }
            }
        }

        for (const key in node) {
            if (node[key] && typeof node[key] === 'object') {
                if (Array.isArray(node[key])) {
                    node[key].forEach(child => traverse(child));
                } else {
                    traverse(node[key]);
                }
            }
        }
    };

    traverse(ast);

    const result = {
        provides: provides,
        imports: imports,
        requires: requires,
        uses: Array.from(uses),
        external: Array.from(external),
        description: `Handles ${filePath.split('\\\\').pop().split('.')[0]} in ${filePath.split('\\\\').slice(-2)[0]} module.`
    };
    console.log(JSON.stringify(result));
} catch (e) {
    console.error(JSON.stringify({
        provides: [],
        imports: [],
        requires: [],
        uses: [],
        external: [],
        description: `Parse error: ${e.message} at line ${e.loc?.line || 'unknown'}`
    }));
    process.exit(1);
}
"""
write_file(os.path.join(PROJECT_DIR, "src", "dependency_analyzer", "scripts", "parse_js.js"), parse_js_content)

# src/dependency_analyzer/__init__.py
init_content = """
# Empty file to mark dependency_analyzer as a package
"""
write_file(os.path.join(PROJECT_DIR, "src", "dependency_analyzer", "__init__.py"), init_content)

# src/dependency_analyzer/cli.py
cli_content = """
import argparse
import os
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .utils import setup_logging
from .dependency_map import build_dependency_map, scan_dependencies
from .header_manager import process_files

class CodebaseWatcher(FileSystemEventHandler):
    def __init__(self, project_root, map_output, log_file, tracking_handler):
        self.project_root = project_root
        self.map_output = map_output
        self.log_file = log_file
        self.tracking_handler = tracking_handler

    def on_any_event(self, event):
        if not event.is_directory:
            print(f"Change detected: {event.src_path}")
            map_path = build_dependency_map(self.project_root, self.map_output)
            scan_dependencies(map_path, self.project_root, self.log_file, self.tracking_handler)
            process_files(self.project_root, map_path)

def main():
    parser = argparse.ArgumentParser(description="Live dependency analyzer.")
    parser.add_argument("project_root", help="Project root directory")
    parser.add_argument("--map-output", help="Dependency map output path", default=None)
    parser.add_argument("--log-output", help="Full path to the dependency scan log file", default=None)
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--background", action="store_true", help="Run in background")
    args = parser.parse_args()

    project_root = os.path.abspath(args.project_root)
    if not os.path.exists(project_root):
        print(f"Error: Project root {project_root} does not exist.")
        sys.exit(1)

    dependency_tracking_dir = os.path.join(project_root, 'dependency_tracking')
    log_file_path = args.log_output or os.path.join(dependency_tracking_dir, "dependency_scan.log")
    log_file, tracking_handler = setup_logging(log_file_path, args.verbose)

    print("Initializing Dependency Analyzer...")
    map_path = build_dependency_map(project_root, args.map_output)
    scan_dependencies(map_path, project_root, log_file, tracking_handler)
    process_files(project_root, map_path)

    if args.background:
        print(f"Running in background, logging to {log_file_path}...")
    else:
        print(f"Watching {project_root} for changes...")

    event_handler = CodebaseWatcher(project_root, args.map_output, log_file, tracking_handler)
    observer = Observer()
    observer.schedule(event_handler, project_root, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("Stopped watching.")
    observer.join()

if __name__ == "__main__":
    main()
"""
write_file(os.path.join(PROJECT_DIR, "src", "dependency_analyzer", "cli.py"), cli_content)

# src/dependency_analyzer/config.py
config_content = """
import os
from .file_parsers import parse_python_file, parse_js_file, parse_html_file

# Standard library modules to exclude from external dependencies
STANDARD_LIB = {
    'os', 'sys', 'json', 'ast', 'pathlib', 're', 'time', 'datetime', 'logging', 
    'sqlite3', 'fastapi', 'uvicorn', 'unittest'
}

# File parsers by extension
FILE_PARSERS = {
    '.py': parse_python_file,
    '.js': parse_js_file,
    '.html': parse_html_file
}

# Default output directory
DEPENDENCY_TRACKING_DIR = 'dependency_tracking'
"""
write_file(os.path.join(PROJECT_DIR, "src", "dependency_analyzer", "config.py"), config_content)

# src/dependency_analyzer/file_parsers.py
file_parsers_content = """
import ast
import os
import subprocess
import json
import logging

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

def parse_python_file(file_path):
    if not file_path.lower().endswith('.py'):
        return {"provides": [], "imports": [], "uses": [], "external": [], "description": "Non-Python file"}
    if not os.path.exists(file_path):
        logging.warning(f"File does not exist for parsing: {file_path}")
        return {"provides": [], "imports": [], "uses": [], "external": [], "description": "File not found"}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
    except SyntaxError as e:
        logging.warning(f"Syntax error in {file_path}: {e}")
        return {"provides": [], "imports": [], "uses": [], "external": [], "description": f"Syntax error: {e}"}
    
    from .config import STANDARD_LIB
    imports = []
    uses = set()
    external = set()
    provides = set()
    imported_names = {}
    is_test_file = False
    
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            provides.add(node.name)
            if any(isinstance(base, ast.Name) and base.id == 'TestCase' for base in node.bases):
                is_test_file = True
        elif isinstance(node, ast.FunctionDef):
            provides.add(node.name)
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr in ('get', 'post', 'put', 'delete'):
                        if isinstance(decorator.func.value, ast.Name) and decorator.func.value.id == 'app':
                            uses.add(node.name)
        if isinstance(node, ast.Import):
            for name in node.names:
                alias = name.asname or name.name
                imported_names[alias] = name.name
                imports.append({"import": name.name, "as": name.asname})
                if name.name.split('.')[0] not in STANDARD_LIB:
                    external.add(name.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for name in node.names:
                alias = name.asname or name.name
                full_name = f"{module}.{name.name}" if module else name.name
                imported_names[alias] = full_name
                imports.append({"from": module, "import": name.name, "as": name.asname})
                if module.split('.')[0] not in STANDARD_LIB:
                    external.add(module.split('.')[0])
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id in imported_names:
                    uses.add(f"{imported_names[node.func.value.id]}.{node.func.attr}")
            elif isinstance(node.func, ast.Name) and node.func.id in imported_names:
                uses.add(imported_names[node.func.id])
    
    if is_test_file:
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test'):
                uses.add(node.name)
    
    description = next((n.value.s.strip() for n in tree.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Str)), 
                       f"Handles {os.path.basename(file_path).split('.')[0]} in {os.path.basename(os.path.dirname(file_path))} module.")
    return {"provides": list(provides), "imports": imports, "uses": list(uses), "external": list(external), "description": description}

def parse_js_file(file_path):
    if not os.path.exists(file_path):
        logging.warning(f"File does not exist for parsing: {file_path}")
        return {"provides": [], "imports": [], "requires": [], "uses": [], "external": [], "description": "File not found"}
    try:
        script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'parse_js.js')
        node_path = os.path.join(os.path.dirname(__file__), '..', 'nodejs', 'node.exe' if os.name == 'nt' else 'node')
        if not os.path.exists(script_path) or not os.path.exists(node_path):
            logging.error(f"Missing script {script_path} or Node.js {node_path}")
            return {"provides": [], "imports": [], "requires": [], "uses": [], "external": [], "description": "Node.js setup incomplete"}
        cmd = [node_path, script_path, file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        error_output = result.stderr.strip()
        if error_output:
            logging.error(f"Error parsing {file_path} with Node.js: {error_output}")
            try:
                return json.loads(error_output)
            except json.JSONDecodeError:
                return {"provides": [], "imports": [], "requires": [], "uses": [], "external": [], "description": f"Parse error: {error_output}"}
        return json.loads(output)
    except Exception as e:
        logging.error(f"Unexpected error parsing {file_path}: {e}")
        return {"provides": [], "imports": [], "requires": [], "uses": [], "external": [], "description": f"Parse error: {str(e)}"}

def parse_html_file(file_path):
    if not os.path.exists(file_path):
        logging.warning(f"File does not exist for parsing: {file_path}")
        return {"provides": [], "imports": [], "requires": [], "external": [], "description": "File not found"}
    try:
        if not BeautifulSoup:
            logging.warning(f"Skipping {file_path}: BeautifulSoup not installed.")
            return {"provides": [], "imports": [], "requires": [], "external": [], "description": "HTML parsing skipped"}
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        scripts = [tag['src'] for tag in soup.find_all('script') if tag.get('src')]
        return {"provides": [], "imports": scripts, "requires": [], "external": scripts, 
                "description": f"HTML entry for {os.path.basename(file_path).split('.')[0]}"}
    except Exception as e:
        logging.warning(f"Error parsing {file_path}: {e}")
        return {"provides": [], "imports": [], "requires": [], "external": [], "description": "Parse error"}
"""
write_file(os.path.join(PROJECT_DIR, "src", "dependency_analyzer", "file_parsers.py"), file_parsers_content)

# src/dependency_analyzer/dependency_map.py
dependency_map_content = """
import os
import json
import csv
import logging
from .config import FILE_PARSERS, DEPENDENCY_TRACKING_DIR
from .utils import load_gitignore, should_ignore
from .validators import check_file_alignment

def build_dependency_map(root_dir, output_path=None):
    logging.info(f"Building dependency map for {root_dir}...")
    spec = load_gitignore(root_dir)
    dependency_map = {"files": {}, "inter_component_dependencies": []}
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if not should_ignore(os.path.join(dirpath, d), root_dir, spec)]
        for filename in [f for f in filenames if not should_ignore(os.path.join(dirpath, f), root_dir, spec)]:
            file_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(file_path, root_dir).replace(os.sep, '/')
            ext = os.path.splitext(filename)[1].lower()
            if ext in FILE_PARSERS:
                dependency_map["files"][rel_path] = FILE_PARSERS[ext](file_path)
    
    dependency_map["inter_component_dependencies"] = [
        {"from": "frontend", "to": "backend", "via": "HTTP API calls", "endpoints": []}
    ]
    
    dependency_tracking_dir = os.path.join(root_dir, DEPENDENCY_TRACKING_DIR)
    if not os.path.exists(dependency_tracking_dir):
        os.makedirs(dependency_tracking_dir)
    output_path = output_path or os.path.join(dependency_tracking_dir, 'dependency_map.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dependency_map, f, indent=4, ensure_ascii=False)
    logging.info(f"Dependency map saved to {output_path}")
    return output_path

def scan_dependencies(dependency_map_path, codebase_root, log_file, tracking_handler):
    logging.info(f"Scanning dependencies with map at {dependency_map_path}...")
    try:
        with open(dependency_map_path, 'r', encoding='utf-8') as f:
            dependency_map = json.load(f)
    except Exception as e:
        logging.error(f"Error loading {dependency_map_path}: {e}")
        return

    provides_lookup = {}
    for rel_path, file_details in dependency_map.get("files", {}).items():
        file_path = os.path.normpath(os.path.join(codebase_root, rel_path.replace('/', os.sep)))
        module_name = rel_path.replace('/', '.')[:-3]
        for provided in file_details.get("provides", []):
            provides_lookup[f"{module_name}.{provided}"] = rel_path

    reference_counts = {}
    for rel_path, file_details in dependency_map.get("files", {}).items():
        module_name = rel_path.replace('/', '.')[:-3]
        for prov in file_details.get("provides", []):
            full_item = f"{module_name}.{prov}"
            reference_counts[full_item] = {"count": 0, "locations": []}

    for rel_path, file_details in dependency_map.get("files", {}).items():
        module_name = rel_path.replace('/', '.')[:-3]
        for use in file_details.get("uses", []):
            full_use = f"{module_name}.{use}"
            if full_use in reference_counts:
                reference_counts[full_use]["count"] += 1
                reference_counts[full_use]["locations"].append(rel_path)
        for imp in file_details.get("imports", []):
            if isinstance(imp, dict) and imp.get("from"):
                full_import = f"{imp['from'].replace('/', '.')}.{imp['import']}"
                if full_import in reference_counts:
                    reference_counts[full_import]["count"] += 1
                    reference_counts[full_import]["locations"].append(rel_path)

    dependency_tracking_dir = os.path.join(codebase_root, DEPENDENCY_TRACKING_DIR)
    if not os.path.exists(dependency_tracking_dir):
        os.makedirs(dependency_tracking_dir)
    csv_path = os.path.join(dependency_tracking_dir, 'dependency_metadata.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['full_item', 'count', 'locations']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for full_item, info in reference_counts.items():
            writer.writerow({'full_item': full_item, 'count': info["count"], 'locations': ', '.join(info["locations"])})
    logging.info(f"Dependency metadata saved to {csv_path}")

    for rel_path, file_details in dependency_map.get("files", {}).items():
        file_path = os.path.normpath(os.path.join(codebase_root, rel_path.replace('/', os.sep)))
        if os.path.exists(file_path):
            check_file_alignment(file_path, file_details)

    if not tracking_handler.has_issues():
        logging.info("All dependencies aligned and integrated across files with no unused definitions")
    logging.info(f"Scan completed. Log at {log_file}")
"""
write_file(os.path.join(PROJECT_DIR, "src", "dependency_analyzer", "dependency_map.py"), dependency_map_content)

# src/dependency_analyzer/header_manager.py
header_manager_content = """
import os
import json
import uuid
import re
import logging
from .utils import list_files_in_directory

def generate_file_key():
    return f"header_key_{uuid.uuid4().hex}"

def load_or_create_header_keys(project_root):
    dependency_tracking_dir = os.path.join(project_root, 'dependency_tracking')
    if not os.path.exists(dependency_tracking_dir):
        os.makedirs(dependency_tracking_dir)
    keys_file = os.path.join(dependency_tracking_dir, 'header_keys.json')
    return json.load(open(keys_file, 'r', encoding='utf-8')) if os.path.exists(keys_file) else {}

def save_header_keys(project_root, header_keys):
    dependency_tracking_dir = os.path.join(project_root, 'dependency_tracking')
    with open(os.path.join(dependency_tracking_dir, 'header_keys.json'), 'w', encoding='utf-8') as f:
        json.dump(header_keys, f, indent=4)

def format_dependencies(file_details):
    lines = []
    if file_details.get("imports"):
        lines.append("Imports:")
        imports = file_details["imports"]
        if imports and isinstance(imports[0], dict):
            for imp in imports:
                if "from" in imp:
                    lines.append(f"  - from {imp['from']} import {imp['import']} as {imp['as'] or imp['import']}")
                else:
                    lines.append(f"  - import {imp['import']} as {imp['as'] or imp['import']}")
        else:
            lines.extend(f"  - {imp}" for imp in imports)
    if file_details.get("uses"):
        lines.append("Uses:")
        lines.extend(f"  - {use}" for use in file_details["uses"])
    if file_details.get("external"):
        lines.append("External Dependencies:")
        lines.extend(f"  - {ext}" for ext in file_details["external"])
    return "\\n".join(lines) or "No dependencies found."

def get_comment_syntax(file_path):
    ext = file_path.lower().split('.')[-1]
    return {
        'py': ('"""', '"""'),
        'js': ('/**', '*/'),
        'html': ('<!--', '-->')
    }.get(ext, (None, None))

def remove_existing_headers(full_content, file_key, start_comment, end_comment):
    pattern = (
        f"{re.escape(start_comment)}\\s*\\n"
        f"#\\s{re.escape(file_key)}_start\\s*\\n"
        f"(?:#.*\\n)*?"
        f"#\\s{re.escape(file_key)}_end\\s*\\n"
        f"{re.escape(end_comment)}\\s*\\n?"
    )
    matches = list(re.finditer(pattern, full_content, re.MULTILINE))
    if not matches:
        return full_content
    new_content = full_content
    for match in reversed(matches):
        new_content = new_content[:match.start()] + new_content[match.end():]
    return new_content

def add_or_update_header(file_path, rel_path, file_details, header_keys):
    start_comment, end_comment = get_comment_syntax(file_path)
    if not start_comment:
        logging.warning(f"Skipping {rel_path}: Unsupported file type.")
        return
    file_key = header_keys.setdefault(rel_path, generate_file_key())
    deps = format_dependencies(file_details)
    header = [
        f"{start_comment}\\n",
        f"# {file_key}_start\\n",
        "#\\n",
        f"# File: {rel_path}\\n",
        "# Dependencies:\\n",
    ] + [f"# {line}\\n" for line in deps.split('\\n')] + [
        "#\\n",
        f"# {file_key}_end\\n",
        f"{end_comment}\\n"
    ]
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        content = remove_existing_headers(content, file_key, start_comment, end_comment)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(''.join(header) + content)
        logging.debug(f"Updated header in {rel_path}")
    except Exception as e:
        logging.error(f"Error updating {file_path}: {e}")

def find_dependency_map(project_root):
    dependency_tracking_dir = os.path.join(project_root, 'dependency_tracking')
    map_path = os.path.join(dependency_tracking_dir, 'dependency_map.json')
    return map_path if os.path.exists(map_path) else None

def process_files(project_root, dependency_map_path=None):
    dependency_map_path = dependency_map_path or find_dependency_map(project_root)
    if not dependency_map_path:
        logging.error(f"No dependency_map.json found in {project_root}.")
        return
    try:
        with open(dependency_map_path, 'r', encoding='utf-8') as f:
            dependency_map = json.load(f)
    except Exception as e:
        logging.error(f"Error loading {dependency_map_path}: {e}")
        return
    
    header_keys = load_or_create_header_keys(project_root)
    processed_files = set()
    all_files = set(list_files_in_directory(project_root))
    
    for rel_path, file_details in dependency_map.get("files", {}).items():
        file_path = os.path.normpath(os.path.join(project_root, rel_path.replace('/', os.sep)))
        norm_rel_path = os.path.relpath(file_path, project_root).replace(os.sep, '/')
        if norm_rel_path in processed_files:
            logging.warning(f"Skipping duplicate entry for {norm_rel_path} in dependency map.")
            continue
        processed_files.add(norm_rel_path)
        if os.path.exists(file_path):
            add_or_update_header(file_path, norm_rel_path, file_details, header_keys)
    
    save_header_keys(project_root, header_keys)
"""
write_file(os.path.join(PROJECT_DIR, "src", "dependency_analyzer", "header_manager.py"), header_manager_content)

# src/dependency_analyzer/utils.py
utils_content = """
import os
import sys
import logging
import pathspec

class TrackingHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.warning_or_higher_count = 0

    def emit(self, record):
        if record.levelno >= logging.WARNING:
            self.warning_or_higher_count += 1

    def has_issues(self):
        return self.warning_or_higher_count > 0

def setup_logging(log_file_path, verbose=False):
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    log_dir = os.path.dirname(log_file_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    file_handler = logging.FileHandler(log_file_path, encoding='utf-8', mode='w')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_level = logging.DEBUG if verbose else logging.INFO
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    tracking_handler = TrackingHandler()
    tracking_handler.setLevel(logging.WARNING)
    root_logger.addHandler(tracking_handler)

    root_logger.setLevel(logging.DEBUG)
    logging.debug(f"Logging configured. Log file: {log_file_path}")
    return log_file_path, tracking_handler

def load_gitignore(root_dir):
    gitignore_path = os.path.join(root_dir, '.gitignore')
    patterns = ['node_modules/']
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            patterns.extend([p.strip() for p in f.readlines() if p.strip() and not p.startswith('#')])
    return pathspec.PathSpec.from_lines('gitwildmatch', patterns)

def should_ignore(path, root_dir, spec):
    if not spec:
        return False
    rel_path = os.path.relpath(path, root_dir).replace(os.sep, '/')
    return spec.match_file(rel_path) or 'node_modules' in rel_path.split('/')

def list_files_in_directory(directory):
    supported_extensions = ('.py', '.js', '.html')
    found_files = []
    spec = load_gitignore(directory)
    for dirpath, dirnames, filenames in os.walk(directory):
        dirnames[:] = [d for d in dirnames if not should_ignore(os.path.join(dirpath, d), directory, spec)]
        for filename in filenames:
            if filename.lower().endswith(supported_extensions):
                file_path = os.path.join(dirpath, filename)
                if should_ignore(file_path, directory, spec):
                    continue
                rel_path = os.path.relpath(file_path, directory).replace(os.sep, '/')
                found_files.append(rel_path)
    return found_files
"""
write_file(os.path.join(PROJECT_DIR, "src", "dependency_analyzer", "utils.py"), utils_content)

# src/dependency_analyzer/validators.py
validators_content = """
import ast
import os
import json
import logging
from .file_parsers import parse_js_file

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
                logging.warning(f"{self.file_path}: Avoid wildcard imports from {node.module}.")
            self.imports.append({"from": node.module, "import": alias.name, "as": alias.asname})
        self.generic_visit(node)

class UsageVisitor(ast.NodeVisitor):
    def __init__(self):
        self.names = set()
        self.attributes = set()
        self.variables = {}
    def visit_Name(self, node):
        self.names.add(node.id)
        self.generic_visit(node)
    def visit_Attribute(self, node):
        full_name = self.get_full_name(node)
        self.attributes.add(full_name)
        self.generic_visit(node)
    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            self.attributes.add(self.get_full_name(node.func))
        elif isinstance(node.func, ast.Name):
            self.names.add(node.func.id)
        self.generic_visit(node)
    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Name) and isinstance(node.value, (ast.Name, ast.Attribute)):
            self.variables[node.targets[0].id] = self.get_full_name(node.value)
        self.generic_visit(node)
    def get_full_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self.get_full_name(node.value)}.{node.attr}"
        return ""

def check_file_alignment(file_path, file_details):
    if not os.path.exists(file_path):
        logging.error(f"{file_path}: File does not exist on disk.")
        return

    ext = file_path.lower().split('.')[-1]
    if ext == 'py':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
        except SyntaxError as e:
            logging.error(f"{file_path}: Syntax error: {e}")
            return

        import_visitor = ImportVisitor()
        import_visitor.file_path = file_path
        import_visitor.visit(tree)
        actual_imports = import_visitor.imports

        defined = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                defined.add(node.name)

        usage_visitor = UsageVisitor()
        usage_visitor.visit(tree)
        actual_uses = usage_visitor.names.union(usage_visitor.attributes)
        variable_mappings = usage_visitor.variables

        for exp_imp in file_details.get("imports", []):
            if isinstance(exp_imp, dict):
                imp_key = exp_imp.get("import")
                imp_from = exp_imp.get("from", "")
                imp_as = exp_imp.get("as") or imp_key
                found = any(
                    imp.get("import") == imp_key or
                    (imp.get("from") or "").startswith(imp_from) or
                    imp.get("as") == imp_as
                    for imp in actual_imports
                )
                if not found:
                    logging.warning(f"{file_path}: Potentially missing import {exp_imp} (check aliases or usage).")
        
        for ext in file_details.get("external", []):
            if not any(imp.get("import").startswith(ext) or (imp.get("from") or "").startswith(ext) for imp in actual_imports):
                logging.warning(f"{file_path}: Missing external library {ext} in imports.")

        for prov in file_details.get("provides", []):
            if prov not in defined:
                logging.warning(f"{file_path}: Missing definition for {prov} (may be dynamic or nested).")

        for use in file_details.get("uses", []):
            if '.' in use:
                if use not in actual_uses and not any(use.startswith(var) for var in variable_mappings.values()):
                    logging.warning(f"{file_path}: Missing attribute use {use} (check indirect usage).")
            else:
                if use not in actual_uses and use not in variable_mappings:
                    logging.warning(f"{file_path}: Missing use of {use} (check variable assignments).")

    elif ext == 'js':
        parsed_data = parse_js_file(file_path)
        actual_imports = parsed_data.get("imports", [])
        actual_provides = parsed_data.get("provides", [])

        for exp_imp in file_details.get("imports", []):
            if isinstance(exp_imp, dict):
                imp_key = exp_imp.get("import")
                imp_from = exp_imp.get("from", "")
                imp_as = exp_imp.get("as") or imp_key
                found = any(
                    imp.get("import") == imp_key or
                    (imp.get("from") or "").startswith(imp_from) or
                    imp.get("as") == imp_as
                    for imp in actual_imports
                )
                if not found:
                    logging.warning(f"{file_path}: Potentially missing import {exp_imp} (check aliases or usage).")

        for ext in file_details.get("external", []):
            if not any(imp.get("import", "").startswith(ext) or (imp.get("from") or "").startswith(ext) for imp in actual_imports):
                logging.warning(f"{file_path}: Missing external library {ext} in imports.")

        for prov in file_details.get("provides", []):
            if prov not in actual_provides:
                logging.warning(f"{file_path}: Missing definition for {prov} (may be dynamic or nested).")
"""
write_file(os.path.join(PROJECT_DIR, "src", "dependency_analyzer", "validators.py"), validators_content)

print("Project structure generated successfully!")
print("Next steps:")
print("1. cd dependency_analyzer")
print("2. pip install -r requirements.txt")
print("3. Download Node.js and extract to dependency_analyzer/nodejs, then run 'nodejs/npm install @babel/parser'")
print("4. pyinstaller --add-data 'src/dependency_analyzer/scripts;dependency_analyzer/scripts' --add-data 'nodejs;nodejs' --onefile src/dependency_analyzer/cli.py -n dependency-analyzer")
print("5. Run: dist/dependency-analyzer <project_root> --verbose")