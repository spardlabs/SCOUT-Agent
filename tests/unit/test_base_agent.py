"""Tests for BaseAgent Claude tool-use loop."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scout.agents.base import BaseAgent


class ConcreteAgent(BaseAgent):
    """Test implementation of BaseAgent."""

    def get_system_prompt(self) -> str:
        return "You are a test agent."

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "add_numbers",
                "description": "Add two numbers",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"},
                    },
                    "required": ["a", "b"],
                },
            }
        ]

    async def execute_tool(self, tool_name: str, tool_input: dict):
        if tool_name == "add_numbers":
            return {"result": tool_input["a"] + tool_input["b"]}
        raise ValueError(f"Unknown tool: {tool_name}")


class TestBaseAgent:
    def _make_text_response(self, text):
        """Create a mock Claude response with text only (end_turn)."""
        block = MagicMock()
        block.type = "text"
        block.text = text
        response = MagicMock()
        response.stop_reason = "end_turn"
        response.content = [block]
        return response

    def _make_tool_response(self, tool_name, tool_input, tool_id="tool_123"):
        """Create a mock Claude response with a tool call."""
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = tool_name
        tool_block.input = tool_input
        tool_block.id = tool_id
        response = MagicMock()
        response.stop_reason = "tool_use"
        response.content = [tool_block]
        return response

    @pytest.mark.asyncio
    async def test_simple_text_response(self):
        """Agent returns text when Claude gives end_turn with no tool calls."""
        mock_client = MagicMock()
        mock_client.messages.create = MagicMock(
            return_value=self._make_text_response("Hello, I'm done!")
        )

        agent = ConcreteAgent(mock_client)
        result = await agent.run({"task": "say hello"})

        assert result["result"] == "Hello, I'm done!"
        assert result["tool_results"] == []

    @pytest.mark.asyncio
    async def test_tool_call_then_response(self):
        """Agent executes tool, then gets final text response."""
        mock_client = MagicMock()
        mock_client.messages.create = MagicMock(
            side_effect=[
                self._make_tool_response("add_numbers", {"a": 3, "b": 5}),
                self._make_text_response("The answer is 8"),
            ]
        )

        agent = ConcreteAgent(mock_client)
        result = await agent.run({"task": "add 3 and 5"})

        assert result["result"] == "The answer is 8"
        assert len(result["tool_results"]) == 1
        assert result["tool_results"][0]["tool"] == "add_numbers"
        assert result["tool_results"][0]["output"] == {"result": 8}

    @pytest.mark.asyncio
    async def test_tool_error_handling(self):
        """Agent handles tool execution errors gracefully."""
        mock_client = MagicMock()
        mock_client.messages.create = MagicMock(
            side_effect=[
                self._make_tool_response("unknown_tool", {}),
                self._make_text_response("I encountered an error"),
            ]
        )

        agent = ConcreteAgent(mock_client)
        result = await agent.run({"task": "do something"})

        assert result["result"] == "I encountered an error"

    @pytest.mark.asyncio
    async def test_max_turns_limit(self):
        """Agent stops after max_turns to prevent infinite loops."""
        mock_client = MagicMock()
        # Always return tool calls, never end_turn
        mock_client.messages.create = MagicMock(
            return_value=self._make_tool_response("add_numbers", {"a": 1, "b": 1})
        )

        agent = ConcreteAgent(mock_client, max_turns=3)
        result = await agent.run({"task": "loop forever"})

        assert "maximum number of turns" in result["result"]
        assert mock_client.messages.create.call_count == 3

    @pytest.mark.asyncio
    async def test_system_prompt_passed_to_claude(self):
        """Agent passes system prompt to Claude API call."""
        mock_client = MagicMock()
        mock_client.messages.create = MagicMock(
            return_value=self._make_text_response("done")
        )

        agent = ConcreteAgent(mock_client)
        await agent.run({"task": "test"})

        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs["system"] == "You are a test agent."

    @pytest.mark.asyncio
    async def test_tools_passed_to_claude(self):
        """Agent passes tool definitions to Claude API call."""
        mock_client = MagicMock()
        mock_client.messages.create = MagicMock(
            return_value=self._make_text_response("done")
        )

        agent = ConcreteAgent(mock_client)
        await agent.run({"task": "test"})

        call_kwargs = mock_client.messages.create.call_args
        tools = call_kwargs.kwargs["tools"]
        assert len(tools) == 1
        assert tools[0]["name"] == "add_numbers"
