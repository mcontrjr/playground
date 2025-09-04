#!/usr/bin/env python3

import subprocess
import os
import argparse
from typing import List, Dict, Tuple
import google.generativeai as genai
from dotenv import load_dotenv
from markdown.markdown_formatter import MarkdownFormatter

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_CONFIGS = {
    "gemini-2.5-flash": {
        "max_input_tokens": 1048576,
        "max_output_tokens": 8192,
        "cost_per_million_input": 0.075,
    },
    "gemini-2.5-pro": {
        "max_input_tokens": 2097152,
        "max_output_tokens": 8192,
        "cost_per_million_input": 1.25,
    }
}

OUTPUT_TOKEN_RESERVE = 2000
SYSTEM_OVERHEAD_TOKENS = 100
IGNORE_EXTENSIONS = ['.csv', '.json', '.log', '.lock', '.md', '.txt', '.yaml', '.yml', '.toml', '.xml', '.svg', '.env', '.gitignore', '.pyc']
GIT_DIFF_RANGE = "HEAD~1..HEAD"

def get_git_changes(repo_path="."):
    """Get git changes and file contents."""
    os.chdir(repo_path)

    try:
        diff_summary = subprocess.run(
            ['git', 'diff', '--name-status', GIT_DIFF_RANGE],
            capture_output=True, text=True, check=True
        )
        full_diff = subprocess.run(
            ['git', 'diff', GIT_DIFF_RANGE],
            capture_output=True, text=True, check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Git error: {e}")
        return [], ""

    changed_files = []
    for line in diff_summary.stdout.strip().split('\n'):
        if not line:
            continue

        parts = line.split('\t', 1)
        status, file_path = parts[0], parts[1]

        if status == 'R':
            file_path = file_path.split('\t')[1]

        content = ""
        if status in ['A', 'M', 'R']:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                else:
                    content = f"File '{file_path}' not found locally"
            except Exception as e:
                content = f"Could not read '{file_path}': {e}"
        elif status == 'D':
            content = "File was deleted"

        changed_files.append({
            'status': status,
            'file_path': file_path,
            'content': content
        })

    return changed_files, full_diff.stdout.strip()

def filter_files(files_info, ignore_exts):
    """Filters files based on their extensions."""
    filtered = []
    for f_info in files_info:
        _, ext = os.path.splitext(f_info['file_path'])
        if ext.lower() not in [e.lower() for e in ignore_exts]:
            filtered.append(f_info)
    return filtered

def select_optimal_model(estimated_tokens: int) -> str:
    """Select most cost-effective model based on token usage."""
    for model_name in ["gemini-2.5-flash", "gemini-2.5-pro"]:
        config = MODEL_CONFIGS[model_name]
        available = config["max_input_tokens"] - OUTPUT_TOKEN_RESERVE - SYSTEM_OVERHEAD_TOKENS

        if estimated_tokens <= available:
            print(f"Selected {model_name} ({estimated_tokens:,} tokens, limit {available:,})")
            return model_name

    print(f"Warning: Content large, using gemini-2.5-pro ({estimated_tokens:,} tokens)")
    return "gemini-2.5-pro"

def count_tokens(text: str, model_name: str) -> int:
    """Count tokens using model tokenizer."""
    try:
        model = genai.GenerativeModel(model_name)
        return model.count_tokens(text).total_tokens
    except Exception as e:
        print(f"Warning: Token count failed, using estimate: {e}")
        return len(text) // 4

def prepare_optimized_prompt(files: List[Dict], full_diff: str, model_name: str) -> Tuple[str, Dict]:
    """Build optimized prompt using token counting."""
    config = MODEL_CONFIGS[model_name]
    max_tokens = config["max_input_tokens"] - OUTPUT_TOKEN_RESERVE - SYSTEM_OVERHEAD_TOKENS

    instruction = (
        "Generate a comprehensive but concise changelog based on the following Git changes. "
        "Structure your response with sections for:\n"
        "- **New Features**\n"
        "- **Bug Fixes**\n"
        "- **Performance Improvements**\n"
        "- **Breaking Changes**\n"
        "- **Other Changes**\n\n"
        "Focus on meaningful changes. Ignore trivial formatting or whitespace changes.\n\n"
    )

    instruction_tokens = count_tokens(instruction, model_name)
    remaining_tokens = max_tokens - instruction_tokens

    print(f"Instruction: {instruction_tokens:,} tokens")
    print(f"Available: {remaining_tokens:,} tokens")

    prompt_parts = [instruction]

    full_diff_tokens = count_tokens(full_diff, model_name) if full_diff else 0

    if full_diff and full_diff_tokens < remaining_tokens * 0.7:
        print(f"Including full diff ({full_diff_tokens:,} tokens)")
        prompt_parts.extend(["\n=== GIT DIFF ===\n", full_diff])
        remaining_tokens -= full_diff_tokens
    else:
        print(f"Using file-by-file approach (diff too large: {full_diff_tokens:,} tokens)")
        prompt_parts.append("\n=== FILE CHANGES ===\n")

        # Prepare files with token counts
        file_data = []
        for f in files:
            header = f"\n**File: {f['file_path']}** (Status: {f['status']})\n```\n"
            footer = "\n```\n"
            content_tokens = count_tokens(f['content'], model_name)
            header_tokens = count_tokens(header + footer, model_name)

            file_data.append({
                'info': f,
                'header': header,
                'footer': footer,
                'content_tokens': content_tokens,
                'header_tokens': header_tokens,
                'total_tokens': content_tokens + header_tokens
            })

        file_data.sort(key=lambda x: x['total_tokens'])

        tokens_used = 0
        included = 0

        for data in file_data:
            if tokens_used + data['total_tokens'] <= remaining_tokens:
                prompt_parts.extend([data['header'], data['info']['content'], data['footer']])
                tokens_used += data['total_tokens']
                included += 1
                print(f"  Included {data['info']['file_path']} ({data['total_tokens']:,} tokens)")
            else:
                available = remaining_tokens - tokens_used - data['header_tokens']
                if available > 100:
                    chars_per_token = len(data['info']['content']) / max(data['content_tokens'], 1)
                    max_chars = int(available * chars_per_token * 0.8)

                    truncated = data['info']['content'][:max_chars]
                    if len(truncated) < len(data['info']['content']):
                        truncated += "\n\n... [TRUNCATED] ..."

                    prompt_parts.extend([data['header'], truncated, data['footer']])
                    actual_tokens = count_tokens(data['header'] + truncated + data['footer'], model_name)
                    tokens_used += actual_tokens
                    included += 1
                    print(f"  Truncated {data['info']['file_path']} ({actual_tokens:,} tokens)")
                else:
                    print(f"  Skipped {data['info']['file_path']} (insufficient tokens)")
                break

        print(f"Included {included}/{len(files)} files using {tokens_used:,} tokens")

    final_prompt = "".join(prompt_parts)
    actual_tokens = count_tokens(final_prompt, model_name)

    stats = {
        'model': model_name,
        'final_tokens': actual_tokens,
        'max_tokens': max_tokens,
        'utilization': (actual_tokens / max_tokens) * 100,
        'cost': (actual_tokens / 1_000_000) * config['cost_per_million_input']
    }

    return final_prompt, stats

def generate_changelog(prompt: str, model_name: str, show_prompt: bool = False) -> str:
    """Generate changelog using Gemini model."""
    if show_prompt:
        print("\nPrompt preview:")
        print(prompt[:500] + ("..." if len(prompt) > 500 else ""))
        print("-" * 50)

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.3,
                'top_p': 0.8,
                'max_output_tokens': MODEL_CONFIGS[model_name]['max_output_tokens']
            }
        )
        return response.text
    except Exception as e:
        return f"Error generating changelog: {e}"

