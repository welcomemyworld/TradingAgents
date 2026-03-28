import unittest

from tradingagents.llm_clients.factory import create_llm_client
from tradingagents.llm_clients.openai_client import invoke_with_backoff


class DummyResponse:
    def __init__(self, content):
        self.content = content


class TransientError(Exception):
    status_code = 429


class PermanentError(Exception):
    status_code = 400


class OpenAIClientRetryTests(unittest.TestCase):
    def test_retry_helper_retries_transient_errors_then_succeeds(self):
        attempts = {"count": 0}
        sleeps = []

        def operation():
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise TransientError("busy")
            return DummyResponse("ok")

        response = invoke_with_backoff(
            operation,
            max_attempts=3,
            base_delay_seconds=0.01,
            max_delay_seconds=0.02,
            sleep_fn=sleeps.append,
        )

        self.assertEqual(response.content, "ok")
        self.assertEqual(attempts["count"], 3)
        self.assertEqual(len(sleeps), 2)

    def test_retry_helper_does_not_retry_non_transient_errors(self):
        attempts = {"count": 0}

        def operation():
            attempts["count"] += 1
            raise PermanentError("bad request")

        with self.assertRaises(PermanentError):
            invoke_with_backoff(
                operation,
                max_attempts=3,
                base_delay_seconds=0.01,
                max_delay_seconds=0.02,
                sleep_fn=lambda _: None,
            )

        self.assertEqual(attempts["count"], 1)

    def test_vectorengine_provider_is_supported_as_openai_compatible(self):
        client = create_llm_client(
            provider="vectorengine",
            model="gpt-5.4",
            base_url="https://api.vectorengine.ai/v1",
        )

        self.assertTrue(client.validate_model())


if __name__ == "__main__":
    unittest.main()
