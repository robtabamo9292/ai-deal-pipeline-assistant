"""Headless Streamlit smoke tests: the public demos must work without an API key."""
from streamlit.testing.v1 import AppTest


def _click(app: AppTest, label: str) -> AppTest:
    button = next(button for button in app.button if button.label == label)
    button.click().run()
    assert not app.exception
    return app


def test_streamlit_loads_and_previews_fictional_case(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = AppTest.from_file("app.py", default_timeout=30).run()
    assert not app.exception

    _click(app, "Preview fictional case (no API key)")
    assert any(
        "Northstar" in str(element.value)
        for element in app.markdown
    )
    assert not any("earned no evidence credit" in str(w.value) for w in app.warning)


def test_invented_claim_preview_shows_the_source_check(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = AppTest.from_file("app.py", default_timeout=30).run()

    _click(app, "Preview invented-claim check (no API key)")
    warnings = [str(w.value) for w in app.warning]
    assert any("3 extracted signals were not found" in w for w in warnings)
    assert any("Fortune 500 health systems" in w for w in warnings)
