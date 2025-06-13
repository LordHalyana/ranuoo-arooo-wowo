import os
import fnmatch
import toml
import json

def check_folder_integrity(base_path=None, fix=False, output_json=False) -> list[str]:
    # Always check the integrity of the 'workspace' folder in the project root unless overridden
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if base_path is None:
        workspace_path = os.path.join(project_root, "workspace")
    else:
        workspace_path = base_path
    try:
        config = toml.load(os.path.join(project_root, "config.project.toml"))
    except FileNotFoundError:
        return [f"[ERROR] config.project.toml not found in {project_root}."]

    integrity = config.get("integrity", {})
    require_dirs = integrity.get("require_dirs", [])
    require_files = integrity.get("require_files", [])
    forbid_patterns = integrity.get("forbid_files", [])
    enforce_flat = integrity.get("enforce_flat_src", False)
    ignore_dirs = integrity.get("ignore_dirs", [])

    problems = []

    # Detect all top-level folders in workspace/ (microservices)
    try:
        microservices = [d for d in os.listdir(workspace_path) if os.path.isdir(os.path.join(workspace_path, d))]
    except FileNotFoundError:
        return [f"[ERROR] workspace folder not found at {workspace_path}."]

    for ms in microservices:
        ms_path = os.path.join(workspace_path, ms)
        # Check required subdirectories
        for d in require_dirs:
            subdir_path = os.path.join(ms_path, d)
            if not os.path.isdir(subdir_path):
                problems.append(f"[MISSING] {ms}/ Required subdirectory: {d}")
                if fix:
                    try:
                        os.makedirs(subdir_path, exist_ok=True)
                    except Exception as e:
                        problems.append(f"[ERROR] Could not create directory {ms}/{d}: {e}")
        # Check required files
        for f in require_files:
            file_path = os.path.join(ms_path, f)
            if not os.path.isfile(file_path):
                problems.append(f"[MISSING] {ms}/ Required file: {f}")
        # Check forbidden files
        for root, dirs, files in os.walk(ms_path):
            # Remove ignored dirs from traversal
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            if any(os.path.basename(root) == ignored for ignored in ignore_dirs):
                continue
            for file in files:
                for pattern in forbid_patterns:
                    if fnmatch.fnmatch(file.lower(), pattern.lower()):
                        rel_path = os.path.relpath(os.path.join(root, file), project_root)
                        problems.append(f"[FORBIDDEN] {ms}/ Matches '{pattern}': {rel_path}")
        # Optionally check for flat src/ in each microservice
        if enforce_flat:
            src_path = os.path.join(ms_path, "src")
            if os.path.isdir(src_path):
                for item in os.listdir(src_path):
                    subpath = os.path.join(src_path, item)
                    if os.path.isdir(subpath):
                        problems.append(f"[STRUCTURE] {ms}/src/ must be flat — subdirectory found: {item}")

    if output_json:
        print(json.dumps({"problems": problems}, indent=2, ensure_ascii=False))
    return problems
