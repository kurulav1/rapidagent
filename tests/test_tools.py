from rapidagent.tools import ToolRegistry

def test_list_tools_contains_search_and_calculator(tool_registry):
    tools = [t["name"] for t in tool_registry.list_tools()]
    assert "search" in tools
    assert "calculator" in tools

def test_search_tool(tool_registry):
    result = tool_registry.run("search", "pizza")
    assert "Search results" in result

def test_calculator_valid(tool_registry):
    result = tool_registry.run("calculator", "2 + 3 * 4")
    assert result == "14"

def test_calculator_invalid(tool_registry):
    result = tool_registry.run("calculator", "2 + unknown")
    assert "Error" in result

def test_unknown_tool(tool_registry):
    result = tool_registry.run("doesnotexist", "input")
    assert "not found" in result
