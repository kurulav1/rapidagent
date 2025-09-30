import pytest
import tempfile
import os
from rapidagent.store import Store
from rapidagent.tools import ToolRegistry, CalculatorTool, SearchTool
from rapidagent.llms import LLMRegistry

@pytest.fixture
def temp_store():
    db_fd, path = tempfile.mkstemp()
    os.close(db_fd)
    try:
        store = Store(path)
        yield store
    finally:
        os.remove(path)

@pytest.fixture
def tool_registry():
    return ToolRegistry([CalculatorTool(), SearchTool()])



@pytest.fixture
def llm_registry(temp_store, tool_registry):
    return LLMRegistry(temp_store, tool_registry)