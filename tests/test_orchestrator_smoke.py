from mcp.orchestrator import run_pipeline

def test_pipeline_runs():
    text = "Invoice\nAnthropic, PBC\nDate of issue July 6, 2025\nTotal $6.00"
    res = run_pipeline(text)
    assert res is not None
    assert "agents_ran" in res.meta
    assert res.vendor != ""
