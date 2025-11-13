# ML Memory Trainer for ChatGPT Conversations

An intelligent ML-based system for building a "permanent memory" from your ChatGPT conversation history. Uses RAG (Retrieval-Augmented Generation) with vector embeddings for privacy-preserving local execution.

## Features

- **Privacy-First Design**: Fully local execution, no cloud dependencies
- **Incremental Training**: Daily fine-tuning with only new/updated conversations
- **Smart Retrieval**: Semantic search using vector embeddings (FAISS)
- **Prompt Assistance**: Context-aware suggestions from past conversations
- **Thread Detection**: Identifies open threads and unanswered questions
- **Action Item Tracking**: Finds pending tasks and follow-ups
- **Flexible Architecture**: Multiple embedding strategies and model options

## Architecture

The system uses a RAG-based approach:
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2 by default)
- **Vector Store**: FAISS for efficient semantic search
- **Fallbacks**: scikit-learn TF-IDF and numpy-based similarity if dependencies unavailable
- **Tracking**: SQLite database for incremental training state

## Installation

### Prerequisites

Python 3.10+ required.

### Basic Installation

```bash
# Install core dependencies
pip install sentence-transformers faiss-cpu scikit-learn numpy

# Or install from the parent repository in editable mode
cd /path/to/Modular_Utilities
pip install -e .
```

### Optional Dependencies

For GPU acceleration:
```bash
pip install faiss-gpu  # instead of faiss-cpu
```

## Quick Start

### 1. Prepare Your Data

First, extract your ChatGPT conversations:

```bash
cd GPT-Export-Parser
python extract_messages.py
```

This creates `data/pruned.json` from your `conversations.json` export.

### 2. Initial Training

Train the model on your entire conversation history:

```bash
python ml_trainer/cli.py train --data-dir data --model-dir ml_model
```

This will:
- Load all conversations from `pruned.json`
- Generate embeddings for each conversation
- Build a vector database for semantic search
- Save the trained model to `ml_model/`

### 3. Query Your Memory

Search your conversation history:

```bash
python ml_trainer/cli.py query "Python debugging" --show-text
```

### 4. Get Prompt Assistance

Get context-aware suggestions:

```bash
python ml_trainer/cli.py prompt-assist "How do I handle async errors?" --enhanced
```

### 5. Check Open Threads

Find unresolved conversations:

```bash
python ml_trainer/cli.py threads --summary
```

## Usage Guide

### Training Commands

**Initial Training:**
```bash
python ml_trainer/cli.py train \
  --data-dir data \
  --model-dir ml_model \
  --embedding-model all-MiniLM-L6-v2 \
  --strategy full
```

**Incremental Training (Daily Updates):**
```bash
python ml_trainer/cli.py train --incremental
```

**Training Strategies:**
- `full`: Single embedding per conversation (default, memory efficient)
- `messages`: Separate embedding per message (more granular)
- `chunks`: Chunked embeddings for very long conversations

### Query Commands

**Basic Query:**
```bash
python ml_trainer/cli.py query "machine learning" --num-results 5
```

**Query with Scores:**
```bash
python ml_trainer/cli.py query "async programming" --show-scores --show-text
```

### Prompt Assistance

**Get Context Suggestions:**
```bash
python ml_trainer/cli.py prompt-assist "How do I optimize database queries?"
```

**Enhanced Prompt with Context:**
```bash
python ml_trainer/cli.py prompt-assist "debugging React components" --enhanced
```

This prepends relevant historical context to your prompt.

### Thread Detection

**Summary View:**
```bash
python ml_trainer/cli.py threads --summary --days 30
```

**Detailed Open Threads:**
```bash
python ml_trainer/cli.py threads --days 14 --limit 20
```

### Status

**Check Training Status:**
```bash
python ml_trainer/cli.py status
```

Shows:
- Number of trained conversations
- Training runs and checkpoints
- Data statistics
- Model size

## Python API

### Training

```python
from ml_trainer.trainer import MLMemoryTrainer

trainer = MLMemoryTrainer(
    data_dir='data',
    model_dir='ml_model',
    embedding_strategy='full'
)

# Initial training
metrics = trainer.train_initial()

# Incremental training
metrics = trainer.train_incremental()
```

### Querying

```python
from ml_trainer.embeddings import EmbeddingGenerator
from ml_trainer.vector_store import VectorStore
from ml_trainer.retrieval import ConversationRetriever

# Load model
embedding_gen = EmbeddingGenerator()
vector_store = VectorStore(dimension=384)
vector_store.load('ml_model/vector_store')

retriever = ConversationRetriever(vector_store, embedding_gen)

# Search
results = retriever.retrieve("Python async", k=5, return_scores=True)

for result in results:
    print(result['title'], result['similarity_score'])
```

