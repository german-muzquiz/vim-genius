"""
Code block extraction and processing functionality.
"""

import os
import re
import shutil
import subprocess


def extract_code_blocks(response: str) -> list[dict]:
    """
    Extract code blocks from the LLM response.

    Args:
        response: The LLM response text

    Returns:
        A list of dictionaries containing code block information
    """
    # Regex to match code blocks with their attributes
    pattern = (
        r'<code_block\s+filename="([^"]+)"\s+filetype="([^"]+)"\s+operation="([^"]+)"(?:\s+[^>]*)?>(.*?)</code_block>'
    )
    matches = re.finditer(pattern, response, re.DOTALL)

    code_blocks = []
    for match in matches:
        filename = match.group(1)
        filetype = match.group(2)
        operation = match.group(3)
        content = match.group(4)

        code_blocks.append({"filename": filename, "filetype": filetype, "operation": operation, "content": content})

    return code_blocks


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


def process_code_blocks(code_blocks: list[dict], workspace_home: str) -> None:
    """
    Process extracted code blocks and write them to files.

    Args:
        code_blocks: List of code block dictionaries
    """
    for block in code_blocks:
        filename = block["filename"]
        operation = block["operation"]
        content = block["content"]

        # Create full paths
        temp_file_path = os.path.join(os.path.expanduser("~"), ".genius", "staging", filename)
        repo_file_path = os.path.join(workspace_home, filename)

        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)

        if operation == "add":
            # For new files, write the content directly
            with open(temp_file_path, "w", encoding="utf-8") as f:
                f.write(content)

        elif operation == "update":
            # For updates, write the patch to a file with .patch extension
            patch_file = f"{temp_file_path}.patch"
            with open(patch_file, "w", encoding="utf-8") as f:
                f.write(content)

            # Copy the original file to temp dir if it exists
            if os.path.exists(repo_file_path):
                shutil.copy2(repo_file_path, temp_file_path)

                # Apply the patch to the file
                try:
                    subprocess.run(["patch", temp_file_path, patch_file], check=True, capture_output=True, text=True)

                except subprocess.CalledProcessError as e:
                    print(f"Error applying patch to {filename}: {e.stderr}")
                    print(f"Attempting alternative patching method for {filename}...")

                    # Try the alternative patching method
                    with open(patch_file, "r", encoding="utf-8") as f:
                        patch_content = f.read()
                    patched_content = apply_patch_manually(repo_file_path, patch_content)
                    open(temp_file_path, "w", encoding="utf-8").write(patched_content)

                # Delete temporary files ignoring if it exists or not
                for to_delete in [f"{temp_file_path}.orig", f"{temp_file_path}.patch"]:
                    try:
                        os.remove(to_delete)
                    except FileNotFoundError:
                        pass

        elif operation == "delete":
            # For deletions, create a marker file with .delete extension
            with open(f"{temp_file_path}.delete", "w", encoding="utf-8") as f:
                f.write("")
