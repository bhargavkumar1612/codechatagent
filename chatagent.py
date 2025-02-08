# pip install -U "autogen-agentchat" "autogen-ext[openai]"
from dotenv import load_dotenv

load_dotenv()
import argparse
import json
import sys
from pathlib import Path
import asyncio
from datetime import datetime
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

    @staticmethod
    def get_git_diff() -> str:
        """Get the git diff of unstaged changes"""
        try:
            import subprocess

            result = subprocess.run(["git", "diff"], capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            print(f"Error getting git diff: {e}")
            return ""

    @staticmethod
    def get_git_history(num_commits: int = 5) -> str:
        """Get the last n commit messages and their changes"""
        try:
            import subprocess

            result = subprocess.run(
                ["git", "log", f"-{num_commits}", "--patch"],
                capture_output=True,
                text=True,
            )
            return result.stdout
        except Exception as e:
            print(f"Error getting git history: {e}")
            return ""


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
    def __init__(self, agent_type: str = "openai"):
        """Initialize the AI analyzer with the specified agent type"""
        if agent_type == "openai":
            from openai_analyser import OpenAIAnalyzer

            self.agent = OpenAIAnalyzer()
        elif agent_type == "claude":
            from claude_analyser import ClaudeAnalyzer

            self.agent = ClaudeAnalyzer()
        elif agent_type == "deepseek":
            from deepseek_analyser import DeepSeekAnalyzer

            self.agent = DeepSeekAnalyzer()
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")

    async def analyze_file_changes(
        self, file_system: Dict[str, str], changes: Dict[str, str]
    ) -> Dict:
        analysis_prompt = self._build_analysis_prompt(file_system, changes)
        return await self.agent.analyze(analysis_prompt)

    def _build_analysis_prompt(
        self, file_system: Dict[str, str], changes: Dict[str, str]
    ) -> str:
        prompt = FileHandler.read_file_content("chat_agent_prompt.txt")

        # Add git information to the prompt
        git_diff = FileHandler.get_git_diff()
        if git_diff:
            prompt = prompt.replace("{git_diff}", f"\nUnstaged Changes:\n{git_diff}\n")
        # git_history = FileHandler.get_git_history()
        # if git_history:
        #     prompt = prompt.replace(
        #         "{git_history}", f"\nRecent Commit History:\n{git_history}\n"
        #     )
        file_system_str = ""
        for path, content in file_system.items():
            file_system_str += f"\n{path}:\n{content}\n"

        changes_str = ""
        for path, change in changes.items():
            changes_str += f"\n{path}:\n{change}\n"

        prompt = prompt.replace("{file_system}", file_system_str)
        prompt = prompt.replace("{changes}", changes_str)


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
            return analysis_str  # type: ignore

    @staticmethod
    def format_output_to_md(analysis_json: Dict) -> str:
        try:
            result = ""
            # Add timestamp for each analysis
            result += (
                f"*Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
            )

            for key in analysis_json.keys():
                result += f"### {key.capitalize()}\n"
                if key == "changes_required":
                    for file_path, code_block in analysis_json[key].items():
                        result += f"#### {file_path}\n"
                        if code_block:
                            code_block = code_block.replace("\\n", "\n").strip()
                            # Add language identifier for better markdown rendering
                            ext = file_path.split(".")[-1]
                            result += f"```{ext}\n{code_block}\n```\n\n"
                elif key == "impact_analysis":
                    # Format impact analysis as a bulleted list
                    impacts = analysis_json[key]
                    if isinstance(impacts, list):
                        for impact in impacts:
                            result += f"- {impact}\n"
                    else:
                        result += f"{impacts}\n"
                    result += "\n"
                elif key == "dependencies":
                    # Format dependencies as a table
                    deps = analysis_json[key]
                    if isinstance(deps, dict):
                        result += "| Module | Dependency Type |\n|---------|----------------|\n"
                        for module, dep_type in deps.items():
                            result += f"| {module} | {dep_type} |\n"
                    else:
                        result += f"{deps}\n"
                    result += "\n"
                else:
                    result += f"{analysis_json[key]}\n\n"
            return result
        except Exception as e:
            print(f"Error formatting output: {e}, output: {analysis_json}")
            return str(analysis_json)


class ChatAgent:
    def __init__(self, base_path: Path, agent_type: str = "openai"):
        self.file_system_analyzer = FileSystemAnalyzer(base_path)
        self.agent_type = agent_type
        self.ai_analyzer = AIAnalyzer(agent_type)
        self.result_formatter = ResultFormatter()
        # Create timestamp once for consistent folder naming
        self.timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self.result_dir = Path(f"results/{self.agent_type}/{self.timestamp}")
        self.debug_dir = self.result_dir / "debug"
        self.result_file = self.result_dir / "result.md"

    async def run_interactive_session(self):
        self._create_result_dir()
        print("Enter your questions/changes (type 'exit' to quit):")

        with open(self.result_file, "w") as f:
            print(f"# Agent: {self.agent_type}\n")
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

                # Save prompt to debug folder
                prompt = self.ai_analyzer._build_analysis_prompt(file_system, changes)
                debug_prompt_file = self.debug_dir / f"prompt_{question_count}.txt"
                with open(debug_prompt_file, "w") as debug_f:
                    debug_f.write(prompt)

                # Analyze and get raw response
                raw_result = await self.ai_analyzer.analyze_file_changes(
                    file_system, changes
                )

                # Save raw response to debug folder
                debug_response_file = self.debug_dir / f"response_{question_count}.txt"
                with open(debug_response_file, "w") as debug_f:
                    debug_f.write(raw_result)

                # Parse and format response
                result = self.result_formatter.parse_result_to_json(raw_result)
                result = self.result_formatter.format_output_to_md(result)

                # Write formatted response
                f.write(f"\n{result}\n")
                f.flush()

                question_count += 1
                print("Response has been written to", self.result_file)

    def _create_result_dir(self):
        self.result_dir.mkdir(parents=True, exist_ok=True)
        self.debug_dir.mkdir(parents=True, exist_ok=True)


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
    parser.add_argument(
        "--agent",
        type=str,
        default="openai",
        choices=["openai", "claude", "deepseek"],
        help="AI agent to use for analysis",
    )
    args = parser.parse_args()

    chat_agent = ChatAgent(Path(args.dir), args.agent)
    await chat_agent.run_interactive_session()


if __name__ == "__main__":
    asyncio.run(main())
