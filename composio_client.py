import requests
from dataclasses import dataclass
from typing import List
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain import hub
from langchain_openai import ChatOpenAI
from composio_langchain import ComposioToolSet, Action
import os

REPO_URL = os.getenv("REPO_URL")


@dataclass
class GithubConfig:
    """Configuration for Github repository access"""

    repo_url: str
    branch: str = "main"
    composio_api_key: str = os.getenv("COMPOSIO_API_KEY")



class GithubContentFetcher:
    def __init__(self, config: GithubConfig):
        self.config = config
        self.agent_executor = self._setup_agent()

    def _setup_agent(self) -> AgentExecutor:
        """Initialize and configure the LangChain agent"""
        llm = ChatOpenAI()
        prompt = hub.pull("hwchase17/openai-functions-agent")

        composio_toolset = ComposioToolSet(api_key=self.config.composio_api_key)
        tools = composio_toolset.get_tools(
            actions=[Action.GITHUB_GET_REPOSITORY_CONTENT]
        )

        agent = create_openai_functions_agent(llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True)

    def _create_task_prompt(self, file_path: str) -> str:
        """Create the task prompt for the agent"""
        return f"from the repo {self.config.repo_url}, get the content of the file {file_path} in the {self.config.branch} branch"

    def _parse_download_link(self, result_output: str) -> str:
        """Extract download link from agent's output"""
        try:
            download_link = (
                result_output.split("Download")[1].split("](")[1].split(")")[0]
            )
            return download_link
        except IndexError:
            raise ValueError("Could not parse download link from the output")

    def _download_file(self, download_link: str) -> str:
        """Download file content from the given link"""
        response = requests.get(download_link)
        response.raise_for_status()  # Raise exception for bad status codes
        return response.text

    def get_file_content(self, file_path: str) -> str:
        """
        Fetch content of a specific file from the Github repository

        Args:
            file_path (str): Path to the file in the repository

        Returns:
            str: Content of the requested file
        """
        # Get download link using agent
        result = self.agent_executor.invoke(
            {"input": self._create_task_prompt(file_path)}
        )

        # Parse and use download link
        download_link = self._parse_download_link(result["output"])
        return self._download_file(download_link)


def main():
    # Configuration
    config = GithubConfig(repo_url=REPO_URL)


    # Initialize fetcher
    fetcher = GithubContentFetcher(config)

    try:
        # Get file content
        content = fetcher.get_file_content("app.py")
        print(content)
    except Exception as e:
        print(f"Error fetching file content: {str(e)}")


if __name__ == "__main__":
    main()
