"""
Command-Line Interface for ML Memory Trainer

Provides commands for training, querying, and managing the ML memory model.
"""

import argparse
import logging
import sys
import os
import json
from pathlib import Path


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='[%(levelname)s] %(message)s'
    )


def cmd_train(args):
    """Handle train command."""
    from ml_trainer.trainer import MLMemoryTrainer
    
    setup_logging(args.verbose)
    
    trainer = MLMemoryTrainer(
        data_dir=args.data_dir,
        model_dir=args.model_dir,
        embedding_model=args.embedding_model,
        embedding_strategy=args.strategy,
        use_cache=not args.no_cache
    )
    
    if args.incremental:
        print("Running incremental training...")
        metrics = trainer.train_incremental(show_progress=not args.quiet)
    else:
        print("Running initial training...")
        max_conv = args.max_conversations if hasattr(args, 'max_conversations') else None
        metrics = trainer.train_initial(
            max_conversations=max_conv,
            show_progress=not args.quiet
        )
    
    print("\n=== Training Complete ===")
    print(f"Conversations processed: {metrics.get('num_processed', 0)}")
    print(f"Total embeddings: {metrics.get('total_embeddings', 0)}")
    print(f"Vector store size: {metrics.get('vector_store_size', 0)}")
    
    if args.incremental:
        print(f"New conversations: {metrics.get('num_new', 0)}")
        print(f"Updated conversations: {metrics.get('num_updated', 0)}")


def cmd_query(args):
    """Handle query command."""
    from ml_trainer.embeddings import EmbeddingGenerator
    from ml_trainer.vector_store import VectorStore
    from ml_trainer.retrieval import ConversationRetriever
    
    setup_logging(args.verbose)
    
    # Load model
    config_path = os.path.join(args.model_dir, 'config.json')
    if not os.path.exists(config_path):
        print("Error: No trained model found. Run training first.")
        return 1
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Initialize components
    embedding_gen = EmbeddingGenerator(
        model_name=config['embedding_model']
    )
    
    vector_store = VectorStore(dimension=config['embedding_dimension'])
    vector_store_path = os.path.join(args.model_dir, 'vector_store')
    vector_store.load(vector_store_path)
    
    retriever = ConversationRetriever(vector_store, embedding_gen)
    
    # Execute query
    print(f"\nQuery: {args.query}")
    print("=" * 60)
    
    results = retriever.retrieve(
        args.query,
        k=args.num_results,
        return_scores=True
    )
    
    if not results:
        print("No results found.")
        return
    
    for i, result in enumerate(results, 1):
        print(f"\n[Result {i}]")
        print(f"Title: {result.get('title', 'Untitled')}")
        print(f"Date: {result.get('update_time', 'Unknown')}")
        if args.show_scores:
            print(f"Similarity: {result.get('similarity_score', 0.0):.3f}")
        
        if args.show_text:
            text = result.get('text', '')
            print(f"\nText preview:\n{text[:300]}{'...' if len(text) > 300 else ''}")
        print("-" * 60)


def cmd_prompt_assist(args):
    """Handle prompt-assist command."""
    from ml_trainer.embeddings import EmbeddingGenerator
    from ml_trainer.vector_store import VectorStore
    from ml_trainer.retrieval import ConversationRetriever
    from ml_trainer.prompt_builder import PromptBuilder
    
    setup_logging(args.verbose)
    
    # Load model components
    config_path = os.path.join(args.model_dir, 'config.json')
    if not os.path.exists(config_path):
        print("Error: No trained model found. Run training first.")
        return 1
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    embedding_gen = EmbeddingGenerator(model_name=config['embedding_model'])
    vector_store = VectorStore(dimension=config['embedding_dimension'])
    vector_store.load(os.path.join(args.model_dir, 'vector_store'))
    
    retriever = ConversationRetriever(vector_store, embedding_gen)
    prompt_builder = PromptBuilder(retriever)
    
    # Get suggestions
    print(f"\nAnalyzing prompt: {args.prompt}")
    print("=" * 60)
    
    suggestions = prompt_builder.suggest_context(
        args.prompt,
        k=args.num_results,
        include_snippets=True
    )
    
    print(f"\nFound {suggestions['num_results']} relevant conversations:\n")
    
    for i, conv in enumerate(suggestions['relevant_conversations'], 1):
        print(f"{i}. {conv['title']} ({conv['date']})")
        if 'snippet' in conv:
            print(f"   {conv['snippet']}\n")
    
    if suggestions['suggested_topics']:
        print(f"\nCommon topics: {', '.join(suggestions['suggested_topics'])}")
    
    if suggestions['common_patterns']:
        print(f"Patterns: {', '.join(suggestions['common_patterns'])}")
    
    if args.enhanced:
        print("\n" + "=" * 60)
        print("Enhanced prompt with context:")
        print("=" * 60)
        enhanced = prompt_builder.build_enhanced_prompt(
            args.prompt,
            k=3,
            format_style='detailed'
        )
        print(enhanced)


