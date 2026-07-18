"""Web app page route tests."""

from fastapi.testclient import TestClient

from web_app.main import app


client = TestClient(app)


def test_template_pages_render_successfully():
    for route in ["/", "/philippines", "/indonesia", "/dashboard"]:
        response = client.get(route)

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

def test_nudge_event_endpoint_accepts_replay_events():
    response = client.post(
        "/api/nudge-event",
        json={
            "event_type": "transcript",
            "timestamp": "00:00:01",
            "speaker": "customer",
            "chunk": "Hello from replay",
        },
    )

    assert response.status_code == 200
    assert response.json()["broadcast"] is True
    assert response.json()["event_type"] == "transcript"
