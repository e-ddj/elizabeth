import pytest
import json
from unittest.mock import patch, MagicMock
from api.index import app

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'job-matcher'

@patch('api.job_matcher.match.match_job_to_users')
def test_match_job_success(mock_match, client):
    """Test successful job matching."""
    # Mock the matching function
    mock_match.return_value = {
        "job_id": "test-job-123",
        "job_title": "Python Developer",
        "company": "Test Corp",
        "matches": [
            {
                "user_id": "user-1",
                "user_name": "John Doe",
                "user_email": "john@example.com",
                "match_score": 0.85,
                "match_reasons": ["Strong Python skills", "Relevant experience"],
                "skill_matches": ["Python", "Django"],
                "experience_match": True,
                "location_match": True,
                "salary_match": True
            }
        ]
    }
    
    # Make request
    response = client.post('/api/job-matcher/match',
                          json={"job_id": "test-job-123"},
                          content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['job_id'] == "test-job-123"
    assert len(data['matches']) == 1
    assert data['matches'][0]['match_score'] == 0.85

def test_match_job_missing_id(client):
    """Test match request without job_id."""
    response = client.post('/api/job-matcher/match',
                          json={},
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'job_id is required' in data['error']

def test_match_job_no_payload(client):
    """Test match request without payload."""
    response = client.post('/api/job-matcher/match')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

@patch('api.job_matcher.match.match_job_to_users')
def test_match_job_error(mock_match, client):
    """Test error handling in job matching."""
    # Mock function to raise exception
    mock_match.side_effect = Exception("Database connection failed")
    
    response = client.post('/api/job-matcher/match',
                          json={"job_id": "test-job-123"},
                          content_type='application/json')
    
    assert response.status_code == 500
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Failed to match job' in data['error']
    assert 'Database connection failed' in data['details']