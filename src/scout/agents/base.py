import json
from abc import ABC, abstractmethod
from typing import Any

import anthropic

from scout.core.logging import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """Base class for all SCOUT agents. Handles Claude tool-use conversation loop."""

    def __init__(
        self,
        anthropic_client: anthropic.Anthropic,
        model: str = "claude-sonnet-4-20250514",
        max_turns: int = 20,
    ):
        self.client = anthropic_client
        self.model = model
        self.max_turns = max_turns

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""

    @abstractmethod
    def get_tools(self) -> list[dict]:
        """Return the Claude tool-use schemas for this agent."""

    @abstractmethod
    async def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        """Execute a tool call and return the result."""

    def _extract_text_result(self, response) -> str:
        """Extract text content from a Claude response."""
        for block in response.content:
            if block.type == "text":
                return block.text
        return ""

    async def run(self, task_context: dict) -> dict:
        """
        Main agent loop: send context to Claude, handle tool calls, repeat.

        Returns a dict with:
        - result: The final text response from Claude
        - tool_results: List of all tool execution results
        """
        messages = [
            {
                "role": "user",
                "content": json.dumps(task_context),
            }
        ]

        all_tool_results = []
        turns = 0

        while turns < self.max_turns:
            turns += 1
            logger.info(
                "agent_turn",
                agent=self.__class__.__name__,
                turn=turns,
            )

            response = self.client.messages.create(
                model=self.model,
                system=self.get_system_prompt(),
                tools=self.get_tools(),
                messages=messages,
                max_tokens=4096,
            )

            # Check if Claude is done (no more tool calls)
            if response.stop_reason == "end_turn":
                return {
                    "result": self._extract_text_result(response),
                    "tool_results": all_tool_results,
                }

            # Process tool calls
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.info(
                        "tool_call",
                        agent=self.__class__.__name__,
                        tool=block.name,
                    )
                    try:
                        result = await self.execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result) if not isinstance(result, str) else result,
                        })
                        all_tool_results.append({
                            "tool": block.name,
                            "input": block.input,
                            "output": result,
                        })
                    except Exception as e:
                        logger.error(
                            "tool_error",
                            agent=self.__class__.__name__,
                            tool=block.name,
                            error=str(e),
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Error: {e}",
                            "is_error": True,
                        })

            # Add assistant response and tool results to conversation
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        logger.warning("agent_max_turns_reached", agent=self.__class__.__name__)
        return {
            "result": "Agent reached maximum number of turns",
            "tool_results": all_tool_results,
        }
