"""
Tool that edits a file in the workspace.
"""

import os
import shutil
import subprocess

from pydantic_ai import ModelRetry, RunContext

from genius_assistant.schemas import Deps


def edit_file(ctx: RunContext[Deps], filename: str, patch: str) -> bool:
    """
    Edits the contents of a file.

    Args:
        ctx: The context object containing the dependencies.
        filename: The name of the file to edit relative to the workspace root.
        patch: The patch to apply to the file.
                Format Requirements:

                1. Header (REQUIRED):
                  <header_format>
                    --- path/to/file
                    +++ path/to/file.updated
                  </header_format>
                  - Must include both lines
                  - Use full paths relative to the project root

                2. Hunks:
                  <hunk_format>
                    @@ -lineStart,lineCount +lineStart,lineCount @@
                    -removed line
                    +added line
                  </hunk_format>
                  - Each hunk starts with @@ showing line numbers for changes
                  - Format: @@ -originalStart,originalCount +newStart,newCount @@
                  - Use - for removed/changed lines
                  - Use + for new/modified lines
                  - Indentation must match exactly

                  Common Pitfalls:
                    1. Missing or incorrect header lines
                    2. Incorrect line numbers in @@ lines
                    3. Wrong indentation in changed lines
                    4. Incomplete context (missing lines that need changing)
                    5. Not marking all modified lines with - and +

                    Best Practices:
                    1. Replace entire code paragraphs:
                        - Remove complete old version with - lines
                        - Add complete new version with + lines
                        - Include correct line numbers
                    2. Moving code requires two hunks:
                        - First hunk: Remove from old location
                        - Second hunk: Add to new location
                    3. One hunk per logical change
                    4. Verify line numbers match the line numbers you have in the file

    Returns:
        True if the file was edited successfully, False otherwise.
    """
    print(f"=> Editing file: {filename}")

    if os.path.isabs(filename) and not filename.startswith(ctx.deps.workspace_home):
        raise ModelRetry(f"File {filename} is not in the workspace")
    if not os.path.exists(os.path.join(ctx.deps.workspace_home, filename)) or not os.path.isfile(
        os.path.join(ctx.deps.workspace_home, filename)
    ):
        raise ModelRetry(f"File {filename} does not exist or is not a file")

    filename = os.path.join(ctx.deps.workspace_home, filename)

    # Backup original file to ~/.genius/backup preserving structure, skip if already backed up
    backup_root = os.path.expanduser("~/.genius/backup")
    abs_file = filename
    # Compute relative path to workspace
    rel_path = os.path.relpath(abs_file, ctx.deps.workspace_home)
    backup_path = os.path.join(backup_root, rel_path)
    if not os.path.exists(backup_path):
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(abs_file, backup_path)

    # Write the patch to a file with .patch extension
    patch_file = f"{filename}.patch"
    with open(patch_file, "w", encoding="utf-8") as f:
        f.write(patch)

    # Apply the patch to the file
    try:
        subprocess.run(
            ["patch", "--no-backup-if-mismatch", "-r", "-", filename, patch_file],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        # Try the alternative patching method
        patched_content = apply_patch_manually(filename, patch)
        open(filename, "w", encoding="utf-8").write(patched_content)

    # Delete temporary files ignoring if it exists or not
    for to_delete in [f"{filename}.rej", f"{filename}.patch"]:
        try:
            os.remove(to_delete)
        except FileNotFoundError:
            pass

    # Compare new content with backup
    with open(abs_file, "r", encoding="utf-8") as f:
        new_content = f.read()
    # Load original content from backup
    with open(backup_path, "r", encoding="utf-8") as f:
        original_content = f.read()

    if new_content == original_content:
        print(f"File {filename} was not changed")
        return False

    ctx.deps.modified_files.append(filename)
    return True


def apply_patch_manually(original_file_path: str, patch_content: str) -> str:
    """
    Apply a patch manually using find-and-replace when the patch command fails.

    Args:
        original_file_path: Path to the original file
        patch_content: Content of the patch file

    Returns:
        The content of the patched file
    """
    # Read the original file content
    with open(original_file_path, "r", encoding="utf-8") as f:
        original_content = f.read()

    # Split the patch into hunks
    # Skip the header lines (first two lines)
    lines = patch_content.strip().split("\n")
    if len(lines) < 2 or not lines[0].startswith("---") or not lines[1].startswith("+++"):
        print(f"Invalid patch format for {original_file_path}")
        return original_content

    # Skip the header
    lines = lines[2:]

    # Process each hunk
    result_content = original_content
    current_hunk: list[str] = []
    in_hunk = False

    for line in lines:
        if line.startswith("@@"):
            # Process previous hunk if exists
            if in_hunk and current_hunk:
                result_content = apply_hunk(result_content, current_hunk)
                current_hunk = []

            in_hunk = True
            current_hunk.append(line)
        elif in_hunk:
            current_hunk.append(line)

    # Process the last hunk
    if in_hunk and current_hunk:
        result_content = apply_hunk(result_content, current_hunk)

    return result_content


def apply_hunk(content: str, hunk_lines: list[str]) -> str:
    """Apply a single hunk to the content using find and replace."""
    original_block: list[str] = []
    new_block: list[str] = []
    for line in hunk_lines:
        if line and line.startswith("@@"):
            continue
        elif line.startswith("-"):
            original_block.append(line[1:])
        elif line.startswith("+"):
            new_block.append(line[1:])
        else:
            original_block.append(line[1:])
            new_block.append(line[1:])

    # Find the original content and replace with the new content
    return content.replace("\n".join(original_block), "\n".join(new_block))
