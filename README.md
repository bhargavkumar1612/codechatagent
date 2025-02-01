# Code Chat Agent

A CLI tool that uses AutoGen to analyze the impact of code changes across a Python project. This tool helps developers understand the potential risks and effects of proposed changes before implementing them.

## Features

- Analyzes proposed code changes against existing codebase
- Identifies affected files and dependencies
- Provides detailed impact analysis using GPT-4
- Suggests modifications to maintain system stability
- CLI interface for easy integration into workflows
- Interactive mode for continuous analysis

## Installation

1. Clone the repository:
```bash
git clone [<repository-url>](https://github.com/bhargavkumar1612/codechatagent.git)
cd codechatagent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
Create a `.env` file with your OpenAI API key:
```bash
OPENAI_API_KEY=<your-openai-api-key>
```

## Usage

Run the analyzer in interactive mode:
```bash
python chatagent_openai.py --dir ./proj
```

### Command Line Arguments

- `--dir`: Directory containing the Python files to analyze (required)

The tool will continuously listen for your inputs and provide analysis and suggestions based on your proposed changes.

### Example

```bash
python chatagent.py --dir <directory_path> --agent <agent_type>
```
note: agent_type can be openai, claude, deepseek
currently only openai is tested

## Output

The tool provides analysis in a structured markdown format:

1. For each proposed change:
   - **Changes Required**: Detailed code changes with file paths
   - **Impact Analysis**: Assessment of how the changes affect the system
   - **Potential Risks**: Identification of possible issues or vulnerabilities
   - **Suggested Modifications**: Recommendations for improving the implementation

Example output format:
```markdown
### 1. [Description of Change]

### Changes_required
#### [filename]
```python
[code changes]
```

### Impact_analysis
[Detailed analysis of the change's impact]

### Potential_risks
[List of potential risks]

### Suggested_modifications
[Recommendations for implementation]
```

## Limitations

- Currently only analyzes Python files
- Basic dependency detection using string matching
- Requires OpenAI API key and credits

## Note
Still under development
