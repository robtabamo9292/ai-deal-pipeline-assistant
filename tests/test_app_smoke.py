"""Headless Streamlit smoke test: public demo must work without an API key."""
from streamlit.testing.v1 import AppTest


def test_streamlit_loads_and_previews_fictional_case(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = AppTest.from_file("app.py", default_timeout=30).run()
    assert not app.exception

    preview = next(
        button for button in app.button
        if button.label == "Preview fictional case (no API key)"
    )
    preview.click().run()
    assert not app.exception
    assert any(
        "Northstar" in str(element.value)
        for element in app.markdown
    )
