"""Test endpoint_key stability"""
import pytest
from app.core.idempotency import normalize_endpoint_key


def test_endpoint_key_stability_same_path_different_ids():
    """Test: Same endpoint pattern with different IDs produces same endpoint_key"""
    path1 = "/books/123e4567-e89b-12d3-a456-426614174000/journal-entries/789e4567-e89b-12d3-a456-426614174001/post"
    path2 = "/books/987e6543-e21b-12d3-a456-426614174002/journal-entries/456e7890-e12b-34c5-d678-901234567890/post"
    
    key1 = normalize_endpoint_key("POST", path1)
    key2 = normalize_endpoint_key("POST", path2)
    
    # Should normalize to same pattern (with {id} placeholders)
    assert key1 == key2
    assert "{id}" in key1
    assert "journal-entries" in key1
    assert "post" in key1


def test_endpoint_key_stability_different_methods():
    """Test: Different HTTP methods produce different endpoint_keys"""
    path = "/books/123/journal-entries/456/post"
    
    post_key = normalize_endpoint_key("POST", path)
    get_key = normalize_endpoint_key("GET", path)
    
    assert post_key != get_key
    assert post_key.startswith("POST:")
    assert get_key.startswith("GET:")


def test_endpoint_key_stability_query_params_ignored():
    """Test: Query parameters are ignored in endpoint_key"""
    path1 = "/books/123/journal-entries/456/post?filter=active"
    path2 = "/books/123/journal-entries/456/post?filter=inactive&sort=date"
    
    key1 = normalize_endpoint_key("POST", path1)
    key2 = normalize_endpoint_key("POST", path2)
    
    assert key1 == key2
