import pytest

from transitiq.workflow.middleware import load_ticket, validate_ticket_description


def test_validate_accepts_a_substantive_description():
    validate_ticket_description("Container held at customs pending documentation")


@pytest.mark.parametrize("description", [None, "", "   ", "ab", "abcd"])
def test_validate_rejects_missing_or_too_short_descriptions(description):
    with pytest.raises(ValueError):
        validate_ticket_description(description)


@pytest.mark.parametrize("description", ["error", "unknown"])
def test_validate_rejects_placeholders_long_enough_to_pass_the_length_rule(description):
    with pytest.raises(ValueError):
        validate_ticket_description(description)


@pytest.mark.parametrize("description", ["N/A", "ERROR", "  Unknown  "])
def test_validate_matches_placeholders_case_insensitively(description):
    with pytest.raises(ValueError):
        validate_ticket_description(description)


async def test_load_ticket_returns_none_when_state_already_holds_valid_raw_text():
    result = await load_ticket.abefore_model(
        {"raw_text": "Container held at customs pending documentation"}, None
    )

    assert result is None


async def test_load_ticket_validates_existing_raw_text_instead_of_hydrating():
    with pytest.raises(ValueError):
        await load_ticket.abefore_model({"raw_text": "bad"}, None)


async def test_load_ticket_requires_a_shipment_id_when_raw_text_is_absent():
    with pytest.raises(ValueError):
        await load_ticket.abefore_model({}, None)