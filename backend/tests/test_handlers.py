import json
import os
import pytest
from unittest.mock import patch

# Mock AWS credentials before importing any boto3 clients
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "ap-south-1"

# Environment variables that handlers/services expect
os.environ["QUERY_CACHE_TABLE"] = "test-query-cache"
os.environ["SESSIONS_TABLE"] = "test-sessions"

import boto3
from moto import mock_aws

# Import modules to test
from utils.text_utils import parse_llm_json
from services.query_cache import make_query_hash, get_cached_response, put_cached_response
from lambdas.grievance_handler.handler import handler as grievance_handler
from lambdas.recommend_schemes.handler import handler as recommend_schemes_handler
from lambdas.rag_query.handler import handler as rag_query_handler


def make_event(body: dict) -> dict:
    """Helper to cleanly mock API Gateway proxy events."""
    return {
        "body": json.dumps(body),
        "headers": {},
        "requestContext": {}
    }


@pytest.fixture(scope="function")
def dynamodb_mock():
    """Moto fixture to mock DynamoDB responses for QueryCache testing."""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
        
        # Create Tables for cache and sessions
        query_cache_table = os.environ["QUERY_CACHE_TABLE"]
        dynamodb.create_table(
            TableName=query_cache_table,
            KeySchema=[{"AttributeName": "query_hash", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "query_hash", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )
        
        sessions_table = os.environ["SESSIONS_TABLE"]
        dynamodb.create_table(
            TableName=sessions_table,
            KeySchema=[
                {"AttributeName": "session_id", "KeyType": "HASH"},
                {"AttributeName": "event_id", "KeyType": "RANGE"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "session_id", "AttributeType": "S"},
                {"AttributeName": "event_id", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )
        
        yield dynamodb


class TestQueryCache:
    def test_make_query_hash_deterministic(self):
        hash1 = make_query_hash("Hello World", "en", "doc1")
        hash2 = make_query_hash("Hello World", "en", "doc1")
        assert hash1 == hash2

    def test_make_query_hash_case_insensitive(self):
        hash1 = make_query_hash("PMAY", "en", "doc1")
        hash2 = make_query_hash("pmay", "en", "doc1")
        hash3 = make_query_hash("   pmay   ", "en", "doc1")
        assert hash1 == hash2 == hash3

    def test_make_query_hash_language_differentiates(self):
        hash1 = make_query_hash("PMAY", "en", "doc1")
        hash2 = make_query_hash("PMAY", "hi", "doc1")
        assert hash1 != hash2

    def test_get_cached_response_miss(self, dynamodb_mock):
        q_hash = make_query_hash("missing", "en", None)
        assert get_cached_response(q_hash) is None

    def test_get_cached_response_hit(self, dynamodb_mock):
        q_hash = make_query_hash("hit", "en", None)
        put_cached_response(q_hash, {"answer": "Stored text"})
        
        cached = get_cached_response(q_hash)
        assert cached is not None
        assert cached["answer"] == "Stored text"

    def test_put_cached_response_ttl(self, dynamodb_mock):
        q_hash = make_query_hash("ttl", "en", None)
        put_cached_response(q_hash, {"answer": "TTL test"})
        
        table = dynamodb_mock.Table(os.environ["QUERY_CACHE_TABLE"])
        response = table.get_item(Key={"query_hash": q_hash})
        item = response.get("Item")
        
        assert item is not None
        assert "expires_at" in item
        assert isinstance(item["expires_at"], int)


class TestGrievanceHandler:
    @patch("lambdas.grievance_handler.handler.invoke_claude")
    def test_valid_request(self, mock_invoke):
        mock_invoke.return_value = "Dear Sir, my water supply is disrupted. Thank you."
        
        event = make_event({
            "issue_type": "Water",
            "description": "No water",
            "location": "Ward 5"
        })
        res = grievance_handler(event, None)
        assert res["statusCode"] == 200
        
        body = json.loads(res["body"])
        assert body["success"] is True
        assert "water supply is disrupted" in body["data"]["complaint_letter"]

    def test_missing_description(self):
        event = make_event({"issue_type": "Water", "location": "Ward 5"})
        res = grievance_handler(event, None)
        assert res["statusCode"] == 400

    def test_missing_location(self):
        event = make_event({"issue_type": "Water", "description": "No water"})
        res = grievance_handler(event, None)
        assert res["statusCode"] == 400

    def test_empty_body(self):
        event = make_event({})
        res = grievance_handler(event, None)
        assert res["statusCode"] == 400

    def test_invalid_json(self):
        event = {"body": "invalid::json"}
        res = grievance_handler(event, None)
        assert res["statusCode"] == 400

    @patch("lambdas.grievance_handler.handler.invoke_claude")
    def test_bedrock_exception_fallback(self, mock_invoke):
        mock_invoke.side_effect = Exception("AWS Bedrock timeout")
        event = make_event({
            "issue_type": "Water",
            "description": "No water",
            "location": "Ward 5"
        })
        res = grievance_handler(event, None)
        
        # Should gracefully return 200 with fallback letter
        assert res["statusCode"] == 200
        body = json.loads(res["body"])
        letter = body["data"]["complaint_letter"]
        assert "Subject: Complaint regarding Water" in letter

    @patch("lambdas.grievance_handler.handler.invoke_claude")
    def test_hindi_language_prompt(self, mock_invoke):
        mock_invoke.return_value = "हिंदी लेटर"
        event = make_event({
            "issue_type": "Water",
            "description": "No water",
            "location": "Ward 5",
            "language": "hi"
        })
        res = grievance_handler(event, None)
        
        assert mock_invoke.called
        prompt_arg = mock_invoke.call_args.kwargs.get("prompt", "")
        assert "हिंदी (Hindi)" in prompt_arg


class TestRecommendSchemesHandler:
    @patch("lambdas.recommend_schemes.handler.invoke_claude")
    def test_valid_farmer_profile(self, mock_invoke):
        # Provide valid JSON output array
        mock_invoke.return_value = json.dumps([
            {"name": "PM KISAN", "description": "Test", "eligibility": [], "apply_steps": []}
        ])
        
        event = make_event({
            "age": 30,
            "state": "MH",
            "income": 50000,
            "occupation": "Farmer"
        })
        res = recommend_schemes_handler(event, None)
        assert res["statusCode"] == 200
        
        data = json.loads(res["body"])["data"]
        schemes = data["schemes"]
        assert len(schemes) == 1
        assert schemes[0]["name"] == "PM KISAN"

    def test_missing_age(self):
        event = make_event({"state": "MH", "income": 50000, "occupation": "Farmer"})
        res = recommend_schemes_handler(event, None)
        assert res["statusCode"] == 400

    def test_age_out_of_range(self):
        # 0 age should be invalid
        event = make_event({"age": 0, "state": "MH", "income": 50000, "occupation": "Farmer"})
        assert recommend_schemes_handler(event, None)["statusCode"] == 400
        
        # 150 age should be invalid
        eventTemplate = {"age": 150, "state": "MH", "income": 50000, "occupation": "Farmer"}
        assert recommend_schemes_handler(make_event(eventTemplate), None)["statusCode"] == 400

    def test_negative_income(self):
        event = make_event({"age": 30, "state": "MH", "income": -100, "occupation": "Farmer"})
        res = recommend_schemes_handler(event, None)
        assert res["statusCode"] == 400

    @patch("lambdas.recommend_schemes.handler.invoke_claude")
    def test_claude_malformed_json_fallback(self, mock_invoke):
        # Claude returns conversational text that cannot be parsed
        mock_invoke.return_value = "Here are your schemes: [ { not a valid json at all..."
        
        event = make_event({"age": 30, "state": "MH", "income": 50000, "occupation": "Farmer"})
        res = recommend_schemes_handler(event, None)
        assert res["statusCode"] == 200
        
        schemes = json.loads(res["body"])["data"]["schemes"]
        # Fallback should yield precisely 3 top fallback schemes
        assert len(schemes) == 3
        
    @patch("lambdas.recommend_schemes.handler.invoke_claude")
    def test_claude_exception_fallback(self, mock_invoke):
        # Network/Rate limit error
        mock_invoke.side_effect = Exception("Bedrock error")
        
        event = make_event({"age": 30, "state": "MH", "income": 50000, "occupation": "Farmer"})
        res = recommend_schemes_handler(event, None)
        assert res["statusCode"] == 200
        
        schemes = json.loads(res["body"])["data"]["schemes"]
        assert len(schemes) == 3


class TestRagQueryHandler:
    @patch("lambdas.rag_query.handler.get_cached_response")
    @patch("lambdas.rag_query.handler.retrieve_relevant_chunks")
    @patch("lambdas.rag_query.handler.generate_general_answer")
    @patch("lambdas.rag_query.handler.put_cached_response")
    @patch("lambdas.rag_query.handler.append_conversation_event")
    def test_valid_query_cache_miss(
        self, mock_append, mock_cache_put, mock_generate, mock_retrieve, mock_cache_get
    ):
        mock_cache_get.return_value = None
        mock_retrieve.return_value = []
        mock_generate.return_value = "This is a detailed generated answer."
        
        event = make_event({"query": "What is PMAY?"})
        res = rag_query_handler(event, None)
        
        assert res["statusCode"] == 200
        data = json.loads(res["body"])["data"]
        assert data["answer"] == "This is a detailed generated answer."
        
        # Verify retrieve & generate were called
        mock_retrieve.assert_called_once()
        mock_generate.assert_called_once()

    def test_empty_query(self):
        event = make_event({"query": ""})
        res = rag_query_handler(event, None)
        assert res["statusCode"] == 400

    def test_query_too_long(self):
        event = make_event({"query": "A" * 2001})
        res = rag_query_handler(event, None)
        assert res["statusCode"] == 400

    def test_invalid_language(self):
        event = make_event({"query": "Hello", "language": "fr"})
        res = rag_query_handler(event, None)
        assert res["statusCode"] == 400

    @patch("lambdas.rag_query.handler.get_cached_response")
    @patch("lambdas.rag_query.handler.append_conversation_event")
    def test_cache_hit(self, mock_append, mock_cache_get):
        mock_cache_get.return_value = {
            "answer": "Cached answer",
            "sources": [],
            "confidence": 100.0
        }
        event = make_event({"query": "Cached query"})
        res = rag_query_handler(event, None)
        
        assert res["statusCode"] == 200
        data = json.loads(res["body"])["data"]
        assert data["answer"] == "Cached answer"
        
        # Ensure we appended cache hit to db
        kwargs = mock_append.call_args.kwargs
        assert kwargs["extra"]["cached"] is True


class TestTextUtils:
    def test_parse_llm_json_plain(self):
        raw = '{"key": "value"}'
        res = parse_llm_json(raw)
        assert res == {"key": "value"}

    def test_parse_llm_json_json_fences(self):
        raw = '```json\n{"key": "value"}\n```'
        res = parse_llm_json(raw)
        assert res == {"key": "value"}

    def test_parse_llm_json_plain_fences(self):
        raw = '```\n[1, 2, 3]\n```'
        res = parse_llm_json(raw)
        assert res == [1, 2, 3]

    def test_parse_llm_json_invalid(self):
        raw = "This is simply not JSON"
        res = parse_llm_json(raw, fallback="FALLBACK")
        assert res == "FALLBACK"

    def test_parse_llm_json_empty(self):
        res = parse_llm_json("   ", fallback=["empty"])
        assert res == ["empty"]
