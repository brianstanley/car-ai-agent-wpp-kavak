import unittest
from unittest.mock import patch, MagicMock
from kavak_chatbot.services import KavakInfoService


class TestKavakInfoService(unittest.TestCase):
    def setUp(self):
        self.service = KavakInfoService(embedding_model="test-model")

    @patch("kavak_chatbot.services.kavak_info_service.OpenAI")
    def test_get_embedding_success(self, mock_openai):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client

        service = KavakInfoService(embedding_model="test-model")
        result = service.get_embedding("test text")
        self.assertEqual(result, [0.1, 0.2, 0.3])
        mock_client.embeddings.create.assert_called_once_with(model="test-model", input="test text")

    @patch.object(KavakInfoService, "get_embedding", return_value=[0.1, 0.2, 0.3])
    @patch("kavak_chatbot.services.kavak_info_service.SessionLocal")
    def test_create_kavak_info_with_embedding_success(self, mock_sessionlocal, mock_get_embedding):
        mock_session = MagicMock()
        mock_sessionlocal.return_value = mock_session
        mock_add = mock_session.add
        mock_commit = mock_session.commit
        mock_refresh = mock_session.refresh
        mock_close = mock_session.close

        service = KavakInfoService(embedding_model="test-model")
        result = service.create_kavak_info_with_embedding("text", ["meta1"], "title")
        self.assertTrue(result)
        mock_add.assert_called()
        mock_commit.assert_called()
        mock_close.assert_called()

    @patch.object(KavakInfoService, "get_embedding", return_value=[0.1, 0.2, 0.3])
    @patch("kavak_chatbot.services.kavak_info_service.SessionLocal")
    def test_search_similar_success(self, mock_sessionlocal, mock_get_embedding):
        mock_session = MagicMock()
        mock_sessionlocal.return_value = mock_session
        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.limit.return_value.all.return_value = ["result1", "result2"]

        service = KavakInfoService(embedding_model="test-model")
        results = service.search_similar("query", limit=2)
        self.assertEqual(results, ["result1", "result2"])
        mock_session.close.assert_called()

    @patch("kavak_chatbot.services.kavak_info_service.OpenAI")
    def test_get_embedding_error(self, mock_openai):
        mock_client = MagicMock()
        mock_client.embeddings.create.side_effect = Exception("fail")
        mock_openai.return_value = mock_client
        service = KavakInfoService(embedding_model="test-model")
        with self.assertRaises(Exception):
            service.get_embedding("fail")

    @patch.object(KavakInfoService, "get_embedding", side_effect=Exception("fail"))
    @patch("kavak_chatbot.services.kavak_info_service.SessionLocal")
    def test_create_kavak_info_with_embedding_error(self, mock_sessionlocal, mock_get_embedding):
        mock_session = MagicMock()
        mock_sessionlocal.return_value = mock_session
        service = KavakInfoService(embedding_model="test-model")
        result = service.create_kavak_info_with_embedding("text", ["meta1"], "title")
        self.assertFalse(result)
        mock_session.rollback.assert_called()
        mock_session.close.assert_called()

if __name__ == "__main__":
    unittest.main()