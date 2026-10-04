from app.services.calculator_gateway import LOCAL_TOOLS, CalculatorGateway
from mcp_server import calculator
from tests.test_calculator import MARIA


def test_server_publishes_every_tool_with_a_described_schema():
    tools = CalculatorGateway().tools()
    assert {t.name for t in tools} == set(LOCAL_TOOLS)
    assert all(t.description and "profile" in t.input_schema["properties"] for t in tools)


def test_mcp_result_matches_the_pure_function(caplog):
    result = CalculatorGateway().call("full_assessment", {"profile": MARIA})
    assert result == calculator.full_assessment(MARIA)
    assert "using in-process calculator" not in caplog.text


def test_falls_back_in_process_when_the_server_is_unavailable(caplog):
    result = CalculatorGateway(server_module="mcp_server.missing").call("what_if", {"profile": MARIA, "changes": {"savings": 0}})
    assert result["delta"] == 0 and result["resources"] == 50_000
    assert "using in-process calculator" in caplog.text
