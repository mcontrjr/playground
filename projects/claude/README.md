# Git Changelog Generator

A Python script that uses Claude's API to generate human-readable changelogs from git diffs between commits.

## Features

- Analyzes git diffs between any two commits
- Generates AI-powered changelog summaries
- Handles large diffs by intelligent chunking
- Categorizes files as added, modified, deleted, or renamed
- Outputs structured changelog entries suitable for release notes

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your Claude API key:
   ```bash
   export CLAUDE_API_KEY="your-api-key-here"
   ```

## Usage

```bash
# Generate changelog between two commits
python changelog_generator.py <commit1> <commit2>

# Generate changelog from a commit to HEAD
python changelog_generator.py <commit>

# Save changelog to file
python changelog_generator.py <commit1> <commit2> -o changelog.md

# Examples
python changelog_generator.py HEAD~5 HEAD
python changelog_generator.py v1.0.0 v1.1.0
python changelog_generator.py abc123 def456 -o release-notes.md
```

## How it works

1. **Git Analysis**: Extracts diff content and file change statistics between commits
2. **Intelligent Chunking**: Splits large diffs into manageable chunks (100KB max per request)
3. **AI Processing**: Uses Claude API to analyze changes and generate human-readable summaries
4. **Changelog Generation**: Combines all analyses into a coherent changelog entry

## Output Format

The generated changelog includes:
- Overall summary of changes
- Key features added, modified, or removed
- Breaking changes and important notes
- Detailed file change listings
- Categorized file modifications

## Requirements

- Python 3.7+
- Git repository
- Claude API key
- requests library