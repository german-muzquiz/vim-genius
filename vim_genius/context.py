"""
Context injection functionality for vim-genius.
"""

import os
import re
from typing import Dict

from crawl4ai import AsyncWebCrawler, BrowserConfig


async def load_url_content(url: str) -> str:
    """
    Load content from a URL using AsyncWebCrawler.

    Args:
        url: The URL to load

    Returns:
        The content of the URL in markdown format
    """
    browser_config = BrowserConfig(verbose=False)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        print(f"Loading URL: {url}")
        result = await crawler.arun(url)
        return result.markdown


def load_file_content(file: str) -> str:
    """
    Load content from a file.

    Args:
        file: The file path to load

    Returns:
        The content of the file
    """
    file_path = file.strip()

    if not os.path.isabs(file_path):
        file_path = os.path.join("/context", file_path)

    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            content = f"Error reading file {file_path}: {str(e)}"
    else:
        content = f"File not found: {file_path}"

    return content


async def inject_entry(entry: str) -> Dict[str, str]:
    """
    Inject content from a file, folder, or URL.

    Args:
        entry: The entry to inject (file path, folder path, or URL)

    Returns:
        A dictionary mapping file paths to content
    """
    result: Dict[str, str] = {}
    entry = entry.strip()

    # Url loading
    if entry.startswith("http"):
        content = await load_url_content(entry)
        result[entry] = content
        return result

    # File loading
    if not os.path.isabs(entry):
        entry = os.path.join("/workspace", entry)
    if os.path.isdir(entry):
        # For reproducible order, sort the file list.
        for dir_entry in sorted(os.listdir(entry)):
            result.update(await inject_entry(os.path.join(entry, dir_entry)))
    elif os.path.isfile(entry):
        content = load_file_content(entry)
        result[entry] = content
    else:
        result[entry] = "Could not find file or folder"
    return result


async def inject_context(user_input: str) -> str:
    """
    Inject context into the user input.

    Args:
        user_input: The user input to inject context into

    Returns:
        The user input with context injected
    """
    # This regex finds tokens such as "@filename" or "@folder/"
    tokens = re.findall(r"@(\S+)", user_input)
    file_injection_chunks: list[str] = []
    url_injection_chunks: list[str] = []
    for token in tokens:
        context = await inject_entry(token)
        for file_path, content in context.items():
            if file_path.startswith("http"):
                url_injection_chunks.append(f"  <web_resource url={file_path}>\n{content}\n  </web_resource>")
            else:
                if file_path.startswith("/workspace/"):
                    file_path = file_path[len("/workspace/") :]  # noqa: PLW2901
                file_injection_chunks.append(f"  <project_file filename={file_path}>\n{content}\n  </project_file>")

    # Remove all @tokens from the original user prompt.
    adjusted_prompt = re.sub(r"@\S+", "", user_input)

    if file_injection_chunks:
        adjusted_prompt += "<project_files>"
        adjusted_prompt += "\n" + "\n".join(file_injection_chunks)
        adjusted_prompt += "\n</project_files>"
    if url_injection_chunks:
        adjusted_prompt += "<web_resources>"
        adjusted_prompt += "\n" + "\n".join(url_injection_chunks)
        adjusted_prompt += "\n</web_resources>"

    return adjusted_prompt
