# 📝 Automated Changelog Generation Workflow

This repository includes an automated changelog generation system powered by AI that creates meaningful changelogs from Git commits.

## 🚀 Quick Setup

### 1. Prerequisites

Ensure your repository has these files:
- `changelog.py` (the AI changelog generator)
- `requirements.txt` or `pyproject.toml` (Python dependencies)
- `.github/workflows/changelog.yml` (GitHub Actions workflow)

### 2. Configure GitHub Secrets

Add your Gemini API key to GitHub repository secrets:

1. Go to `Settings` → `Secrets and variables` → `Actions`
2. Click `New repository secret`
3. Name: `GEMINI_API_KEY`
4. Value: Your Google AI Studio API key

### 3. Get a Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Click "Get API Key"
3. Create a new API key
4. Copy the key to use in GitHub secrets

## 🔄 How It Works

### Automatic Triggers

The workflow runs automatically on:

- **Direct pushes** to `main`/`master` branches
- **Merged pull requests** to `main`/`master` branches
- **Manual workflow dispatch** (with custom options)

### Manual Triggers

You can manually trigger the workflow from the GitHub Actions tab:

1. Go to `Actions` → `Generate Changelog`
2. Click `Run workflow`
3. Optional: Customize git range (e.g., `HEAD~5..HEAD`)
4. Optional: Choose AI model (`auto`, `gemini-2.5-flash`, `gemini-2.5-pro`)

## 📋 Features

### Smart Analysis
- **Git Integration**: Analyzes actual code changes, not just commit messages
- **File Filtering**: Ignores non-relevant files (.log, .csv, .md, etc.)
- **Context Awareness**: Understands code structure and relationships

### AI-Powered Generation
- **Intelligent Categorization**: Automatically sorts changes into:
  - 🆕 **New Features**
  - 🐛 **Bug Fixes**
  - ⚡ **Performance Improvements**
  - 💥 **Breaking Changes**
  - 🔧 **Other Changes**

### Cost Optimization
- **Automatic Model Selection**: Chooses most cost-effective model
- **Token Management**: Optimizes prompts to stay within limits
- **Cost Estimation**: Shows estimated API costs

### GitHub Integration
- **Automatic Commits**: Commits generated changelog to repository
- **PR Comments**: Posts changelog preview on merged PRs
- **Artifact Upload**: Saves changelog as downloadable artifact

## 🛠️ Local Development

### Running Locally

```bash
# Basic usage - analyze last commit
python changelog.py

# Custom git range
python changelog.py --range "HEAD~3..HEAD"

# Save to file
python changelog.py --output CHANGELOG.md

# Show token statistics
python changelog.py --show-stats

# Show AI prompt for debugging
python changelog.py --show-prompt
```

### Available Options

```bash
python changelog.py --help
```

- `-r, --range`: Git range to analyze (default: HEAD~1..HEAD)
- `-m, --model`: AI model (`auto`, `gemini-2.5-flash`, `gemini-2.5-pro`)
- `-o, --output`: Output file path (default: stdout with formatting)
- `--show-stats`: Display token usage and cost estimates
- `--show-prompt`: Show the prompt sent to the AI
- `-p, --path`: Repository path (default: current directory)

## 📁 File Structure

```
.github/
└── workflows/
    └── changelog.yml          # GitHub Actions workflow
changelog.py                   # Main changelog generator
requirements.txt               # Python dependencies
markdown/                      # Terminal formatting utilities
├── markdown_formatter.py
├── colored_logger.py
└── spinner.py
CHANGELOG.md                   # Generated changelog (auto-created)
```

## 🔧 Configuration

### Model Selection

The workflow automatically selects the most cost-effective model:

- **gemini-2.5-flash**: Fast and economical for smaller changes
- **gemini-2.5-pro**: More capable for complex analysis

### Git Range Customization

Different scenarios use different git ranges:

- **Direct pushes**: `HEAD~1..HEAD` (last commit)
- **Merged PRs**: `base_sha..head_sha` (full PR range)
- **Manual**: User-specified range

