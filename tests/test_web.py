"""Fast Flask application smoke tests."""

import io

import pytest

from detectra import create_app


@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True, SECRET_KEY="test-secret")
    return app.test_client()


@pytest.mark.parametrize(
    "path",
    ["/", "/upload", "/mixture", "/multiple"],
)
def test_pages_render(client, path):
    response = client.get(path)
    assert response.status_code == 200


def test_upload_rejects_non_csv_file(client):
    response = client.post(
        "/upload",
        data={"file": (io.BytesIO(b"not a spectrum"), "sample.txt")},
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_multiple_requires_a_selection(client):
    response = client.post("/multiple", data={}, follow_redirects=False)
    assert response.status_code == 302
