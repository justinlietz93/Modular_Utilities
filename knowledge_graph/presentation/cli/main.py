"""CLI entry point for knowledge graph utility."""
import argparse
import sys
from pathlib import Path
from typing import Optional

from ...domain.models import VerbosityLevel
from ...application.graph_service import GraphService, SettingsService
from ...application.ingestion_service import IngestionService
from ...application.query_service import QueryService
from ...application.pruning_service import PruningService


def prompt_yes_no(message: str) -> bool:
    """Prompt user for yes/no response."""
    while True:
        response = input(f"{message} (y/n): ").strip().lower()
        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        print("Please enter 'y' or 'n'.")


def print_if_verbosity(message: str, level: VerbosityLevel, settings_service: SettingsService):
    """Print message if verbosity level allows."""
    if settings_service.should_log(level):
        print(message)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='knowledge-graph',
        description='Knowledge graph utility for organizing and querying conceptual knowledge',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a graph
  knowledge-graph --create --graph-id my-graph
  
  # Ingest content
  knowledge-graph --input research-papers/ --graph-id my-graph
  knowledge-graph --input research-papers/ --graph-id my-graph --recursive
  
  # Query the graph
  knowledge-graph --query "machine learning neural networks" --graph-id my-graph
  knowledge-graph --query "machine learning" --output results.md
  
  # Extract subgraph
  knowledge-graph --query "quantum computing" --subgraph quantum.json --hops 3
  
  # Get metadata
  knowledge-graph --metadata --graph-id my-graph
  knowledge-graph --query "AI" --metadata metrics.md
  
  # Dump graph
  knowledge-graph --dump --graph-id my-graph
  
  # Prune graph
  knowledge-graph --prune --bottom 10
  knowledge-graph --prune --top 25 -Y
  
  # Settings
  knowledge-graph --settings --verbosity high
  knowledge-graph --settings --db off
  
  # Random query
  knowledge-graph --query --random
        """
    )
    
    # Graph operations
    parser.add_argument('--create', action='store_true', help='Create a new graph')
    parser.add_argument('--delete', action='store_true', help='Delete a graph')
    parser.add_argument('--dump', action='store_true', help='Dump graph to file')
    parser.add_argument('--graph-id', type=str, help='Graph identifier')
    
    # Input operations
    parser.add_argument('--input', type=str, help='Input file or directory')
    parser.add_argument('--recursive', '--r', action='store_true', help='Recursively process directories')
    
    # Query operations
    parser.add_argument('--query', nargs='*', help='Query string or --random flag')
    parser.add_argument('--random', action='store_true', help='Perform random query')
    parser.add_argument('--output', type=str, help='Output file for query results')
    
    # Subgraph operations
    parser.add_argument('--subgraph', type=str, help='Extract subgraph to file')
    parser.add_argument('--hops', type=int, default=1, help='Number of hops for subgraph extraction')
    
    # Metadata operations
    parser.add_argument('--metadata', nargs='?', const=True, help='Show or save metadata')
    
    # Pruning operations
    parser.add_argument('--prune', action='store_true', help='Prune graph')
    parser.add_argument('--bottom', type=int, help='Prune bottom percentage')
    parser.add_argument('--top', type=int, help='Prune top percentage')
    
    # Settings operations
    parser.add_argument('--settings', action='store_true', help='Modify settings')
    parser.add_argument('--verbosity', type=str, choices=['off', 'low', 'medium', 'high', 'max'],
                       help='Set verbosity level')
    parser.add_argument('--db', type=str, choices=['on', 'off'], help='Enable/disable query database')
    
    # General options
    parser.add_argument('-Y', dest='auto_yes', action='store_true', help='Automatically answer yes to prompts')
    
    args = parser.parse_args()
    
    # Initialize services
    settings_service = SettingsService()
    graph_service = GraphService()
    ingestion_service = IngestionService()
    query_service = QueryService()
    pruning_service = PruningService()
    
    # Handle settings command
    if args.settings:
        if args.verbosity:
            level = VerbosityLevel(args.verbosity)
            if settings_service.update_verbosity(level):
                print(f"Verbosity set to: {args.verbosity}")
                return 0
            else:
                print("Error updating verbosity")
                return 1
        
        if args.db:
            enabled = args.db == 'on'
            if settings_service.update_database(enabled):
                print(f"Query database: {'enabled' if enabled else 'disabled'}")
                return 0
            else:
                print("Error updating database setting")
                return 1
        
        print("No settings specified. Use --verbosity or --db")
        return 1
    
    # Handle create command
    if args.create:
        if not args.graph_id:
            print("Error: --graph-id is required for --create")
            return 1
        
        if graph_service.create_graph(args.graph_id):
            print_if_verbosity(f"Created graph: {args.graph_id}", VerbosityLevel.LOW, settings_service)
            return 0
        else:
            print(f"Error: Graph '{args.graph_id}' already exists")
            return 1
    
    # Handle delete command
    if args.delete:
        graph_id = args.graph_id
        if graph_id is None:
            graph_id = graph_service.tracker.get_last_graph()
            if graph_id is None:
                print("Error: No graph to delete. Specify --graph-id")
                return 1
        
        # Prompt for confirmation unless -Y is specified
        if not args.auto_yes:
            if not prompt_yes_no(f"Delete graph '{graph_id}'?"):
                print("Deletion canceled")
                return 0
        
        if graph_service.delete_graph(graph_id):
            print_if_verbosity(f"Deleted graph: {graph_id}", VerbosityLevel.LOW, settings_service)
            return 0
        else:
            print(f"Error deleting graph: {graph_id}")
            return 1
    
    # Handle dump command
    if args.dump:
        graph = graph_service.get_graph(args.graph_id)
        if not graph:
            print("Error: Graph not found")
            return 1
        
        output_file = f"{graph.graph_id}_dump.json"
        if graph_service.dump_graph(args.graph_id, output_file):
            print_if_verbosity(f"Graph dumped to: {output_file}", VerbosityLevel.LOW, settings_service)
            return 0
        else:
            print("Error dumping graph")
            return 1
    
    # Handle input command
    if args.input:
        if not args.graph_id:
            # Use last graph
            graph_id = graph_service.tracker.get_last_graph()
            if not graph_id:
                print("Error: No graph specified and no last graph found")
                return 1
        else:
            graph_id = args.graph_id
        
        graph = graph_service.get_graph(graph_id)
        if not graph:
            print(f"Error: Graph '{graph_id}' not found")
            return 1
        
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input path does not exist: {args.input}")
            return 1
        
        count = 0
        if input_path.is_dir():
            count = ingestion_service.ingest_directory(input_path, graph, args.recursive)
        else:
            if ingestion_service.ingest_file(input_path, graph):
                count = 1
        
        if count > 0:
            graph_service.save_graph(graph)
            print_if_verbosity(f"Ingested {count} file(s) into graph '{graph_id}'", 
                             VerbosityLevel.MEDIUM, settings_service)
            
            if settings_service.should_log(VerbosityLevel.HIGH):
                print(f"Total nodes: {len(graph.nodes)}")
                print(f"Total edges: {len(graph.edges)}")
            
            return 0
        else:
            print("No files were ingested")
            return 1
    
    # Handle query command
    if args.query is not None:
        # Determine graph
        graph = graph_service.get_graph(args.graph_id)
        if not graph:
            print("Error: Graph not found")
            return 1
        
        # Check for random query
        is_random = args.random or (isinstance(args.query, list) and '--random' in args.query)
        
        if is_random:
            results = query_service.random_query(graph, log_query=settings_service.settings.database_enabled)
            query_str = "random"
        else:
            # Join query words
            query_str = ' '.join(args.query) if isinstance(args.query, list) else str(args.query)
            results = query_service.query(query_str, graph, log_query=settings_service.settings.database_enabled)
        
        # Save graph after query (to update retrieval counts)
        graph_service.save_graph(graph)
        
        # Handle metadata request
        if args.metadata:
            metadata = query_service.get_metadata(graph, query_str if not is_random else None)
            
            if isinstance(args.metadata, str):
                # Save to file
                query_service.save_metadata_to_file(metadata, args.metadata)
                print_if_verbosity(f"Metadata saved to: {args.metadata}", VerbosityLevel.LOW, settings_service)
            else:
                # Print to terminal
                if settings_service.should_log(VerbosityLevel.LOW):
                    print("\n=== Graph Metadata ===")
                    for key, value in metadata.items():
                        print(f"{key}: {value}")
        
        # Handle subgraph extraction
        if args.subgraph:
            subgraph_data = query_service.extract_subgraph(query_str, graph, args.hops)
            
            if subgraph_data:
                # Add metadata if requested
                if args.metadata and not isinstance(args.metadata, str):
                    metadata = query_service.get_metadata(graph, query_str)
                    subgraph_data["metadata"] = metadata
                
                query_service.save_subgraph_to_file(subgraph_data, args.subgraph)
                print_if_verbosity(f"Subgraph saved to: {args.subgraph}", VerbosityLevel.LOW, settings_service)
            else:
                print("No results found for subgraph extraction")
                return 1
        
        # Handle output
        elif args.output:
            query_service.save_results_to_file(results, args.output)
            print_if_verbosity(f"Results saved to: {args.output}", VerbosityLevel.LOW, settings_service)
        else:
            # Print to terminal
            if settings_service.should_log(VerbosityLevel.MEDIUM):
                print(f"\n=== Query Results ({len(results)} results) ===\n")
                for i, result in enumerate(results[:10], 1):
                    print(f"{i}. (Score: {result.score:.4f})")
                    print(f"   {result.content[:200]}...")
                    if result.source_file and settings_service.should_log(VerbosityLevel.HIGH):
                        print(f"   Source: {result.source_file}")
                    print()
        
        # Show high verbosity metrics
        if settings_service.should_log(VerbosityLevel.HIGH) and not args.metadata:
            metadata = query_service.get_metadata(graph, query_str)
            print("\n=== Query Metrics ===")
            if 'top_result_score' in metadata:
                print(f"Top result score: {metadata['top_result_score']:.4f}")
                print(f"Average score: {metadata['avg_score']:.4f}")
        
        return 0
    
    # Handle prune command
    if args.prune:
        graph = graph_service.get_graph(args.graph_id)
        if not graph:
            print("Error: Graph not found")
            return 1
        
        if not args.auto_yes:
            if not prompt_yes_no(f"Prune graph '{graph.graph_id}'?"):
                print("Pruning canceled")
                return 0
        
        if args.top:
            pruned = pruning_service.prune_top(graph, args.top)
            print_if_verbosity(f"Pruned {pruned} nodes from top {args.top}%", 
                             VerbosityLevel.LOW, settings_service)
        else:
            percentage = args.bottom if args.bottom else 10
            pruned = pruning_service.prune_bottom(graph, percentage)
            print_if_verbosity(f"Pruned {pruned} nodes from bottom {percentage}%", 
                             VerbosityLevel.LOW, settings_service)
        
        graph_service.save_graph(graph)
        
        if settings_service.should_log(VerbosityLevel.MEDIUM):
            print(f"Remaining nodes: {len(graph.nodes)}")
            print(f"Remaining edges: {len(graph.edges)}")
        
        return 0
    
    # Handle standalone metadata command
    if args.metadata is not None:
        graph = graph_service.get_graph(args.graph_id)
        if not graph:
            print("Error: Graph not found")
            return 1
        
        metadata = query_service.get_metadata(graph)
        
        if isinstance(args.metadata, str):
            # Save to file
            query_service.save_metadata_to_file(metadata, args.metadata)
            print_if_verbosity(f"Metadata saved to: {args.metadata}", VerbosityLevel.LOW, settings_service)
        else:
            # Print to terminal
            if settings_service.should_log(VerbosityLevel.LOW):
                print("\n=== Graph Metadata ===")
                for key, value in metadata.items():
                    print(f"{key}: {value}")
        
        return 0
    
    # No command specified
    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())
