import os
import fnmatch
import json # Using JSON for the temporary file for simplicity and readability

def get_loc(file_path):
    """Calculates the lines of code (LOC) for a given file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0

def is_ignored(path, root_dir, ignore_patterns):
    """Checks if a given path matches any of the ignore patterns."""
    relative_path = os.path.relpath(path, root_dir)
    normalized_path = relative_path.replace(os.sep, '/')

    for pattern in ignore_patterns:
        if pattern.endswith('/'):
            if (normalized_path + '/').startswith(pattern):
                return True
        elif fnmatch.fnmatch(normalized_path, pattern):
            return True
    return False

def analyze_directory(root_dir, ignore_patterns):
    """
    Performs a single, comprehensive analysis of a directory and returns a
    data object containing all necessary information for subsequent steps.
    """
    report = {
        'files_metadata': {}, # Using a dict with path as key for easier lookup
        'ascii_map_lines': [],
        'path_to_line_num': {},
        'global_stats': {'total_files': 0, 'total_size': 0, 'total_loc': 0}
    }
    
    all_paths = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
        # Efficiently prune ignored directories from traversal
        original_dirnames = list(dirnames)
        dirnames[:] = [d for d in original_dirnames if not is_ignored(os.path.join(dirpath, d), root_dir, ignore_patterns)]
        
        depth = os.path.relpath(dirpath, root_dir).count(os.sep) if dirpath != root_dir else 0
        
        # Add current directory and its files to the list
        all_paths.append({'path': dirpath, 'type': 'dir', 'depth': depth})
        for filename in filenames:
            all_paths.append({'path': os.path.join(dirpath, filename), 'type': 'file', 'depth': depth + 1})
            
        # Add the pruned (ignored) directories to the list for the map
        for ignored_dir in set(original_dirnames) - set(dirnames):
            all_paths.append({'path': os.path.join(dirpath, ignored_dir), 'type': 'ignored_dir', 'depth': depth + 1})

    # Sort all paths alphabetically for a consistent and readable ASCII map
    all_paths.sort(key=lambda x: x['path'])

    # Build the final report object from the sorted list
    for line_num, item in enumerate(all_paths):
        full_path = item['path']
        depth = item['depth']
        name = os.path.basename(full_path)
        indent = '    ' * (depth - 1) if depth > 0 else ''
        connector = '└── ' if depth > 0 else ''

        if item['type'] == 'dir':
            map_line = f"{indent}{connector}{name}/"
            report['ascii_map_lines'].append(map_line)
            report['path_to_line_num'][full_path] = line_num

        elif item['type'] == 'ignored_dir':
            map_line = f"{indent}{connector}{name}/ (IGNORED)"
            report['ascii_map_lines'].append(map_line)
            report['path_to_line_num'][full_path] = line_num
        
        elif item['type'] == 'file':
            # Check if file is ignored by a specific pattern (e.g., *.tmp)
            if is_ignored(full_path, root_dir, ignore_patterns):
                 map_line = f"{indent}{connector}{name} (IGNORED)"
                 report['ascii_map_lines'].append(map_line)
                 report['path_to_line_num'][full_path] = line_num
            else:
                map_line = f"{indent}{connector}{name}"
                report['ascii_map_lines'].append(map_line)
                report['path_to_line_num'][full_path] = line_num
                try:
                    size = os.path.getsize(full_path)
                    loc = get_loc(full_path)
                    
                    # Store metadata and update global stats
                    report['files_metadata'][full_path] = {'size': size, 'loc': loc}
                    report['global_stats']['total_files'] += 1
                    report['global_stats']['total_size'] += size
                    report['global_stats']['total_loc'] += loc
                except OSError:
                    # File might be a broken symlink or inaccessible
                    report['files_metadata'][full_path] = {'size': 0, 'loc': 0, 'error': 'access denied'}


    return report

def save_analysis(report, output_path):
    """Saves the analysis report to a JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4)

def load_analysis(input_path):
    """Loads an analysis report from a JSON file."""
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)