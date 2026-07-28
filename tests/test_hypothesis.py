from hypothesis import form_hypothesis


def test_form_hypothesis_recent_deploy_timeout():
    evidence = {
        "logs": [
            {"message": "TimeoutError: payment-service exceeded 300ms"},
            {"message": "checkout failed with HTTP 500"},
        ],
        "metrics": {
            "error_rate_pct": {"baseline": 0.2, "current": 12.0},
            "recent_deploy": {
                "version": "v1.84.2",
                "change": "timeout reduced from 3000ms to 300ms",
            },
        },
    }
    result = form_hypothesis(evidence)
    assert result["id"] == "recent-deploy-timeout-regression"
    assert result["confidence"] >= 0.8


def test_form_hypothesis_insufficient_evidence():
    result = form_hypothesis({"logs": [], "metrics": {}})
    assert result["id"] == "insufficient-evidence"
    assert result["confidence"] < 0.5
