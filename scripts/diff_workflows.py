#!/usr/bin/env python3
"""
Compare two ComfyUI workflow JSON files and show differences.
"""
import json
import sys
import argparse
import re
from pathlib import Path
from difflib import unified_diff


def load_catalog(catalog_path: Path = None) -> list[dict]:
    """Load workflow catalog and return list of entries."""
    if catalog_path is None:
        catalog_path = Path("outputs/workflows/README.md")
    
    if not catalog_path.exists():
        return []
    
    entries = []
    content = catalog_path.read_text()
    
    for line in content.split('\n'):
        if line.startswith('|') and '---' not in line and 'Workflow' not in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 5:  # | filename | hash | description | date |
                entries.append({
                    'filename': parts[1],
                    'hash': parts[2],
                    'description': parts[3],
                    'date': parts[4]
                })
    
    return entries


def resolve_workflow_path(reference: str, catalog_path: Path = None) -> Path:
    """
    Resolve a workflow reference to a file path.
    
    Can resolve by:
    - Direct file path
    - Hash (8-character hex)
    - Description regex pattern
    
    Args:
        reference: File path, hash, or description pattern
        catalog_path: Path to catalog file (default: outputs/workflows/README.md)
    
    Returns:
        Path to the workflow file
    
    Raises:
        FileNotFoundError: If workflow cannot be found
        ValueError: If multiple matches found
    """
    # First, check if it's a direct file path
    path = Path(reference)
    if path.exists():
        return path
    
    # Load catalog
    catalog = load_catalog(catalog_path)
    if not catalog:
        raise FileNotFoundError(f"No catalog found and file doesn't exist: {reference}")
    
    # Try to match by hash (exact match)
    if re.match(r'^[0-9a-f]{8}$', reference):
        matches = [e for e in catalog if e['hash'] == reference]
        if len(matches) == 1:
            return Path("outputs/workflows") / matches[0]['filename']
        elif len(matches) > 1:
            filenames = [m['filename'] for m in matches]
            raise ValueError(f"Multiple workflows found with hash {reference}: {filenames}")
        # If no match by hash, continue to try as description pattern
    
    # Try to match by description (regex)
    try:
        pattern = re.compile(reference, re.IGNORECASE)
        matches = [e for e in catalog if pattern.search(e['description'])]
        
        if len(matches) == 1:
            return Path("outputs/workflows") / matches[0]['filename']
        elif len(matches) > 1:
            print(f"Multiple workflows match pattern '{reference}':", file=sys.stderr)
            for m in matches:
                print(f"  {m['hash']}: {m['filename']} - {m['description']}", file=sys.stderr)
            raise ValueError(f"Multiple matches found. Please be more specific.")
        elif not matches:
            raise FileNotFoundError(f"No workflow found matching: {reference}")
    except re.error as e:
        raise ValueError(f"Invalid regex pattern '{reference}': {e}")


def load_workflow(path: Path) -> dict:
    """Load and parse a workflow JSON file."""
    with open(path, 'r') as f:
        return json.load(f)


def pretty_json(data: dict) -> list[str]:
    """Convert dict to pretty-printed JSON lines."""
    json_str = json.dumps(data, indent=2, sort_keys=True)
    return json_str.splitlines(keepends=True)


def diff_workflows(file1: Path, file2: Path, context_lines: int = 3) -> None:
    """
    Compare two workflow files and print unified diff.
    
    Args:
        file1: Path to first workflow file
        file2: Path to second workflow file
        context_lines: Number of context lines to show around changes
    """
    # Load workflows
    try:
        workflow1 = load_workflow(file1)
        workflow2 = load_workflow(file2)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Convert to pretty-printed JSON for comparison
    lines1 = pretty_json(workflow1)
    lines2 = pretty_json(workflow2)
    
    # Generate unified diff
    diff = unified_diff(
        lines1,
        lines2,
        fromfile=str(file1),
        tofile=str(file2),
        n=context_lines
    )
    
    # Print diff with color if terminal supports it
    has_changes = False
    for line in diff:
        has_changes = True
        line = line.rstrip('\n')
        
        # Color output for terminals
        if sys.stdout.isatty():
            if line.startswith('+++') or line.startswith('---'):
                print(f"\033[1m{line}\033[0m")  # Bold
            elif line.startswith('+'):
                print(f"\033[32m{line}\033[0m")  # Green
            elif line.startswith('-'):
                print(f"\033[31m{line}\033[0m")  # Red
            elif line.startswith('@@'):
                print(f"\033[36m{line}\033[0m")  # Cyan
            else:
                print(line)
        else:
            print(line)
    
    if not has_changes:
        print("No differences found between workflows.")


def main():
    parser = argparse.ArgumentParser(
        description="Compare two ComfyUI workflow JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare by file path
  %(prog)s outputs/workflows/workflow_abc123.json outputs/workflows/workflow_def456.json
  
  # Compare by hash (8-character hex)
  %(prog)s 47e91030 7c833bc9
  
  # Compare by description pattern (regex)
  %(prog)s "Original" "duration.*8"
  %(prog)s "Original WAN" "Modified.*8"
  
  # Mix references
  %(prog)s 47e91030 "duration set to 8"
  
  # Show more context (default is 3 lines)
  %(prog)s -c 5 47e91030 7c833bc9
        """
    )
    
    parser.add_argument(
        "ref1",
        help="First workflow (file path, hash, or description pattern)"
    )
    
    parser.add_argument(
        "ref2",
        help="Second workflow (file path, hash, or description pattern)"
    )
    
    parser.add_argument(
        "-c", "--context",
        type=int,
        default=3,
        help="Number of context lines to show (default: 3)"
    )
    
    parser.add_argument(
        "--catalog",
        type=Path,
        default=None,
        help="Path to catalog file (default: outputs/workflows/README.md)"
    )
    
    args = parser.parse_args()
    
    # Resolve workflow references
    try:
        file1 = resolve_workflow_path(args.ref1, args.catalog)
        file2 = resolve_workflow_path(args.ref2, args.catalog)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Verify files exist
    if not file1.exists():
        print(f"Error: File not found: {file1}", file=sys.stderr)
        sys.exit(1)
    
    if not file2.exists():
        print(f"Error: File not found: {file2}", file=sys.stderr)
        sys.exit(1)
    
    # Compare workflows
    diff_workflows(file1, file2, args.context)


if __name__ == "__main__":
    main()
