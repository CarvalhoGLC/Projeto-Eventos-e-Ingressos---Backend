from unittest.mock import AsyncMock, MagicMock, patch


def test_external_movies_returns_tmdb_data(client):
    """
    Mocka a chamada HTTP real ao TMDb para não depender de rede/chave
    válida durante os testes.
    """
    fake_response_body = {"results": [{"title": "Filme Teste"}]}

    mock_response = MagicMock()
    mock_response.json.return_value = fake_response_body

    mock_async_client = AsyncMock()
    mock_async_client.get.return_value = mock_response

    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_async_client
    mock_context_manager.__aexit__.return_value = None

    with patch(
        "backend_events_tickets.services.httpx.AsyncClient",
        return_value=mock_context_manager,
    ):
        response = client.get("/external/movies", params={"query": "matrix"})

    assert response.status_code == 200
    assert response.json() == fake_response_body