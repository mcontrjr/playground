#!/usr/bin/env python3
"""
Git Changelog Generator using Claude API
Generates human-readable changelogs from git diffs between commits.
"""

import os
import sys
import json
import subprocess
import argparse
from typing import Dict, List, Tuple, Optional
import requests
from dataclasses import dataclass


@dataclass
class FileChange:
    """Represents a file change in the git diff"""
    path: str
    status: str  # 'added', 'modified', 'deleted', 'renamed'
    additions: int
    deletions: int
    old_path: Optional[str] = None  # For renamed files


class ChangelogGenerator:
    """Main class for generating changelogs from git diffs"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        # Configuration for handling large diffs
        self.max_diff_size = 100000  # 100KB chunks
        self.max_files_per_request = 50
    
    def get_git_diff(self, commit1: str, commit2: str) -> Tuple[str, List[FileChange]]:
        """Get git diff between two commits and parse file changes"""
        try:
            # Get the actual diff content
            diff_cmd = ["git", "diff", f"{commit1}..{commit2}"]
            diff_result = subprocess.run(diff_cmd, capture_output=True, text=True, check=True)
            
            # Get file statistics
            stat_cmd = ["git", "diff", "--stat", f"{commit1}..{commit2}"]
            stat_result = subprocess.run(stat_cmd, capture_output=True, text=True, check=True)
            
            # Get list of changed files with their status
            name_status_cmd = ["git", "diff", "--name-status", f"{commit1}..{commit2}"]
            name_status_result = subprocess.run(name_status_cmd, capture_output=True, text=True, check=True)
            
            # Parse file changes
            file_changes = self._parse_file_changes(stat_result.stdout, name_status_result.stdout)
            
            return diff_result.stdout, file_changes
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Git command failed: {e}")
    
    def _parse_file_changes(self, stat_output: str, name_status_output: str) -> List[FileChange]:
        """Parse git diff output to extract file changes"""
        file_changes = []
        
        # Create a mapping of file status
        status_map = {}
        for line in name_status_output.strip().split('\n'):
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                status = parts[0]
                if status.startswith('R'):  # Renamed file
                    status_map[parts[2]] = ('renamed', parts[1])
                else:
                    path = parts[1]
                    if status == 'A':
                        status_map[path] = ('added', None)
                    elif status == 'D':
                        status_map[path] = ('deleted', None)
                    elif status == 'M':
                        status_map[path] = ('modified', None)
        
        # Parse stat output for additions/deletions
        for line in stat_output.strip().split('\n'):
            if '|' not in line:
                continue
            parts = line.split('|')
            if len(parts) != 2:
                continue
                
            file_path = parts[0].strip()
            stats_part = parts[1].strip()
            
            additions = deletions = 0
            if '+' in stats_part:
                additions = stats_part.count('+')
            if '-' in stats_part:
                deletions = stats_part.count('-')
            
            # Get status from status_map
            status, old_path = status_map.get(file_path, ('modified', None))
            
            file_changes.append(FileChange(
                path=file_path,
                status=status,
                additions=additions,
                deletions=deletions,
                old_path=old_path
            ))
        
        return file_changes
    
    def _chunk_diff(self, diff_content: str, file_changes: List[FileChange]) -> List[Tuple[str, List[FileChange]]]:
        """Split large diffs into manageable chunks"""
        if len(diff_content) <= self.max_diff_size and len(file_changes) <= self.max_files_per_request:
            return [(diff_content, file_changes)]
        
        chunks = []
        current_diff = ""
        current_files = []
        
        # Split by files in the diff
        diff_parts = diff_content.split('diff --git')
        
        for i, part in enumerate(diff_parts):
            if i == 0 and not part.strip().startswith('a/'):
                # First part might be metadata
                continue
                
            file_diff = 'diff --git' + part if i > 0 else part
            
            # Find corresponding file change
            file_change = None
            for fc in file_changes:
                if fc.path in file_diff or (fc.old_path and fc.old_path in file_diff):
                    file_change = fc
                    break
            
            if len(current_diff) + len(file_diff) > self.max_diff_size or len(current_files) >= self.max_files_per_request:
                if current_diff and current_files:
                    chunks.append((current_diff, current_files))
                current_diff = file_diff
                current_files = [file_change] if file_change else []
            else:
                current_diff += '\n' + file_diff
                if file_change and file_change not in current_files:
                    current_files.append(file_change)
        
        if current_diff and current_files:
            chunks.append((current_diff, current_files))
        
        return chunks
    
    def _call_claude_api(self, prompt: str) -> str:
        """Make a request to Claude API"""
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 4000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            return data['content'][0]['text']
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
        except KeyError as e:
            raise Exception(f"Unexpected API response format: {e}")
    
    def generate_changelog_chunk(self, diff_content: str, file_changes: List[FileChange], commit1: str, commit2: str) -> str:
        """Generate changelog for a chunk of the diff"""
        files_summary = self._create_files_summary(file_changes)
        
        prompt = f"""Analyze this git diff and create a changelog entry. The diff is between commits {commit1} and {commit2}.

