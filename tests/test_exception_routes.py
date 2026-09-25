from datetime import UTC, datetime

import pytest


async def test_list_returns_empty_array_when_no_exceptions(client):
    response = await client.get("/exceptions")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_returns_stored_exception(client, session, make_exception):
    record = make_exception(
        shipment_id="SHP-42",
        carrier="Hapag-Lloyd",
        origin="Ningbo",
        destination="Hamburg",
        raw_text="Vessel delayed 4 days",
        meta_data={"severity_hint": "high"},
        reported_at=datetime(2026, 2, 14, 9, 30, tzinfo=UTC),
    )
    session.add(record)
    await session.flush()

    response = await client.get("/exceptions")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == record.id
    assert body[0]["shipment_id"] == "SHP-42"
    assert body[0]["source"] == "manual"
    assert body[0]["carrier"] == "Hapag-Lloyd"
    assert body[0]["origin"] == "Ningbo"
    assert body[0]["destination"] == "Hamburg"
    assert body[0]["raw_text"] == "Vessel delayed 4 days"
    assert body[0]["metadata"] == {"severity_hint": "high"}
    assert datetime.fromisoformat(body[0]["reported_at"]) == datetime(
        2026, 2, 14, 9, 30, tzinfo=UTC
    )


async def test_list_orders_newest_reported_at_first(client, session, make_exception):
    session.add_all(
        [
            make_exception(
                shipment_id="OLDEST", reported_at=datetime(2026, 1, 1, tzinfo=UTC)
            ),
            make_exception(
                shipment_id="NEWEST", reported_at=datetime(2026, 3, 1, tzinfo=UTC)
            ),
            make_exception(
                shipment_id="MIDDLE", reported_at=datetime(2026, 2, 1, tzinfo=UTC)
            ),
        ]
    )
    await session.flush()

    response = await client.get("/exceptions")

    assert [row["shipment_id"] for row in response.json()] == [
        "NEWEST",
        "MIDDLE",
        "OLDEST",
    ]


async def test_list_defaults_to_most_recent_fifty(client, session, make_exception):
    session.add_all(
        [
            make_exception(
                shipment_id=f"SHP-{index}",
                reported_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
            for index in range(51)
        ]
    )
    await session.flush()

    response = await client.get("/exceptions")

    assert response.status_code == 200
    assert len(response.json()) == 50


async def test_list_limit_caps_returned_rows(client, session, make_exception):
    session.add_all(
        [
            make_exception(
                shipment_id=f"SHP-{index}",
                reported_at=datetime(2026, 1, index + 1, tzinfo=UTC),
            )
            for index in range(3)
        ]
    )
    await session.flush()

    response = await client.get("/exceptions", params={"limit": 2})

    assert response.status_code == 200
    assert [row["shipment_id"] for row in response.json()] == ["SHP-2", "SHP-1"]


@pytest.mark.parametrize("limit", [0, -1, 201])
async def test_list_rejects_limit_outside_bounds(client, limit):
    response = await client.get("/exceptions", params={"limit": limit})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"