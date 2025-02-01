# pip install -U "autogen-agentchat" "autogen-ext[openai]"
from dotenv import load_dotenv

load_dotenv()
import argparse
import json
import sys
from pathlib import Path
import asyncio
from datetime import datetime

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from typing import Dict, List


class FileHandler:
    @staticmethod
    def read_file_content(file_path: str) -> str:
        try:
            with open(file_path, "r") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            sys.exit(1)

    @staticmethod
    def parse_changes_file(changes_file: str) -> Dict[str, str]:
        try:
            with open(changes_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error parsing changes file: {e}")
            sys.exit(1)


class FileSystemAnalyzer:
    def __init__(self, base_path: Path):
        self.base_path = base_path

    def get_file_system_dict(self) -> Dict[str, str]:
        file_system = {}
        for file_path in self.base_path.rglob("*.py"):
            relative_path = str(file_path.relative_to(self.base_path))
            file_system[relative_path] = FileHandler.read_file_content(str(file_path))
        return file_system

    @staticmethod
    def identify_affected_files(
        file_system: Dict[str, str], changes: Dict[str, str]
    ) -> List[str]:
        affected = set(changes.keys())
        for file_path, content in file_system.items():
            for changed_file in changes.keys():
                if changed_file in content and file_path not in affected:
                    affected.add(file_path)
        return list(affected)


class AIAnalyzer:
    def __init__(self):
        self.agent = AssistantAgent(
            "code_analyzer", OpenAIChatCompletionClient(model="gpt-4")
        )

    async def analyze_file_changes(
        self, file_system: Dict[str, str], changes: Dict[str, str]
    ) -> Dict:
        analysis_prompt = self._build_analysis_prompt(file_system, changes)
        analysis_result = await self.agent.run(task=analysis_prompt)

        # with open("analysis_result.py", "w") as f:
        #     f.write(str(analysis_result))

        return analysis_result.messages[1].content

    def _build_analysis_prompt(
        self, file_system: Dict[str, str], changes: Dict[str, str]
    ) -> str:
        prompt = FileHandler.read_file_content("chat_agent_prompt.txt")

        for path, content in file_system.items():
            prompt += f"\n{path}:\n{content}\n"

        for path, change in changes.items():
            prompt += f"\n{path}:\n{change}\n"

        return prompt


class ResultFormatter:
    @staticmethod
    def parse_result_to_json(analysis_str: str) -> Dict:
        analysis_str = analysis_str.strip()

        # Clean up the analysis string
        if "TERMINATE" in analysis_str:
            analysis_str = analysis_str.replace("TERMINATE", "")

        # Remove JSON code block markers
        for marker in ["```json", "```JSON"]:
            if analysis_str.startswith(marker):
                analysis_str = analysis_str.replace(marker, "")

        analysis_str = analysis_str.strip()

        # Remove trailing backticks
        while analysis_str.endswith("```"):
            analysis_str = analysis_str[:-3].strip()

        # Clean non-printable characters
        analysis_str = "".join(" " if ord(char) < 32 else char for char in analysis_str)

        try:
            return json.loads(analysis_str)
        except Exception as e:
            print(f"Error parsing result to JSON: {e}")
            return analysis_str

    @staticmethod
    def format_output_to_md(analysis_json: Dict) -> str:
        try:
            result = ""
            for key in analysis_json.keys():
                result += f"### {key.capitalize()}\n"
                if key == "changes_required":
                    for file_path, code_block in analysis_json[key].items():
                        result += f"#### {file_path}\n"
                        if code_block:
                            # Clean up the code block by removing escaped newlines
                            code_block = code_block.replace("\\n", "\n")
                            # Remove any trailing/leading whitespace
                            code_block = code_block.strip()
                            result += f"{code_block}\n\n"
                else:
                    result += f"{analysis_json[key]}\n\n"
            return result
        except Exception as e:
            print(f"Error formatting output: {e}, output: {analysis_json}")
            return analysis_json


class ChatAgent:
    def __init__(self, base_path: Path):
        self.file_system_analyzer = FileSystemAnalyzer(base_path)
        self.ai_analyzer = AIAnalyzer()
        self.result_formatter = ResultFormatter()
        self.result_file = (
            f"results/result_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.md"
        )

    async def run_interactive_session(self):
        print("Enter your questions/changes (type 'exit' to quit):")

        with open(self.result_file, "w") as f:
            question_count = 1
            while True:
                file_system = self.file_system_analyzer.get_file_system_dict()
                user_input = input(f"{question_count}> ")

                if user_input.lower() == "exit":
                    break

                changes = {"user_query": user_input}

                # Write question and get response
                f.write(f"\n### {question_count}. {user_input}\n")
                f.flush()
                question_count += 1

                # Analyze and format response
                result = await self.ai_analyzer.analyze_file_changes(
                    file_system, changes
                )
                result = self.result_formatter.parse_result_to_json(result)
                result = self.result_formatter.format_output_to_md(result)

                # Write response
                f.write(f"\n{result}\n")
                f.flush()

                print("Response has been written to", self.result_file)


async def main():
    parser = argparse.ArgumentParser(
        description="Analyze file system changes and their impact."
    )
    parser.add_argument(
        "--dir",
        type=str,
        required=True,
        help="Directory containing the files to analyze",
    )
    args = parser.parse_args()

    chat_agent = ChatAgent(Path(args.dir))
    await chat_agent.run_interactive_session()


if __name__ == "__main__":
    asyncio.run(main())
