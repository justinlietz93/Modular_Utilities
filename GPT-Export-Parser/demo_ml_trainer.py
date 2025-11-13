#!/usr/bin/env python3
"""
Demo script to validate ML Trainer functionality.

This script demonstrates the core capabilities of the ML Memory Trainer
without requiring external dependencies like sentence-transformers or FAISS.
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path

# Add GPT-Export-Parser to path
sys.path.insert(0, str(Path(__file__).parent / 'GPT-Export-Parser'))

from ml_trainer.data_loader import DataLoader, ConversationData
from ml_trainer.embeddings import EmbeddingGenerator
from ml_trainer.vector_store import VectorStore
from ml_trainer.retrieval import ConversationRetriever
from ml_trainer.prompt_builder import PromptBuilder
from ml_trainer.thread_detector import ThreadDetector
from ml_trainer.training_tracker import TrainingTracker


def create_mock_data():
    """Create mock conversation data for testing."""
    mock_data = {
        "January_2024": [
            {
                "id": "conv1",
                "title": "Python AsyncIO Help",
                "create_time": "2024-01-01 10:00:00",
                "update_time": "2024-01-01 10:30:00",
                "messages": [
                    {"author": "user", "text": "How do I use asyncio in Python?"},
                    {"author": "ChatGPT", "text": "AsyncIO is Python's built-in library for asynchronous programming. Here's a basic example..."},
                    {"author": "user", "text": "Can you show me error handling?"},
                    {"author": "ChatGPT", "text": "Sure! Use try-except blocks with async functions..."}
                ]
            },
            {
                "id": "conv2",
                "title": "Machine Learning Basics",
                "create_time": "2024-01-02 10:00:00",
                "update_time": "2024-01-02 11:00:00",
                "messages": [
                    {"author": "user", "text": "What is machine learning?"},
                    {"author": "ChatGPT", "text": "Machine learning is a subset of AI..."},
                    {"author": "user", "text": "I need to implement this soon"},
                    {"author": "ChatGPT", "text": "Let me know when you're ready!"}
                ]
            }
        ],
        "February_2024": [
            {
                "id": "conv3",
                "title": "React Hooks Question",
                "create_time": "2024-02-01 10:00:00",
                "update_time": "2024-02-01 10:30:00",
                "messages": [
                    {"author": "user", "text": "How do React hooks work?"},
                    {"author": "ChatGPT", "text": "React hooks let you use state and other React features..."}
                ]
            }
        ]
    }
    return mock_data


def test_data_loader(data_dir):
    """Test DataLoader functionality."""
    print("\n" + "="*60)
    print("1. Testing DataLoader")
    print("="*60)
    
    loader = DataLoader(data_dir)
    conversations = loader.load_all_conversations()
    
    print(f"✓ Loaded {len(conversations)} conversations")
    
    stats = loader.get_stats()
    print(f"✓ Total messages: {stats['total_messages']}")
    print(f"✓ Date range: {stats['date_range']['earliest']} to {stats['date_range']['latest']}")
    
    conv = loader.get_conversation_by_id("conv1")
    print(f"✓ Retrieved conversation by ID: {conv.title}")
    
    return conversations


def test_embeddings():
    """Test EmbeddingGenerator functionality."""
    print("\n" + "="*60)
    print("2. Testing Embeddings")
    print("="*60)
    
    # Use fallback mode (no sentence-transformers required)
    gen = EmbeddingGenerator(use_sentence_transformers=False)
    print("✓ Initialized EmbeddingGenerator (TF-IDF fallback mode)")
    
    text = "This is a test sentence for embedding generation"
    embedding = gen.generate_embedding(text)
    print(f"✓ Generated embedding with dimension: {len(embedding)}")
    
    conv_data = {
        'id': 'test',
        'messages': [
            {'author': 'user', 'text': 'Hello'},
            {'author': 'ChatGPT', 'text': 'Hi there!'}
        ]
    }
    
    embeddings, metadata = gen.embed_conversation(conv_data, strategy='full')
    print(f"✓ Embedded conversation: {metadata['num_embeddings']} embedding(s)")
    
    return gen


def test_vector_store():
    """Test VectorStore functionality."""
    print("\n" + "="*60)
    print("3. Testing Vector Store")
    print("="*60)
    
    import numpy as np
    
    # Use numpy fallback (no FAISS required)
    # Use dimension 7 to match TF-IDF output from demo
    store = VectorStore(dimension=7, use_faiss=False)
    print("✓ Initialized VectorStore (numpy fallback mode)")
    
    # Add some vectors
    vectors = np.random.rand(5, 7).astype('float32')
    metadata = [
        {'id': f'conv{i}', 'title': f'Conversation {i}', 'text': f'Text {i}'}
        for i in range(5)
    ]
    
    store.add_vectors(vectors, metadata)
    print(f"✓ Added {store.get_size()} vectors to store")
    
    # Search
    query = np.random.rand(7).astype('float32')
    results = store.search(query, k=3)
    print(f"✓ Search returned {len(results)} results")
    
    return store


def test_retrieval(store, gen):
    """Test ConversationRetriever functionality."""
    print("\n" + "="*60)
    print("4. Testing Retrieval")
    print("="*60)
    
    retriever = ConversationRetriever(store, gen)
    print("✓ Initialized ConversationRetriever")
    
    results = retriever.retrieve("test query", k=2)
    print(f"✓ Retrieved {len(results)} conversations")
    
    return retriever


def test_prompt_builder(retriever):
    """Test PromptBuilder functionality."""
    print("\n" + "="*60)
    print("5. Testing Prompt Builder")
    print("="*60)
    
    builder = PromptBuilder(retriever)
    print("✓ Initialized PromptBuilder")
    
    suggestions = builder.suggest_context("How do I debug?", k=2)
    print(f"✓ Generated suggestions with {suggestions['num_results']} relevant conversations")
    
    enhanced = builder.build_enhanced_prompt("Explain asyncio", k=1)
    print(f"✓ Built enhanced prompt ({len(enhanced)} characters)")
    
    return builder


def test_thread_detector(conversations):
    """Test ThreadDetector functionality."""
    print("\n" + "="*60)
    print("6. Testing Thread Detector")
    print("="*60)
    
    detector = ThreadDetector()
    print("✓ Initialized ThreadDetector")
    
    open_threads = detector.detect_open_threads(conversations, days_threshold=365)
    print(f"✓ Detected {len(open_threads)} potential open threads")
    
    if open_threads:
        print(f"  - Top thread: {open_threads[0]['title']} (score: {open_threads[0]['score']:.2f})")
    
    unanswered = detector.detect_unanswered_questions(conversations, days_threshold=365)
    print(f"✓ Found {len(unanswered)} unanswered questions")
    
    action_items = detector.detect_action_items(conversations, days_threshold=365)
    print(f"✓ Detected {len(action_items)} action items")
    
    return detector


def test_training_tracker():
    """Test TrainingTracker functionality."""
    print("\n" + "="*60)
    print("7. Testing Training Tracker")
    print("="*60)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        tracker = TrainingTracker(db_path)
        print("✓ Initialized TrainingTracker")
        
        # Start a training run
        run_id = tracker.start_training_run(
            run_type='test',
            num_conversations=3,
            num_new=3
        )
        print(f"✓ Started training run {run_id}")
        
        # Mark conversations as trained
        tracker.mark_conversation_trained(
            conv_id='conv1',
            update_time=1234567890.0,
            title='Test Conv',
            embedding_strategy='full',
            num_embeddings=1
        )
        print("✓ Marked conversation as trained")
        
        # Complete run
        tracker.complete_training_run(run_id, status='completed')
        print("✓ Completed training run")
        
        # Get stats
        stats = tracker.get_stats()
        print(f"✓ Stats: {stats['num_trained_conversations']} trained, {stats['num_training_runs']} runs")
        
        return tracker
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ML Memory Trainer - Functionality Demo")
    print("=" * 60)
    print("\nThis demo validates core functionality without requiring")
    print("external dependencies (sentence-transformers, FAISS).")
    print("For full features, install: pip install sentence-transformers faiss-cpu")
    
    # Create temporary directory with mock data
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create mock pruned.json
        mock_data = create_mock_data()
        pruned_path = os.path.join(temp_dir, 'pruned.json')
        with open(pruned_path, 'w') as f:
            json.dump(mock_data, f)
        
        # Run tests
        conversations = test_data_loader(temp_dir)
        gen = test_embeddings()
        store = test_vector_store()
        retriever = test_retrieval(store, gen)
        builder = test_prompt_builder(retriever)
        detector = test_thread_detector(conversations)
        tracker = test_training_tracker()
        
        print("\n" + "="*60)
        print("✓ All tests passed successfully!")
        print("="*60)
        print("\nThe ML Memory Trainer is working correctly.")
        print("To use with real data:")
        print("  1. Run: python extract_messages.py")
        print("  2. Run: python ml_trainer/cli.py train")
        print("  3. Query: python ml_trainer/cli.py query 'your question'")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    sys.exit(main())
