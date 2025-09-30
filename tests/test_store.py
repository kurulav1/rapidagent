def test_kv_store(temp_store):
    temp_store.set_kv("foo", "bar")
    assert temp_store.get_kv("foo") == "bar"

def test_agent_lifecycle(temp_store):
    agent_id = temp_store.create_agent("123", "TestAgent", "gpt-4o-mini", ["search"])
    agent = temp_store.get_agent("123")
    assert agent["name"] == "TestAgent"
    assert "search" in temp_store.get_agent_tools("123")

def test_messages_and_traces(temp_store):
    agent_id = temp_store.create_agent("123", "TestAgent", "gpt-4o-mini", [])
    temp_store.add_agent_message(agent_id, "user", "hello")
    msgs = temp_store.get_agent_messages(agent_id)
    assert msgs[0]["content"] == "hello"
    temp_store.add_trace(agent_id, "thought", {"note": "thinking"})
    traces = temp_store.list_traces(agent_id)
    assert traces[0]["type"] == "thought"
    assert "note" in traces[0]["content"]
