from app.mcp_server import mcp


def test_all_mcp_tools_register():
    assert mcp is not None
    names = {tool.name for tool in mcp._tool_manager.list_tools()}

    assert names == {
        "search_protocol",
        "summarize_protocol_section",
        "detect_protocol_risks",
        "generate_action_plan",
        "save_user_memory",
        "recall_user_memory",
    }
