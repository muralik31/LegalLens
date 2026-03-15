from fastapi.testclient import TestClient


def test_phase2_analysis_supports_marathi_and_extra_outputs(client: TestClient) -> None:
    upload = client.post(
        "/upload",
        files={
            "file": (
                "contract.txt",
                (
                    b"Tenant shall pay Rs 10000 monthly rent. "
                    b"Termination without notice may apply. "
                    b"Indemnity and liability clauses are included."
                ),
                "text/plain",
            )
        },
    )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]

    analyze = client.post("/analyze", json={"document_id": document_id, "language": "mr"})
    assert analyze.status_code == 200
    body = analyze.json()
    assert body["language"] == "mr"
    assert body["summary"].startswith("या दस्तऐवजाचा सोपा सारांश")
    assert body["risk_heatmap"]
    assert body["clause_comparisons"]
    assert body["legal_terms_dictionary"]


def test_phase2_chat_endpoint(client: TestClient) -> None:
    upload = client.post(
        "/upload",
        files={
            "file": (
                "contract.txt",
                b"The tenant must give 2 months notice before termination. Monthly rent is Rs 15000.",
                "text/plain",
            )
        },
    )
    document_id = upload.json()["document_id"]

    response = client.post(
        "/chat",
        json={"document_id": document_id, "messages": ["What is the notice period?"], "language": "en"},
    )
    assert response.status_code == 200
    assert "notice" in response.json()["reply"].lower()


def test_disclaimer_endpoint_exists(client: TestClient) -> None:
    response = client.get("/disclaimer")
    assert response.status_code == 200
    assert "not legal advice" in response.json()["disclaimer"].lower()
