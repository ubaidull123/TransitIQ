import pytest

from transitiq.main import analyze_shipment, build_parser


async def test_analyze_shipment_invokes_the_shipment_thread(agent):
    await analyze_shipment(agent, "SHP-7")

    assert agent.invoked_thread_ids == ["shipment:SHP-7"]


async def test_analyze_shipment_returns_the_agents_final_message(agent):
    agent.result_text = "Customs hold, severity high"

    assert await analyze_shipment(agent, "SHP-7") == "Customs hold, severity high"


async def test_analyze_shipment_returns_empty_string_when_the_agent_says_nothing(agent):
    assert await analyze_shipment(agent, "SHP-7") == ""


def test_parser_requires_a_shipment_id():
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_parser_reads_the_shipment_id_argument():
    assert build_parser().parse_args(["SHP-7"]).shipment_id == "SHP-7"