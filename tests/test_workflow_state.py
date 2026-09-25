from transitiq.workflow.state import (
    create_initial_state,
    reduce_actions,
    reduce_context,
    reduce_history,
    reduce_last,
    reduce_status,
)


def test_reduce_last_prefers_new_value():
    assert reduce_last("old", "new") == "new"


def test_reduce_last_keeps_current_when_new_is_none():
    assert reduce_last("old", None) == "old"


def test_reduce_status_falls_back_to_new_when_nothing_recorded():
    assert reduce_status(None, None) == "new"


def test_reduce_status_keeps_current_when_new_is_none():
    assert reduce_status("analyzed", None) == "analyzed"


def test_reduce_actions_appends_actions_carrying_unseen_ids():
    merged = reduce_actions(
        [{"id": "ACT-1", "status": "pending"}], [{"id": "ACT-2", "status": "pending"}]
    )

    assert [action["id"] for action in merged] == ["ACT-1", "ACT-2"]


def test_reduce_actions_updates_matching_id_without_growing_the_list():
    merged = reduce_actions(
        [
            {"id": "ACT-1", "status": "pending"},
            {"id": "ACT-2", "status": "pending"},
        ],
        [{"id": "ACT-1", "status": "completed"}],
    )

    assert len(merged) == 2
    assert {action["id"]: action["status"] for action in merged} == {
        "ACT-1": "completed",
        "ACT-2": "pending",
    }


def test_reduce_context_drops_entries_repeating_source_content_and_time():
    entry = {"source": "operator", "content": "called broker", "created_at": "T1"}

    assert reduce_context([entry], [dict(entry)]) == [entry]


def test_reduce_context_keeps_same_content_from_a_different_source():
    current = [{"source": "operator", "content": "called broker", "created_at": "T1"}]
    new = [{"source": "carrier", "content": "called broker", "created_at": "T1"}]

    assert len(reduce_context(current, new)) == 2


def test_reduce_history_drops_a_repeat_run_of_the_same_type_and_time():
    run = {"exception_type": "customs_hold", "severity": "high", "created_at": "T1"}

    assert reduce_history([run], [dict(run)]) == [run]


def test_create_initial_state_leaves_raw_text_empty_so_middleware_hydrates_it():
    state = create_initial_state("SHP-1")

    assert state["shipment_id"] == "SHP-1"
    assert state["raw_text"] == ""
    assert state["analysis_error"] is None
    assert state["status"] == "new"
    assert state["current_step"] == "new"
    assert state["messages"] == []
    assert state["actions"] == []
    assert state["context"] == []