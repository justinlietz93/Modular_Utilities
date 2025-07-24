import os
import json
import argparse
import re
import uuid
from pathlib import Path

def get_comment_syntax(file_path):
    """Determine the appropriate comment block syntax based on file extension."""
    ext = file_path.lower().split('.')[-1]
    comment_syntax = {
        'py': ('"""', '"""'),
        'js': ('/**', '*/'),
        'html': ('<!--', '-->'),
    }
    result = comment_syntax.get(ext, (None, None))
    print(f"File {file_path}: Extension '{ext}' -> Comment syntax: {result}")
    return result

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
    if file_details.get("imports"):
        output.append("Imports:")
        for imp in file_details["imports"]:
            if "from" in imp:
                output.append(f"  - from {imp['from']} import {imp['import']} as {imp['as'] or imp['import']}")
            else:
                output.append(f"  - import {imp['import']} as {imp['as'] or imp['import']}")
    if file_details.get("uses"):
        output.append("Uses:")
        for use in file_details["uses"]:
            output.append(f"  - {use}")
    if file_details.get("external"):
        output.append("External Dependencies:")
        for ext in file_details["external"]:
            output.append(f"  - {ext}")
    return "\n".join(output) if output else "No dependencies found."

def remove_duplicate_headers(full_content, file_key, start_comment, end_comment):
    """Remove all existing header blocks with the given file key, keeping only the last one."""
    start_pattern = f"{re.escape(start_comment)}\\s*#{re.escape(file_key)}_start"
    end_pattern = f"#{re.escape(file_key)}_end\\s*{re.escape(end_comment)}"
    
    # Find all header blocks
    start_matches = list(re.finditer(start_pattern, full_content, re.MULTILINE))
    end_matches = list(re.finditer(end_pattern, full_content, re.MULTILINE))

    if len(start_matches) != len(end_matches):
        print(f"Warning: Mismatched header markers in content (start: {len(start_matches)}, end: {len(end_matches)}). Cleaning up.")
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
        print(f"Skipping {rel_path}: Unsupported file type for header.")
        return

    # Get or generate the unique file key
    file_key = header_keys.get(rel_path)
    if not file_key:
        file_key = generate_file_key()
        header_keys[rel_path] = file_key
        print(f"Assigned new key {file_key} to {rel_path}")
    else:
        print(f"Reusing existing key {file_key} for {rel_path}")

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
        print(f"Error reading {file_path}: {e}")
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
        print(f"Updated header in {rel_path}")
    except Exception as e:
        print(f"Error writing to {file_path}: {e}")

def find_dependency_map(project_root):
    """Search the project root and subdirectories for dependency_map.json."""
    for dirpath, dirnames, filenames in os.walk(project_root):
        if 'dependency_map.json' in [f.lower() for f in filenames]:
            return os.path.join(dirpath, 'dependency_map.json')
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
            print(f"Error: Could not find dependency_map.json in {project_root} or its subdirectories.")
            return
        print(f"Found dependency map at: {dependency_map_path}")
    else:
        dependency_map_path = os.path.abspath(dependency_map_path)

    # Load the dependency map
    try:
        with open(dependency_map_path, 'r', encoding='utf-8') as f:
            dependency_map = json.load(f)
    except Exception as e:
        print(f"Error loading dependency map {dependency_map_path}: {e}")
        return

    # Load or create header keys
    header_keys = load_or_create_header_keys(project_root)

    # Track processed files to avoid duplicates
    processed_files = set()
    dependency_map_files = set()

    # Process all files from the dependency map dynamically
    for section in ['backend', 'tests', 'frontend']:  # Iterate over known sections
        if section in dependency_map:
            if section == 'backend' and 'modules' in dependency_map[section]:
                for module, module_details in dependency_map[section]['modules'].items():
                    for filename, file_details in module_details.get('files', {}).items():
                        rel_path = f"{section}/{module}/{filename}" if module else f"{section}/{filename}"
                        file_path = os.path.join(project_root, rel_path.replace('/', os.sep))
                        if rel_path in processed_files:
                            print(f"Skipping duplicate entry for {rel_path} in dependency map.")
                            continue
                        processed_files.add(rel_path)
                        dependency_map_files.add(rel_path)
                        if os.path.exists(file_path):
                            print(f"Processing {section} file: {rel_path}")
                            add_or_update_header(file_path, rel_path, file_details, header_keys)
                        else:
                            print(f"File not found on disk: {file_path}")
            elif section == 'frontend' and 'files' in dependency_map[section]:
                for rel_path, file_details in dependency_map[section]['files'].items():
                    file_path = os.path.join(project_root, rel_path.replace('/', os.sep))
                    rel_path = rel_path.replace(os.sep, '/')
                    if rel_path in processed_files:
                        print(f"Skipping duplicate entry for {rel_path} in dependency map.")
                        continue
                    processed_files.add(rel_path)
                    dependency_map_files.add(rel_path)
                    if os.path.exists(file_path):
                        print(f"Processing {section} file: {rel_path}")
                        add_or_update_header(file_path, rel_path, file_details, header_keys)
                    else:
                        print(f"File not found on disk: {file_path}")

    # Compare dependency map files with actual files in the project root
    all_files = list_files_in_directory(project_root)
    missing_in_dependency_map = set(all_files) - dependency_map_files
    if missing_in_dependency_map:
        print("\nWarning: The following files are present in the filesystem but missing in dependency_map.json:")
        for file in sorted(missing_in_dependency_map):
            print(f"  - {file}")

    # Save updated header keys
    save_header_keys(project_root, header_keys)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add or update comment block headers to files listing their path and dependencies.")
    parser.add_argument("project_root", help="Path to the project root directory")
    parser.add_argument("dependency_map_path", nargs='?', help="Path to the dependency map JSON file (optional; will search if not provided)")

    args = parser.parse_args()

    # Resolve paths
    project_root = os.path.abspath(args.project_root)
    dependency_map_path = args.dependency_map_path

    if not os.path.exists(project_root):
        print(f"Error: Project root directory {project_root} does not exist.")
        sys.exit(1)

    process_files(project_root, dependency_map_path)