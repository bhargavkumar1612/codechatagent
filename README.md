# Code Change Impact Analyzer

A CLI tool that uses AutoGen to analyze the impact of code changes across a Python project. This tool helps developers understand the potential risks and effects of proposed changes before implementing them.

## Features

- Analyzes proposed code changes against existing codebase
- Identifies affected files and dependencies
- Provides detailed impact analysis using GPT-4
- Suggests modifications to maintain system stability
- CLI interface for easy integration into workflows

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd code-change-analyzer
```

2. Install dependencies:
```bash
pip install -U "autogen-agentchat" "autogen-ext[openai]" python-dotenv
```


3. Set up your environment variables:
Create a `.env` file with your OpenAI API key:
```bash
OPENAI_API_KEY=<your-openai-api-key>
```


## Usage

1. Prepare your changes in a JSON file (e.g., `changes.json`):
```bash
python chatagent_openai.py --dir ./proj --changes ./proj/changes.json --output ./proj/analysis_result.json
```


### Command Line Arguments

- `--dir`: Directory containing the Python files to analyze (required)
- `--changes`: Path to JSON file containing proposed changes (required)
- `--output`: Path to save analysis results (optional)

### Example

```bash
python chatagent_openai.py --dir ./proj --changes ./proj/changes.json --output ./proj/analysis_result.json
```
## Output

The tool provides:
1. Impact Analysis
   - Potential risks of the changes
   - Detailed analysis of code modifications
   - Suggestions for maintaining functionality

2. Affected Files
   - List of directly modified files
   - Files potentially impacted by the changes
   - Dependency relationships

## Limitations

- Currently only analyzes Python files
- Basic dependency detection using string matching
- Requires OpenAI API key and credits

## Note
Still under development