def cmd_threads(args):
    """Handle threads command."""
    from ml_trainer.data_loader import DataLoader
    from ml_trainer.thread_detector import ThreadDetector
    
    setup_logging(args.verbose)
    
    # Load conversations
    data_loader = DataLoader(args.data_dir)
    conversations = data_loader.load_all_conversations()
    
    detector = ThreadDetector()
    
    print(f"\nAnalyzing conversations for open threads...")
    print("=" * 60)
    
    if args.summary:
        summary = detector.get_thread_summary(
            conversations,
            days_threshold=args.days
        )
        
        print(f"\nThread Summary (last {args.days} days):")
        print(f"Total conversations: {summary['total_recent_conversations']}")
        print(f"Open threads: {summary['open_threads_count']}")
        print(f"Unanswered questions: {summary['unanswered_questions_count']}")
        print(f"Action items: {summary['action_items_count']}")
        
        if summary['top_open_threads']:
            print(f"\nTop Open Threads:")
            for i, thread in enumerate(summary['top_open_threads'], 1):
                print(f"{i}. {thread['title']} (score: {thread['score']:.2f})")
        
        if summary['recent_unanswered']:
            print(f"\nRecent Unanswered Questions:")
            for i, item in enumerate(summary['recent_unanswered'], 1):
                print(f"{i}. {item['title']}")
                print(f"   {item['question'][:100]}...")
    else:
        # Show detailed open threads
        open_threads = detector.detect_open_threads(
            conversations,
            days_threshold=args.days
        )
        
        print(f"\nFound {len(open_threads)} open threads:\n")
        
        for i, thread in enumerate(open_threads[:args.limit], 1):
            print(f"[{i}] {thread['title']}")
            print(f"    Date: {thread['update_time']}")
            print(f"    Score: {thread['score']:.2f}")
            print(f"    Indicators: {', '.join(thread['indicators'])}")
            if thread['last_message']:
                print(f"    Last: {thread['last_message']['text'][:100]}...")
            print()


def cmd_status(args):
    """Handle status command."""
    from ml_trainer.trainer import MLMemoryTrainer
    
    setup_logging(args.verbose)
    
    trainer = MLMemoryTrainer(
        data_dir=args.data_dir,
        model_dir=args.model_dir
    )
    
    status = trainer.get_training_status()
    
    print("\n=== ML Memory Trainer Status ===\n")
    
    # Training stats
    training_stats = status['training_stats']
    print("Training Statistics:")
    print(f"  Trained conversations: {training_stats['num_trained_conversations']}")
    print(f"  Training runs: {training_stats['num_training_runs']}")
    print(f"  Checkpoints: {training_stats['num_checkpoints']}")
    
    if training_stats['latest_run']:
        latest = training_stats['latest_run']
        print(f"\n  Latest run:")
        print(f"    Type: {latest['run_type']}")
        print(f"    Date: {latest['started_at']}")
        print(f"    Status: {latest['status']}")
    
    # Data stats
    data_stats = status['data_stats']
    print(f"\nData Statistics:")
    print(f"  Total conversations: {data_stats['total_conversations']}")
    print(f"  Total messages: {data_stats['total_messages']}")
    print(f"  Avg messages/conv: {data_stats['avg_messages_per_conversation']:.1f}")
    
    if data_stats['date_range']:
        dr = data_stats['date_range']
        print(f"  Date range: {dr['earliest']} to {dr['latest']}")
    
    # Model stats
    print(f"\nModel Statistics:")
    print(f"  Vector store size: {status['model_size']} embeddings")
    
    if status['latest_checkpoint']:
        ckpt = status['latest_checkpoint']
        print(f"  Latest checkpoint: {ckpt['checkpoint_id']}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='ML Memory Trainer for ChatGPT conversations',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train the model')
    train_parser.add_argument(
        '--data-dir',
        default='./data',
        help='Directory containing pruned.json'
    )
    train_parser.add_argument(
        '--model-dir',
        default='./ml_model',
        help='Directory to save model'
    )
    train_parser.add_argument(
        '--incremental',
        action='store_true',
        help='Incremental training (only new/updated conversations)'
    )
    train_parser.add_argument(
        '--embedding-model',
        default='all-MiniLM-L6-v2',
        help='Embedding model name'
    )
    train_parser.add_argument(
        '--strategy',
        choices=['full', 'messages', 'chunks'],
        default='full',
        help='Embedding strategy'
    )
    train_parser.add_argument('--no-cache', action='store_true', help='Disable cache')
    train_parser.add_argument('--quiet', action='store_true', help='Minimal output')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Query the model')
    query_parser.add_argument('query', help='Query text')
    query_parser.add_argument('--model-dir', default='./ml_model', help='Model directory')
    query_parser.add_argument('--num-results', type=int, default=5, help='Number of results')
    query_parser.add_argument('--show-text', action='store_true', help='Show text previews')
    query_parser.add_argument('--show-scores', action='store_true', help='Show similarity scores')
    
    # Prompt assist command
    prompt_parser = subparsers.add_parser('prompt-assist', help='Get prompt suggestions')
    prompt_parser.add_argument('prompt', help='Prompt to analyze')
    prompt_parser.add_argument('--model-dir', default='./ml_model', help='Model directory')
    prompt_parser.add_argument('--num-results', type=int, default=3, help='Number of results')
    prompt_parser.add_argument('--enhanced', action='store_true', help='Show enhanced prompt')
    
    # Threads command
    threads_parser = subparsers.add_parser('threads', help='Detect open threads')
    threads_parser.add_argument('--data-dir', default='./data', help='Data directory')
    threads_parser.add_argument('--days', type=int, default=30, help='Days to analyze')
    threads_parser.add_argument('--limit', type=int, default=10, help='Max results')
    threads_parser.add_argument('--summary', action='store_true', help='Show summary only')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show training status')
    status_parser.add_argument('--data-dir', default='./data', help='Data directory')
    status_parser.add_argument('--model-dir', default='./ml_model', help='Model directory')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to command handler
    if args.command == 'train':
        return cmd_train(args)
    elif args.command == 'query':
        return cmd_query(args)
    elif args.command == 'prompt-assist':
        return cmd_prompt_assist(args)
    elif args.command == 'threads':
        return cmd_threads(args)
    elif args.command == 'status':
        return cmd_status(args)
    
    return 0


if __name__ == '__main__':
    # Add parent directory to path to import ml_trainer modules
    sys.path.insert(0, str(Path(__file__).parent.parent))
    sys.exit(main())
