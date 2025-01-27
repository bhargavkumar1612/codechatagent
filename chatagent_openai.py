# pip install -U "autogen-agentchat" "autogen-ext[openai]"
from dotenv import load_dotenv
import argparse
import json
import sys
from pathlib import Path

load_dotenv()
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from typing import Dict, List


async def analyze_file_changes(
    file_system: Dict[str, str], changes: Dict[str, str]
) -> Dict:
    # Initialize the AI agent
    agent = AssistantAgent("code_analyzer", OpenAIChatCompletionClient(model="gpt-4"))

    # Prepare the analysis prompt
    analysis_prompt = _build_analysis_prompt(file_system, changes)
    # # Get AI analysis
    analysis_result = await agent.run(task=analysis_prompt)

    return {
        "impact_analysis": analysis_result,
        "affected_files": _identify_affected_files(file_system, changes),
    }


def _build_analysis_prompt(file_system: Dict[str, str], changes: Dict[str, str]) -> str:
    prompt = """
    Analyze the following file system changes and provide:
    1. Impact analysis of the changes
    2. Potential risks
    3. Suggested modifications to maintain functionality
    
    Original files:
    """
    for path, content in file_system.items():
        prompt += f"\n{path}:\n{content}\n"

    prompt += "\nProposed changes:\n"
    for path, change in changes.items():
        prompt += f"\n{path}:\n{change}\n"

    return prompt


def _identify_affected_files(
    file_system: Dict[str, str], changes: Dict[str, str]
) -> List[str]:
    affected = set(changes.keys())
    # Add files that might be impacted based on imports or dependencies
    # This is a simplified version - you might want to add more sophisticated dependency analysis
    for file_path, content in file_system.items():
        for changed_file in changes.keys():
            if changed_file in content and file_path not in affected:
                affected.add(file_path)
    return list(affected)


def read_file_content(file_path: str) -> str:
    """Read content from a file."""
    try:
        with open(file_path, "r") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        sys.exit(1)


def parse_changes_file(changes_file: str) -> Dict[str, str]:
    """Parse the changes JSON file."""
    try:
        with open(changes_file, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error parsing changes file: {e}")
        sys.exit(1)


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze file system changes and their impact."
    )
    parser.add_argument(
        "--dir",
        type=str,
        required=True,
        help="Directory containing the files to analyze",
    )
    parser.add_argument(
        "--changes",
        type=str,
        required=True,
        help="JSON file containing the proposed changes",
    )
    parser.add_argument(
        "--output", type=str, help="Output file for the analysis (optional)"
    )

    args = parser.parse_args()

    # Build file system dictionary
    base_path = Path(args.dir)
    file_system = {}
    for file_path in base_path.rglob("*.py"):
        relative_path = str(file_path.relative_to(base_path))
        file_system[relative_path] = read_file_content(str(file_path))

    # Read changes
    changes = parse_changes_file(args.changes)

    # Perform analysis
    result = await analyze_file_changes(file_system, changes)

    # Format output
    output = {
        "impact_analysis": result["impact_analysis"],
        "affected_files": result["affected_files"],
    }

    # Output results
    if args.output:
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
    else:
        print(output)


if __name__ == "__main__":
    asyncio.run(main())
