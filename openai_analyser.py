# tested, needs polish
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from typing import Dict


class OpenAIAnalyzer:
    """OpenAI-specific implementation of the AI analyzer"""

    async def analyze(self, prompt: str) -> Dict:
        """Analyze the code using OpenAI's API"""
        self.agent = AssistantAgent(
            "code_analyzer", OpenAIChatCompletionClient(model="gpt-4")
        )
        analysis_result = await self.agent.run(task=prompt)
        return analysis_result.messages[1].content  # type: ignore
