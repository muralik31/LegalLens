from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_upload_analyze_fetch_and_question() -> None:
    upload = client.post(
        "/upload",
        files={
            "file": (
                "contract.txt",
                b"Tenant shall pay Rs 10000 monthly rent. Termination without notice may apply.",
                "text/plain",
            )
        },
    )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]

    analyze = client.post("/analyze", json={"document_id": document_id, "language": "en"})
    assert analyze.status_code == 200
    body = analyze.json()
    assert body["contract_risk_score"] >= 3
    assert body["document_type"] == "rental_agreement"

    ask = client.post(
        "/ask-question",
        json={"document_id": document_id, "question": "What is the rent?", "language": "en"},
    )
    assert ask.status_code == 200
    assert "rent" in ask.json()["answer"].lower()

    fetch = client.get(f"/document/{document_id}")
    assert fetch.status_code == 200
    assert fetch.json()["analysis"]["document_id"] == document_id


def test_upload_rejects_unsupported_content_type() -> None:
    response = client.post(
        "/upload",
        files={"file": ("malware.bin", b"x", "application/octet-stream")},
    )
    assert response.status_code == 400


def test_upload_rejects_empty_file() -> None:
    response = client.post(
        "/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert response.status_code == 400
