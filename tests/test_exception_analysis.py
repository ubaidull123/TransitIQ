from datetime import UTC, datetime

ANALYZED_STATE = {
    "shipment_id": "SHP-100",
    "status": "analyzed",
    "current_step": "done",
    "exception_type": "customs_hold",
    "severity": "critical",
    "missing_information": ["product license"],
    "recommended_actions": ["contact customs broker"],
    "actions": [
        {
            "id": "ACT-1",
            "description": "contact customs broker",
            "status": "pending",
        }
    ],
    "context": [
        {"source": "operator", "content": "called broker", "created_at": "T1"}
    ],
    "analysis_history": [
        {"exception_type": "customs_hold", "severity": "critical", "created_at": "T1"}
    ],
}


async def test_analysis_returns_stored_analysis(client, session, make_exception, agent):
    session.add(make_exception(shipment_id="SHP-100"))
    await session.flush()
    agent.state_values = ANALYZED_STATE

    response = await client.get("/exceptions/SHP-100/analysis")

    assert response.status_code == 200
    body = response.json()
    assert body["shipment_id"] == "SHP-100"
    assert body["status"] == "analyzed"
    assert body["current_step"] == "done"
    assert body["exception_type"] == "customs_hold"
    assert body["severity"] == "critical"
    assert body["missing_information"] == ["product license"]
    assert body["recommended_actions"] == ["contact customs broker"]
    assert body["context"] == ANALYZED_STATE["context"]
    assert body["analysis_history"] == ANALYZED_STATE["analysis_history"]


async def test_analysis_reads_the_shipment_thread(client, session, make_exception, agent):
    session.add(make_exception(shipment_id="SHP-100"))
    await session.flush()

    await client.get("/exceptions/SHP-100/analysis")

    assert agent.state_reads == ["shipment:SHP-100"]


async def test_analysis_reports_unanalyzed_shipment_with_initial_defaults(
    client, session, make_exception, agent
):
    session.add(make_exception(shipment_id="SHP-100"))
    await session.flush()

    response = await client.get("/exceptions/SHP-100/analysis")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "new"
    assert body["exception_type"] is None
    assert body["severity"] is None
    assert body["missing_information"] == []
    assert body["recommended_actions"] == []
    assert body["actions"] == []
    assert body["analysis_history"] == []
    assert body["updated_at"] is None


async def test_analysis_exposes_the_snapshot_timestamp(
    client, session, make_exception, agent
):
    session.add(make_exception(shipment_id="SHP-100"))
    await session.flush()
    agent.state_values = ANALYZED_STATE
    agent.state_created_at = datetime(2026, 9, 2, 10, 0, tzinfo=UTC)

    response = await client.get("/exceptions/SHP-100/analysis")

    assert datetime.fromisoformat(response.json()["updated_at"]) == datetime(
        2026, 9, 2, 10, 0, tzinfo=UTC
    )


async def test_analysis_returns_404_for_unknown_shipment(client, agent):
    response = await client.get("/exceptions/UNKNOWN/analysis")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert agent.state_reads == []


async def test_analyze_reruns_the_agent_for_the_shipment_thread(
    client, session, make_exception, agent
):
    session.add(make_exception(shipment_id="SHP-100"))
    await session.flush()

    response = await client.post("/exceptions/SHP-100/analyze")

    assert response.status_code == 200
    assert agent.invoked_thread_ids == ["shipment:SHP-100"]


async def test_analyze_returns_the_refreshed_analysis(
    client, session, make_exception, agent
):
    session.add(make_exception(shipment_id="SHP-100"))
    await session.flush()
    agent.result_state = ANALYZED_STATE

    response = await client.post("/exceptions/SHP-100/analyze")

    assert response.status_code == 200
    assert response.json()["exception_type"] == "customs_hold"
    assert response.json()["severity"] == "critical"


async def test_analyze_reports_the_failure_reason_in_the_response(
    client, session, make_exception, agent
):
    session.add(make_exception(shipment_id="SHP-100"))
    await session.flush()
    agent.fail_on_invoke = True

    response = await client.post("/exceptions/SHP-100/analyze")

    assert response.status_code == 200
    assert response.json()["analysis_error"] == "model unavailable"


async def test_analyze_clears_a_previous_error_on_a_later_success(
    client, session, make_exception, agent
):
    session.add(make_exception(shipment_id="SHP-100"))
    await session.flush()
    agent.fail_on_invoke = True
    await client.post("/exceptions/SHP-100/analyze")

    agent.fail_on_invoke = False
    agent.result_state = ANALYZED_STATE
    response = await client.post("/exceptions/SHP-100/analyze")

    assert response.json()["analysis_error"] is None
    assert response.json()["exception_type"] == "customs_hold"


async def test_analysis_surfaces_a_stored_failure(client, session, make_exception, agent):
    session.add(make_exception(shipment_id="SHP-100"))
    await session.flush()
    agent.state_values = {**ANALYZED_STATE, "analysis_error": "API key expired"}

    response = await client.get("/exceptions/SHP-100/analysis")

    assert response.status_code == 200
    assert response.json()["analysis_error"] == "API key expired"


async def test_analysis_reports_no_error_for_a_clean_run(
    client, session, make_exception, agent
):
    session.add(make_exception(shipment_id="SHP-100"))
    await session.flush()
    agent.state_values = ANALYZED_STATE

    response = await client.get("/exceptions/SHP-100/analysis")

    assert response.json()["analysis_error"] is None


async def test_analyze_returns_404_for_unknown_shipment(client, agent):
    response = await client.post("/exceptions/UNKNOWN/analyze")

    assert response.status_code == 404
    assert agent.invoke_attempts == 0


async def test_analyze_reports_unanalyzed_when_the_agent_fails(
    client, session, make_exception, agent
):
    session.add(make_exception(shipment_id="SHP-100"))
    await session.flush()
    agent.fail_on_invoke = True

    response = await client.post("/exceptions/SHP-100/analyze")

    assert response.status_code == 200
    assert response.json()["status"] == "new"
    assert agent.invoke_attempts == 1