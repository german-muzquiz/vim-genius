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


def process_code_blocks(code_blocks: list[dict]) -> None:
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
        temp_file_path = f"/root/.genius/staging/{filename}"
        repo_file_path = f"/workspace/{filename}"

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
                    result = subprocess.run(
                        ["patch", temp_file_path, patch_file], check=True, capture_output=True, text=True
                    )

                except subprocess.CalledProcessError as e:
                    print(f"Error applying patch to {filename}: {e.stderr}")

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