File Changes Summary:
{files_summary}

Git Diff:
```
{diff_content[:50000]}  # Truncate very long diffs
```

Please provide:
1. A brief summary of the overall changes
2. Key features added, modified, or removed
3. Any breaking changes or important notes
4. List of files changed with their purpose

Format as a clean, readable changelog entry suitable for release notes."""
        
        return self._call_claude_api(prompt)
    
    def _create_files_summary(self, file_changes: List[FileChange]) -> str:
        """Create a summary of file changes"""
        added = [f for f in file_changes if f.status == 'added']
        modified = [f for f in file_changes if f.status == 'modified']
        deleted = [f for f in file_changes if f.status == 'deleted']
        renamed = [f for f in file_changes if f.status == 'renamed']
        
        summary = []
        if added:
            summary.append(f"Added ({len(added)}): {', '.join(f.path for f in added[:10])}")
            if len(added) > 10:
                summary.append(f"  ... and {len(added) - 10} more files")
        
        if modified:
            summary.append(f"Modified ({len(modified)}): {', '.join(f.path for f in modified[:10])}")
            if len(modified) > 10:
                summary.append(f"  ... and {len(modified) - 10} more files")
        
        if deleted:
            summary.append(f"Deleted ({len(deleted)}): {', '.join(f.path for f in deleted[:10])}")
            if len(deleted) > 10:
                summary.append(f"  ... and {len(deleted) - 10} more files")
        
        if renamed:
            summary.append(f"Renamed ({len(renamed)}): {', '.join(f'{f.old_path} -> {f.path}' for f in renamed[:5])}")
            if len(renamed) > 5:
                summary.append(f"  ... and {len(renamed) - 5} more files")
        
        return '\n'.join(summary)
    
    def generate_changelog(self, commit1: str, commit2: str) -> str:
        """Generate complete changelog between two commits"""
        print(f"Generating changelog from {commit1} to {commit2}...")
        
        # Get git diff and file changes
        diff_content, file_changes = self.get_git_diff(commit1, commit2)
        
        if not diff_content.strip():
            return f"No changes found between {commit1} and {commit2}"
        
        print(f"Found {len(file_changes)} changed files")
        
        # Split into chunks if necessary
        chunks = self._chunk_diff(diff_content, file_changes)
        print(f"Processing {len(chunks)} chunks...")
        
        changelog_parts = []
        for i, (chunk_diff, chunk_files) in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}...")
            chunk_changelog = self.generate_changelog_chunk(chunk_diff, chunk_files, commit1, commit2)
            changelog_parts.append(chunk_changelog)
        
        # Combine all parts
        if len(changelog_parts) == 1:
            return changelog_parts[0]
        else:
            # Generate a summary of all parts
            combined_prompt = f"""Here are changelog entries for different parts of a large commit diff between {commit1} and {commit2}:

{chr(10).join(f"Part {i+1}:{chr(10)}{part}{chr(10)}" for i, part in enumerate(changelog_parts))}

Please create a unified, coherent changelog that combines all these parts into a single, well-organized entry."""
            
            return self._call_claude_api(combined_prompt)


def main():
    parser = argparse.ArgumentParser(description='Generate changelog from git diff using Claude API')
    parser.add_argument('commit1', help='First commit hash or reference')
    parser.add_argument('commit2', help='Second commit hash or reference (defaults to HEAD)', nargs='?', default='HEAD')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    # Get API key from environment
    api_key = os.getenv('CLAUDE_API_KEY')
    if not api_key:
        print("Error: CLAUDE_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    try:
        generator = ChangelogGenerator(api_key)
        changelog = generator.generate_changelog(args.commit1, args.commit2)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(changelog)
            print(f"Changelog written to {args.output}")
        else:
            print(changelog)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()