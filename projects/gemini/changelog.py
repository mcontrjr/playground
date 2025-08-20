import subprocess
import os
import io
from google import genai
from dotenv import load_dotenv
from markdown_formatter import MarkdownFormatter

load_dotenv()

# --- Configuration ---
MAX_PROMPT_CHARS = 8000  # Max characters for the AI input prompt
IGNORE_EXTENSIONS = ['.csv', '.json', '.log', '.lock', '.md', '.txt', '.yaml', '.yml', '.toml', '.xml', '.svg', '.env', '.gitignore', '.pyc'] # Add more as needed
GIT_DIFF_RANGE = "HEAD~3..HEAD" # e.g., "main develop", "HEAD~1..HEAD", "v1.0..v1.1"

# --- Git Interaction & Parsing ---
def get_git_changes(repo_path="."):
    """
    Executes git diff, parses output, and reads content of changed files.
    Returns a list of dictionaries with file details.
    """
    os.chdir(repo_path)

    try:
        # Get diff summary for file paths and change types
        diff_summary_result = subprocess.run(
            ['git', 'diff', '--name-status', GIT_DIFF_RANGE],
            capture_output=True, text=True, check=True
        )
        diff_summary_lines = diff_summary_result.stdout.strip().split('\n')

        # Get full diff for context (optional, can be large)
        full_diff_result = subprocess.run(
            ['git', 'diff', GIT_DIFF_RANGE],
            capture_output=True, text=True, check=True
        )
        full_diff_text = full_diff_result.stdout.strip()

    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}")
        return [], ""
    except FileNotFoundError:
        print("Git command not found. Ensure Git is installed and in your PATH.")
        return [], ""

    changed_files_info = []

    # Parse --name-status output
    for line in diff_summary_lines:
        if not line:
            continue
        status, file_path = line.split('\t', 1) # Split only on first tab

        file_content = ""
        # Read current content for modified or added files
        if status in ['A', 'M']: # Added (A) or Modified (M)
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        file_content = f.read()
                else:
                    file_content = f"<File '{file_path}' added/modified but not found locally>"
            except Exception as e:
                file_content = f"<Could not read '{file_path}': {e}>"
        elif status == 'D': # Deleted (D)
            file_content = "<File was deleted>"
        elif status == 'R': # Renamed (Rxx)
            old_path, new_path = file_path.split('\t') # Rxx has two paths
            file_path = new_path # Use new path for content
            try:
                if os.path.exists(new_path):
                    with open(new_path, 'r', encoding='utf-8', errors='ignore') as f:
                        file_content = f.read()
                else:
                    file_content = f"<File '{new_path}' renamed but not found locally>"
            except Exception as e:
                file_content = f"<Could not read '{new_path}': {e}>"
            status = 'R' # Simplify status for output

        changed_files_info.append({
            'status': status,
            'file_path': file_path,
            'content': file_content
        })

    return changed_files_info, full_diff_text

def filter_files(files_info, ignore_exts):
    """Filters files based on their extensions."""
    filtered = []
    for f_info in files_info:
        _, ext = os.path.splitext(f_info['file_path'])
        if ext.lower() not in [e.lower() for e in ignore_exts]:
            filtered.append(f_info)
    return filtered

# --- AI Prompt Preparation ---
def prepare_ai_prompt(changed_files_info, full_diff_text, max_chars):
    """
    Constructs the prompt for the AI, applying character limits.
    """
    prompt_parts = []
    current_chars = 0

    # Initial instruction for the AI
    instruction = (
        "Generate a concise, user-friendly changelog or summary based on the following code changes. "
        "Focus on features, bug fixes, performance improvements, and breaking changes. "
        "Ignore trivial changes. If content is truncated, focus on the available information.\n\n"
        "--- Git Changes ---\n"
    )
    prompt_parts.append(instruction)
    current_chars += len(instruction)

    # Optionally add the full diff first (if small enough)
    if current_chars + len(full_diff_text) < max_chars * 0.2: # Reserve 20% for full diff if it fits
        prompt_parts.append("Full Git Diff (Partial if large):\n")
        truncated_diff = full_diff_text[:max_chars - current_chars - len("Full Git Diff (Partial if large):\n") - 50] # Leave room for other info
        prompt_parts.append(truncated_diff + "\n...\n\n" if len(full_diff_text) > len(truncated_diff) else full_diff_text + "\n\n")
        current_chars += len(prompt_parts[-1])
    else:
        prompt_parts.append("Full Git Diff too large to include fully. Relying on file-by-file changes.\n\n")
        current_chars += len(prompt_parts[-1])


    prompt_parts.append("--- Detailed File Changes ---\n")
    current_chars += len(prompt_parts[-1])

    for f_info in changed_files_info:
        file_header = f"File: {f_info['file_path']} (Status: {f_info['status']})\n"
        current_chars += len(file_header)

        # Calculate remaining budget for this file's content
        remaining_budget = max_chars - current_chars - len("\n...\n") # Extra for potential truncation ellipsis

        file_content_to_add = ""
        if remaining_budget <= 0:
            file_content_to_add = "<Content skipped due to character limit>\n"
        elif len(f_info['content']) > remaining_budget:
            # Truncate content, prioritize beginning (often more relevant)
            file_content_to_add = f_info['content'][:remaining_budget] + "\n...\n"
        else:
            file_content_to_add = f_info['content'] + "\n"

        prompt_parts.append(file_header + file_content_to_add + "\n")
        current_chars += len(file_content_to_add)

        if current_chars >= max_chars:
            print(f"Warning: Prompt hit character limit ({max_chars}). Some changes might be omitted.")
            break # Stop adding files if we've hit the limit

    final_prompt = "".join(prompt_parts)

    # Final check and truncation if necessary (shouldn't happen often if logic is correct above)
    if len(final_prompt) > max_chars:
        final_prompt = final_prompt[:max_chars - 50] + "\n... [PROMPT TRUNCATED] ..."

    return final_prompt

# --- AI Integration (Placeholder) ---
def generate_changelog_with_ai(prompt):
    """
    Placeholder function for calling an AI API (e.g., OpenAI, Gemini).
    You would replace this with actual API calls.
    """
    print("\n--- AI Prompt (sent to LLM) ---")
    print(prompt)
    print(f"--- Prompt Length: {len(prompt)} characters ---")
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
    return response.text


# --- Main Execution ---
if __name__ == "__main__":
    current_dir = os.getcwd()
    print(f"Analyzing Git changes in: {current_dir}")

    changed_files, full_diff = get_git_changes(current_dir)

    if not changed_files and not full_diff:
        print("No changes found or an error occurred. Exiting.")
    else:
        print(f"\nFound {len(changed_files)} changed files (before filtering).")
        filtered_files = filter_files(changed_files, IGNORE_EXTENSIONS)
        print(f"Filtered down to {len(filtered_files)} relevant files.")

        if not filtered_files and not full_diff:
            print("No relevant files found after filtering. Nothing to generate a changelog for.")
        else:
            ai_prompt = prepare_ai_prompt(filtered_files, full_diff, MAX_PROMPT_CHARS)
            changelog = generate_changelog_with_ai(ai_prompt)

            print("\n--- GENERATED CHANGELOG ---")
            formatter = MarkdownFormatter()
            formatted_text = formatter.format_for_terminal(changelog)
            print(formatted_text)
