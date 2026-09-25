from datetime import UTC, datetime

BODY = {
    "shipment_id": "SHP-100",
    "source": "manual",
    "reported_at": datetime(2026, 3, 2, 8, 0, tzinfo=UTC).isoformat(),
    "carrier": "Maersk",
    "origin": "Shanghai",
    "destination": "Rotterdam",
    "raw_text": "Container held at customs pending documentation",
}


async def test_create_persists_record_and_returns_201(client):
    response = await client.post("/exceptions", json=BODY)

    assert response.status_code == 201
    body = response.json()
    assert body["shipment_id"] == "SHP-100"
    assert body["source"] == "manual"
    assert body["carrier"] == "Maersk"
    assert body["raw_text"] == "Container held at customs pending documentation"
    assert body["metadata"] is None

    listed = await client.get("/exceptions")
    assert [row["shipment_id"] for row in listed.json()] == ["SHP-100"]


async def test_create_seeds_agent_state_for_the_shipment_thread(client, agent):
    await client.post("/exceptions", json=BODY)

    assert len(agent.seeded) == 1
    config, state = agent.seeded[0]
    assert config["configurable"]["thread_id"] == "shipment:SHP-100"
    assert state["shipment_id"] == "SHP-100"


async def test_create_invokes_agent_for_the_shipment_thread(client, agent):
    response = await client.post("/exceptions", json=BODY)

    assert response.status_code == 201
    assert agent.invoked_thread_ids == ["shipment:SHP-100"]
    messages = agent.invoke_inputs[0]["messages"]
    assert len(messages) == 1
    assert "SHP-100" in messages[0].content


async def test_create_returns_201_when_analysis_fails(client, agent):
    agent.fail_on_invoke = True

    response = await client.post("/exceptions", json=BODY)

    assert response.status_code == 201
    assert response.json()["shipment_id"] == "SHP-100"
    assert agent.invoke_attempts == 1


async def test_create_rejects_duplicate_shipment_id(client, session, make_exception):
    session.add(make_exception(shipment_id="SHP-100"))
    await session.flush()

    response = await client.post("/exceptions", json=BODY)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"
    assert "SHP-100" in response.json()["error"]["message"]


async def test_create_rejects_blank_raw_text(client, agent):
    response = await client.post("/exceptions", json={**BODY, "raw_text": ""})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert agent.invoke_attempts == 0


async def test_create_rejects_unknown_source(client, agent):
    response = await client.post("/exceptions", json={**BODY, "source": "carrier_pigeon"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert agent.invoke_attempts == 0