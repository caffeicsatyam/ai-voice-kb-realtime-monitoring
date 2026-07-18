"""Web app page route tests."""

from fastapi.testclient import TestClient

from web_app.main import app


client = TestClient(app)


def test_template_pages_render_successfully():
    for route in ["/", "/philippines", "/indonesia", "/dashboard"]:
        response = client.get(route)

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]