### Workflow Permissions

The workflow requires these permissions:
- `contents: write` - To commit the changelog
- `pull-requests: read` - To read PR information

## 🎯 Best Practices

### For Repository Maintainers

1. **Meaningful Commits**: Write descriptive commit messages
2. **Logical Grouping**: Group related changes in single commits when possible
3. **Review Output**: Periodically review generated changelogs for accuracy

### For Contributors

1. **Clear PR Descriptions**: Provide context in pull request descriptions
2. **Focused Changes**: Keep PRs focused on single features/fixes when possible
3. **Code Comments**: Add comments explaining complex logic

## 🚨 Troubleshooting

### Common Issues

**Workflow fails with "API key not found"**
- Verify `GEMINI_API_KEY` is set in repository secrets
- Check the API key is valid and not expired

**No changelog generated**
- Ensure there are actual code changes (not just documentation)
- Check that changed files aren't all in the ignore list
- Verify the git range contains commits

**Permission denied when committing**
- Ensure workflow has `contents: write` permission
- Check branch protection rules don't block workflow commits

**Token limit exceeded**
- The workflow will automatically use smaller context windows
- For very large changes, consider multiple smaller commits

### Debug Mode

Enable debug information:

```bash
python changelog.py --show-stats --show-prompt --range "HEAD~3..HEAD"
```

This shows:
- Token usage statistics
- Model selection reasoning
- The actual prompt sent to AI
- Cost estimates

## 🔍 Example Output

### Generated Changelog Structure

```markdown
# New Features
- Added user authentication system with JWT tokens
- Implemented real-time notifications using WebSocket connections

# Bug Fixes
- Fixed memory leak in file processing module
- Resolved race condition in concurrent user sessions

# Performance Improvements
- Optimized database queries reducing response time by 40%
- Implemented caching layer for frequently accessed data

# Breaking Changes
- **BREAKING**: Changed API response format for user endpoints
- Removed deprecated `legacy_auth` parameter from login endpoint

# Other Changes
- Updated documentation for new authentication flow
- Refactored error handling utilities
```

### Workflow Logs

The workflow provides detailed logging:

```
✅ Analyzing Git changes in: /github/workspace
📊 Git range: HEAD~1..HEAD
🔍 Found 5 files (before filtering)
📋 Filtered to 3 relevant files:
   - src/auth.py
   - src/api.py
   - tests/test_auth.py
🤖 Selected gemini-2.5-flash (2,456 tokens, limit 1,046,476)
💰 Cost estimate: $0.0002
📝 Generating changelog...
✅ Changelog written to: CHANGELOG.md
```

## 📈 Advanced Usage

### Custom Prompts

The changelog generator uses intelligent prompts that:

1. **Analyze Code Structure**: Understands file relationships and imports
2. **Categorize Changes**: Automatically sorts into meaningful categories
3. **Provide Context**: Explains the "why" behind changes, not just "what"
4. **Filter Noise**: Ignores trivial formatting and whitespace changes

### Integration with Release Process

You can integrate this with your release workflow:

```yaml
# In another workflow file
- name: Generate Release Changelog
  run: |
    python changelog.py --range "v1.0.0..HEAD" --output RELEASE_NOTES.md
```

### Multiple Repository Support

The changelog generator can analyze any Git repository:

```bash
python changelog.py --path /path/to/repo --range "v2.0.0..HEAD"
```

## 📚 Additional Resources

- [Google AI Studio](https://aistudio.google.com/) - Get your API key
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Git Range Syntax](https://git-scm.com/book/en/v2/Git-Tools-Revision-Selection)

## 🤝 Contributing

To improve the changelog generator:

1. Test changes locally first
2. Consider token usage impact
3. Maintain backward compatibility
4. Update documentation for new features

---

*This automated changelog system helps maintain clear project history with minimal manual effort. The AI analyzes actual code changes to generate meaningful, categorized changelog entries that help users understand what changed and why.*