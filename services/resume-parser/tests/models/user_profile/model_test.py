from unittest.mock import MagicMock
from models.user_profile.model import about_extract

# Sample CV text for testing
mock_resume_text = """
John Doe
123 Main St
Anytown, USA
(123) 456-7890
"""
mock_api_response = '["John", "Doe", "123 Main St", "Anytown", "US", "(123) 456-7890", "US", "I am a healthcare professional with extensive experience in the field."]'


def test_about_extract_success():
    """Test about_extract function with a successful response from OpenAI API."""

    # Create a mock OpenAI client
    mock_openai_client = MagicMock()
    mock_openai_client.chat.completions.create.return_value.choices = [MagicMock()]
    mock_openai_client.chat.completions.create.return_value.choices[
        0
    ].message.content = mock_api_response

    # Call the function with the mocked client
    result = about_extract(mock_resume_text, mock_openai_client)

    # Assert the expected output
    expected_result = [
        "John",
        "Doe",
        "123 Main St",
        "Anytown",
        "US",
        "(123) 456-7890",
        "US",
        "I am a healthcare professional with extensive experience in the field.",
    ]
    assert result == expected_result


def test_about_extract_json_decode_error():
    """Test about_extract function with a JSON decode error."""

    # Create a mock OpenAI client that returns invalid JSON
    mock_openai_client = MagicMock()
    mock_openai_client.chat.completions.create.return_value.choices = [MagicMock()]
    mock_openai_client.chat.completions.create.return_value.choices[
        0
    ].message.content = "invalid json"

    # Call the function with the mocked client
    result = about_extract(mock_resume_text, mock_openai_client)

    # Assert the output should be None due to JSON decode error
    assert result == []


def test_about_extract_unexpected_error():
    """Test about_extract function with an unexpected error."""

    # Create a mock OpenAI client that raises an exception
    mock_openai_client = MagicMock()
    mock_openai_client.chat.completions.create.side_effect = Exception(
        "Unexpected error"
    )

    # Call the function with the mocked client
    result = about_extract(mock_resume_text, mock_openai_client)

    # Assert the output should be None due to unexpected error
    assert result == []
