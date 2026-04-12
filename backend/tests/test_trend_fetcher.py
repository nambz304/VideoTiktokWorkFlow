import pytest
from unittest.mock import patch, MagicMock
from services.trend_fetcher import TrendFetcher

@pytest.fixture
def fetcher():
    return TrendFetcher(reddit_client_id="fake", reddit_secret="fake", reddit_user_agent="test")

def test_fetch_returns_list(fetcher):
    with patch.object(fetcher, '_fetch_google_trends', return_value=[
        {"topic": "Ngủ đủ giấc", "score": 85, "source": "google_trends"}
    ]):
        with patch.object(fetcher, '_fetch_reddit', return_value=[
            {"topic": "Omega-3 benefits", "score": 70, "source": "reddit"}
        ]):
            results = fetcher.fetch(keywords=["sức khoẻ"], lang="vi", limit=5)
            assert isinstance(results, list)
            assert len(results) <= 5
            assert all("topic" in r for r in results)
            assert all("score" in r for r in results)
            assert all("source" in r for r in results)

def test_fetch_sorted_by_score(fetcher):
    with patch.object(fetcher, '_fetch_google_trends', return_value=[
        {"topic": "A", "score": 40, "source": "google"},
        {"topic": "B", "score": 90, "source": "google"},
    ]):
        with patch.object(fetcher, '_fetch_reddit', return_value=[]):
            results = fetcher.fetch(keywords=["health"], lang="en", limit=5)
            assert results[0]["score"] >= results[-1]["score"]
