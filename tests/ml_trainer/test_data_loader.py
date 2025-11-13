"""Tests for data_loader module."""

import sys
import os
from pathlib import Path
# Add GPT-Export-Parser to path before importing
test_dir = Path(__file__).parent.resolve()
gpt_parser_path = test_dir.parent.parent / 'GPT-Export-Parser'
sys.path.insert(0, str(gpt_parser_path))

import pytest
import json
import tempfile
import shutil
from datetime import datetime

from ml_trainer.data_loader import DataLoader, ConversationData


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory with test data."""
    temp_dir = tempfile.mkdtemp()
    
    # Create mock pruned.json
    mock_data = {
        "January_2024": [
            {
                "id": "conv1",
                "title": "Test Conversation 1",
                "create_time": "2024-01-01 10:00:00",
                "update_time": "2024-01-01 10:30:00",
                "messages": [
                    {"author": "user", "text": "Hello"},
                    {"author": "ChatGPT", "text": "Hi there!"}
                ]
            },
            {
                "id": "conv2",
                "title": "Test Conversation 2",
                "create_time": "2024-01-02 10:00:00",
                "update_time": "2024-01-02 11:00:00",
                "messages": [
                    {"author": "user", "text": "How are you?"},
                    {"author": "ChatGPT", "text": "I'm doing well!"}
                ]
            }
        ],
        "February_2024": [
            {
                "id": "conv3",
                "title": "Python Help",
                "create_time": "2024-02-01 10:00:00",
                "update_time": "2024-02-01 10:30:00",
                "messages": [
                    {"author": "user", "text": "Help with Python"},
                    {"author": "ChatGPT", "text": "Sure, what do you need?"}
                ]
            }
        ]
    }
    
    pruned_path = os.path.join(temp_dir, 'pruned.json')
    with open(pruned_path, 'w') as f:
        json.dump(mock_data, f)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


def test_conversation_data():
    """Test ConversationData class."""
    messages = [
        {"author": "user", "text": "Hello"},
        {"author": "ChatGPT", "text": "Hi!"}
    ]
    
    conv = ConversationData(
        conv_id="test1",
        title="Test",
        create_time="2024-01-01 10:00:00",
        update_time="2024-01-01 10:30:00",
        messages=messages
    )
    
    assert conv.id == "test1"
    assert conv.title == "Test"
    assert len(conv.messages) == 2
    
    # Test get_full_text
    full_text = conv.get_full_text()
    assert "Hello" in full_text
    assert "Hi!" in full_text
    
    # Test get_user_messages
    user_msgs = conv.get_user_messages()
    assert len(user_msgs) == 1
    assert user_msgs[0] == "Hello"
    
    # Test get_assistant_messages
    assistant_msgs = conv.get_assistant_messages()
    assert len(assistant_msgs) == 1
    assert assistant_msgs[0] == "Hi!"
    
    # Test to_dict
    conv_dict = conv.to_dict()
    assert conv_dict['id'] == "test1"
    assert conv_dict['messages'] == messages


def test_data_loader_initialization(temp_data_dir):
    """Test DataLoader initialization."""
    loader = DataLoader(temp_data_dir)
    assert loader.data_dir == temp_data_dir
    assert loader.pruned_json_path == os.path.join(temp_data_dir, 'pruned.json')


def test_load_all_conversations(temp_data_dir):
    """Test loading all conversations."""
    loader = DataLoader(temp_data_dir)
    conversations = loader.load_all_conversations()
    
    assert len(conversations) == 3
    assert all(isinstance(c, ConversationData) for c in conversations)
    
    # Check IDs
    ids = [c.id for c in conversations]
    assert "conv1" in ids
    assert "conv2" in ids
    assert "conv3" in ids


def test_get_conversation_by_id(temp_data_dir):
    """Test getting conversation by ID."""
    loader = DataLoader(temp_data_dir)
    
    conv = loader.get_conversation_by_id("conv1")
    assert conv is not None
    assert conv.id == "conv1"
    assert conv.title == "Test Conversation 1"
    
    # Non-existent ID
    conv = loader.get_conversation_by_id("nonexistent")
    assert conv is None


def test_get_stats(temp_data_dir):
    """Test getting statistics."""
    loader = DataLoader(temp_data_dir)
    stats = loader.get_stats()
    
    assert stats['total_conversations'] == 3
    assert stats['total_messages'] == 6  # 2 messages per conversation
    assert stats['avg_messages_per_conversation'] == 2.0
    assert stats['date_range'] is not None
    assert stats['date_range']['earliest'] == '2024-01-01'
    assert stats['date_range']['latest'] == '2024-02-01'


def test_get_conversations_since(temp_data_dir):
    """Test filtering conversations by date."""
    loader = DataLoader(temp_data_dir)
    
    # Get conversations since Feb 1
    convs = loader.get_conversations_since('2024-02-01')
    assert len(convs) == 1
    assert convs[0].id == "conv3"
    
    # Get all conversations
    convs = loader.get_conversations_since('2024-01-01')
    assert len(convs) == 3


def test_missing_pruned_json():
    """Test error handling when pruned.json is missing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        loader = DataLoader(temp_dir)
        
        with pytest.raises(FileNotFoundError):
            loader.load_all_conversations()
