"""Standard MCP interface for the assistant's domain and memory tools.

MCP (Model Context Protocol) lets an external agent discover and invoke tools
through a common contract. The FastAPI application calls the same underlying
functions directly for deterministic demo reliability; this module exposes
those functions over MCP without duplicating business logic.

The main API never imports this module, so an unavailable optional ``mcp``
package cannot break FastAPI. This module is also import-safe without the
package and prints a clear installation instruction if executed in that state.
"""

from typing import Dict, List, Union

from .tools import (
    detect_protocol_risks as detect_risks_tool,
    generate_action_plan as generate_plan_tool,
    recall_user_memory as recall_memory_tool,
    save_user_memory as save_memory_tool,
    search_protocol as search_protocol_tool,
    summarize_protocol_section as summarize_section_tool,
)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # FastAPI/mock mode remains usable without MCP installed.
    FastMCP = None  # type: ignore[assignment]


def search_protocol(query: str) -> dict:
    """Search indexed study documents and return grounded chunks."""
    return search_protocol_tool(query)


def summarize_protocol_section(section_query: str) -> dict:
    """Retrieve and summarize a protocol section with sources."""
    return summarize_section_tool(section_query)


def detect_protocol_risks(focus_area: str = "general") -> dict:
    """Detect evidence-backed operational study risks."""
    return detect_risks_tool(focus_area)


def generate_action_plan(risks: Union[List[Dict[str, object]], str]) -> dict:
    """Convert risk records or a focus area into owned actions."""
    return generate_plan_tool(risks)


def save_user_memory(key: str, value: str) -> dict:
    """Save a user preference or durable fact in local SQLite."""
    return save_memory_tool(key, value)


def recall_user_memory(query: str) -> dict:
    """Search locally stored user memory."""
    return recall_memory_tool(query)


TOOL_FUNCTIONS = (
    search_protocol,
    summarize_protocol_section,
    detect_protocol_risks,
    generate_action_plan,
    save_user_memory,
    recall_user_memory,
)

if FastMCP is not None:
    mcp = FastMCP("clinical-trial-protocol-tools")
    for tool_function in TOOL_FUNCTIONS:
        mcp.tool()(tool_function)
else:
    mcp = None


if __name__ == "__main__":
    if mcp is None:
        raise SystemExit(
            "MCP support is unavailable. Run: pip install -r requirements.txt"
        )
    mcp.run()