def main():
    global GIT_DIFF_RANGE

    parser = argparse.ArgumentParser(description="Generate AI changelog from Git changes")
    parser.add_argument("-r", "--range", default=GIT_DIFF_RANGE, help=f"Git range (default: {GIT_DIFF_RANGE})")
    parser.add_argument("-m", "--model", choices=["auto", "gemini-2.5-flash", "gemini-2.5-pro"],
                      default="auto", help="Model to use (default: auto)")
    parser.add_argument("--show-prompt", action="store_true", help="Show prompt sent to AI")
    parser.add_argument("--show-stats", action="store_true", help="Show token statistics")
    parser.add_argument("-p", "--path", default=".", help="Repository path")

    args = parser.parse_args()
    GIT_DIFF_RANGE = args.range

    print(f"Analyzing Git changes in: {os.path.abspath(args.path)}")
    print(f"Git range: {GIT_DIFF_RANGE}")

    changed_files, full_diff = get_git_changes(args.path)
    if not changed_files and not full_diff:
        print("No changes found.")
        return

    print(f"Found {len(changed_files)} files (before filtering)")
    filtered_files = filter_files(changed_files, IGNORE_EXTENSIONS)
    print(f"Filtered to {len(filtered_files)} relevant files:")
    for f in filtered_files:
        print(f"  - {f['file_path']}")

    if not filtered_files and not full_diff:
        print("No relevant files found after filtering.")
        return

    if args.model == "auto":
        estimate = len(full_diff) // 4 + sum(len(f['content']) for f in filtered_files) // 4
        model = select_optimal_model(estimate)
    else:
        model = args.model
        print(f"Using model: {model}")

    print(f"Preparing prompt for {model}...")
    prompt, stats = prepare_optimized_prompt(filtered_files, full_diff, model)

    if args.show_stats:
        print(f"\nToken Statistics:")
        print(f"  Model: {stats['model']}")
        print(f"  Input tokens: {stats['final_tokens']:,}")
        print(f"  Max tokens: {stats['max_tokens']:,}")
        print(f"  Utilization: {stats['utilization']:.1f}%")
        print(f"  Cost estimate: ${stats['cost']:.4f}")

    print(f"Generating changelog...")
    changelog = generate_changelog(prompt, model, args.show_prompt)

    print("\n" + "="*50)
    print("GENERATED CHANGELOG")
    print("="*50)
    formatter = MarkdownFormatter()
    print(formatter.format_for_terminal(changelog))
    print("="*50)

if __name__ == "__main__":
    main()
