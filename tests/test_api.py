from fastapi.testclient import TestClient


def create_assistant(client: TestClient):
    new_assistant = dict(
        name="test",
        description="test desc",
        system_prompt="hello",
    )
    resp = client.post("/assistants", json=new_assistant)
    return resp


def create_chat(client: TestClient, assistant_id: str):
    new_chat = dict(
        title="test_chat", created_at="2025-01-30", assistant_id=assistant_id
    )
    resp = client.post("/chats", json=new_chat)
    return resp


def test_create_assistant(test_client: TestClient):
    resp = create_assistant(test_client)
    assert resp.status_code == 201


def test_list_assistant(test_client: TestClient):
    create_assistant(test_client)
    resp = test_client.get("/assistants")
    data = resp.json()
    assert len(data) == 1


def test_create_chat(test_client: TestClient):
    resp = create_assistant(test_client)
    assistant: dict = resp.json()
    resp = create_chat(test_client, assistant.get("id"))
    assert resp.status_code == 201


def test_chat_message_completions(test_client: TestClient):
    resp = create_assistant(test_client)
    assistant: dict = resp.json()
    resp = create_chat(test_client, assistant.get("id"))
    chat: dict = resp.json()

    message = {"role": "user", "content": "Hello", "date": "2025-01-30"}

    resp = test_client.post(f"/chats/{chat.get('id')}/completions", json=message)
    assert resp.status_code == 200