### Prompt Building

```python
from ml_trainer.prompt_builder import PromptBuilder

prompt_builder = PromptBuilder(retriever)

# Get suggestions
suggestions = prompt_builder.suggest_context(
    "How do I debug memory leaks?",
    k=3
)

# Build enhanced prompt
enhanced = prompt_builder.build_enhanced_prompt(
    "Explain async/await",
    k=2,
    format_style='detailed'
)
```

### Thread Detection

```python
from ml_trainer.data_loader import DataLoader
from ml_trainer.thread_detector import ThreadDetector

loader = DataLoader('data')
conversations = loader.load_all_conversations()

detector = ThreadDetector()

# Get summary
summary = detector.get_thread_summary(conversations, days_threshold=30)

# Find open threads
open_threads = detector.detect_open_threads(conversations)

# Find unanswered questions
unanswered = detector.detect_unanswered_questions(conversations)
```

## Configuration

### Model Selection

Choose different embedding models:

```bash
# Smaller, faster model
python ml_trainer/cli.py train --embedding-model paraphrase-MiniLM-L3-v2

# Larger, more accurate model
python ml_trainer/cli.py train --embedding-model all-mpnet-base-v2
```

### Embedding Strategies

- **full** (default): Best for general retrieval, memory efficient
- **messages**: Better for finding specific message content
- **chunks**: Best for very long conversations (>1000 words)

### Storage

Default locations:
- Data: `./data/` (pruned.json, metadata.db)
- Model: `./ml_model/` (vector_store, config.json, training.db)
- Cache: `./ml_model/cache/` (embedding cache)

## Advanced Features

### Date-Based Queries

```python
results = retriever.retrieve_by_date_range(
    "machine learning",
    start_date="2024-01-01",
    end_date="2024-06-30"
)
```

### Topic-Based Retrieval

```python
results = retriever.retrieve_by_topic("React hooks", k=5)
```

### Similar Conversations

```python
similar = retriever.retrieve_similar_conversations(
    reference_conv_id="abc123",
    k=3,
    exclude_self=True
)
```

### Multi-Query Retrieval

```python
results = retriever.multi_query_retrieve(
    queries=["async errors", "promise handling", "try-catch"],
    k_per_query=2,
    deduplicate=True
)
```

## Architecture Decisions

### Why RAG?

- **Privacy**: No data leaves your machine
- **Incremental**: Easy to update with new conversations
- **Efficient**: Fast retrieval with FAISS
- **Extensible**: Can add LLM generation later

### Why sentence-transformers?

- **Quality**: State-of-the-art semantic embeddings
- **Speed**: Fast inference on CPU
- **Lightweight**: Small models (90MB for all-MiniLM-L6-v2)
- **Local**: Runs entirely offline

### Fallback Strategy

If sentence-transformers unavailable:
1. Falls back to scikit-learn TF-IDF
2. Falls back to numpy cosine similarity
3. Graceful degradation throughout

## Performance

### Benchmarks (on i5 CPU)

- Initial training: ~100 conversations/min
- Incremental training: ~200 conversations/min
- Query latency: <50ms for k=5
- Memory usage: ~100MB + (1KB * num_conversations)

### Scaling

- Tested with 1000+ conversations
- FAISS supports millions of vectors
- For >10K conversations, consider IVF or HNSW index

## Troubleshooting

### Import Errors

If you get import errors:
```bash
pip install sentence-transformers faiss-cpu scikit-learn
```

### Memory Issues

For large datasets:
```bash
# Use chunks strategy
python ml_trainer/cli.py train --strategy chunks

# Disable cache
python ml_trainer/cli.py train --no-cache
```

### Slow Training

```bash
# Use smaller model
python ml_trainer/cli.py train --embedding-model paraphrase-MiniLM-L3-v2

# Enable quiet mode
python ml_trainer/cli.py train --quiet
```

## Future Enhancements

- [ ] Integration with local LLMs (Llama, Mistral)
- [ ] Web UI for visualization
- [ ] Export to various formats
- [ ] Conversation clustering
- [ ] Topic modeling
- [ ] Sentiment analysis over time
- [ ] Automatic summarization

## Security & Privacy

- ✅ All processing happens locally
- ✅ No network requests for inference
- ✅ No data sent to external services
- ✅ Models can be downloaded once and cached
- ✅ SQLite databases are local-only

## License

Part of the Modular Utilities project. See parent repository for license.

## Contributing

Contributions welcome! This module follows the Apex Modular Organization Standard (AMOS):
- Files limited to 500 lines (enforced via modularization)
- Clear separation of concerns
- Comprehensive documentation
- Type hints and error handling

## Support

For issues or questions:
1. Check this README
2. Review code documentation
3. Open an issue in the parent repository
