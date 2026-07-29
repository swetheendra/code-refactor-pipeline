from fastmcp import FastMCP
import subprocess
import os
from pathlib import Path

mcp = FastMCP("my-server")

SERVER_DIR = Path(__file__).parent.resolve()
WORKSPACE_ROOT = (
    SERVER_DIR / "workspace" if (SERVER_DIR / "workspace").exists() else SERVER_DIR
)

@mcp.tool()
def run_linter(file_path:str) -> dict:
    """
    Run a linter on the specified file and return the results.
    Returns status boolean and list of error strings.
    """

    clean_path = Path(file_path)
    file_path = str(clean_path)

    if not os.path.exists(file_path):
        return {"success": False, "errors": [f"File not found: {file_path}"]}
    
    result = subprocess.run(["flake8", file_path], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    return {"success": result.returncode == 0, "errors": result.stdout.splitlines() if result.stdout else []}


@mcp.tool()
def run_type_checker(file_path:str) -> dict:
    """
    Run a type checker on the specified file and return the results.
    Returns status boolean and list of error strings.
    """

    clean_path = Path(file_path)
    file_path = str(clean_path)

    if not os.path.exists(file_path):
        return {"success": False, "errors": [f"File not found: {file_path}"]}
    
    result = subprocess.run(["mypy", "--ignore-missing-imports", file_path], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    return {"success": result.returncode == 0, "errors": result.stdout.splitlines() if result.stdout else []}


@mcp.tool()
def run_security_scanner(file_path:str) -> dict:
    """
    Run a security scanner on the specified file and return the results.
    Returns status boolean and list of error strings.
    """

    clean_path = Path(file_path)
    file_path = str(clean_path)

    if not os.path.exists(file_path):
        return {"success": False, "errors": [f"File not found: {file_path}"]}
    
    res = subprocess.run(
            ["bandit", "-r", file_path, "-f", "custom", "--msg-template", "{line}:{test_id}:{severity}:{msg}"],
            capture_output=True,
            text=True,
            timeout=20
        )
    issues = [line for line in res.stdout.splitlines() if line and ":" in line]
    return {"success": len(issues) == 0, "errors": issues}

@mcp.tool()
def run_tests(test_file: str) -> dict:
    """Run tests on the specified test file and return the results."""
    given_path = Path(test_file)

    # 1. Extract just the filename to avoid stale absolute path hallucinations (e.g., C:\Users\swt...)
    filename = given_path.name

    # 2. Search for the file inside your active workspace root
    matches = list(WORKSPACE_ROOT.rglob(filename))

    if not matches:
        # Fallback: Check if the raw string actually exists as passed
        if given_path.exists():
            target_path = given_path.resolve()
        else:
            # Helpful error showing what files ACTUALLY exist in workspace
            existing_files = [
                f.relative_to(WORKSPACE_ROOT).as_posix()
                for f in WORKSPACE_ROOT.rglob("*.py")
            ]
            return {
                "success": False,
                "errors": [
                    f"Could not find '{filename}' in workspace: {WORKSPACE_ROOT.as_posix()}",
                    f"Available Python files in workspace: {existing_files}",
                ],
            }
    else:
        # Pick the best match found on disk
        target_path = matches[0]

    # 3. Execute pytest
    result = subprocess.run(
        ["pytest", target_path.as_posix(), "-v"],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        cwd=WORKSPACE_ROOT,
    )

    output = result.stdout if result.stdout else result.stderr
    return {"success": result.returncode == 0, "errors": output}

@mcp.tool()
def apply_code_patch(file_path:str, new_code:str) -> dict:
    """
    Apply a updated patch to the specified file.
    Returns status boolean and list of error strings.
    """

    clean_path = Path(file_path)
    file_path = str(clean_path)

    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)

    try:
        with open(file_path, 'w') as f:
            f.write(new_code)

        return {"success": True, "errors": []}
    except Exception as e:
        return {"success": False, "errors": [str(e)]}

@mcp.tool
def get_git_diff(file_path:str) -> dict:
    """
    Get the git diff for the specified file.
    Returns status boolean and list of error strings.
    """

    clean_path = Path(file_path)
    file_path = str(clean_path)

    if not os.path.exists(file_path):
        return {"success": False, "errors": [f"File not found: {file_path}"]}

    result = subprocess.run(["git", "diff", file_path], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    diff = result.stdout.strip()
    return {"has_changes": len(diff) > 0, "diff": diff if diff else "No changes detected."}

@mcp.tool
def revert_changes(file_path:str) -> dict:
    """
    Revert changes to the specified file using git.
    Returns status boolean and list of error strings.
    """

    clean_path = Path(file_path)
    file_path = str(clean_path)

    if not os.path.exists(file_path):
        return {"success": False, "errors": [f"File not found: {file_path}"]}

    result = subprocess.run(["git", "checkout", "--", file_path], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    return {"success": result.returncode == 0, "errors": result.stderr.splitlines() if result.stderr else []}

if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=8000)