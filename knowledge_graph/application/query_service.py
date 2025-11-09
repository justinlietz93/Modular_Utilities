"""Service for querying knowledge graphs."""
import random
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime

from ..domain.models import KnowledgeGraph, QueryResult, GraphNode
from ..infrastructure.similarity import SimilarityService
from ..infrastructure.storage import QueryDatabase


class QueryService:
    """Service for querying knowledge graphs."""
    
    def __init__(self, storage_dir: str = ".knowledge_graphs"):
        """Initialize query service."""
        self.similarity = SimilarityService()
        self.query_db = QueryDatabase(storage_dir)
    
    def query(self, query: str, graph: KnowledgeGraph, limit: int = 10,
              log_query: bool = True) -> List[QueryResult]:
        """Query the graph for relevant nodes."""
        if not graph.nodes:
            return []
        
        nodes_list = list(graph.nodes.values())
        results = self.similarity.rank_nodes(query, nodes_list)
        
        # Update retrieval counts
        for result in results[:limit]:
            node = graph.nodes.get(result.node_id)
            if node:
                node.retrieval_count += 1
        
        # Update metadata
        if graph.metadata:
            graph.metadata.total_queries += 1
            graph.metadata.last_accessed = datetime.now().isoformat()
        
        # Log query if enabled
        if log_query and results:
            top_result = results[0].content[:100] if results else None
            self.query_db.log_query(graph.graph_id, query, len(results), top_result)
        
        return results[:limit]
    
    def random_query(self, graph: KnowledgeGraph, log_query: bool = True) -> List[QueryResult]:
        """Perform a random query by selecting a random node."""
        if not graph.nodes:
            return []
        
        # Pick a random node
        random_node = random.choice(list(graph.nodes.values()))
        
        # Use its content as the query (take first few words)
        query_words = random_node.content.split()[:5]
        query = ' '.join(query_words)
        
        return self.query(query, graph, limit=10, log_query=log_query)
    
    def extract_subgraph(self, query: str, graph: KnowledgeGraph, 
                        hops: int = 1) -> Optional[Dict]:
        """Extract a subgraph centered on the top query result."""
        results = self.query(query, graph, limit=1, log_query=False)
        
        if not results:
            return None
        
        root_node_id = results[0].node_id
        
        # Get all neighbors within specified hops
        neighbor_ids = graph.get_neighbors(root_node_id, hops)
        neighbor_ids.add(root_node_id)  # Include root
        
        # Build subgraph
        subgraph_data = {
            "root_node_id": root_node_id,
            "query": query,
            "hops": hops,
            "nodes": [],
            "edges": []
        }
        
        # Add nodes
        for node_id in neighbor_ids:
            if node_id in graph.nodes:
                node = graph.nodes[node_id]
                subgraph_data["nodes"].append({
                    "id": node.id,
                    "content": node.content,
                    "source_file": node.source_file,
                    "metadata": node.metadata,
                    "retrieval_count": node.retrieval_count,
                    "created_at": node.created_at
                })
        
        # Add edges
        for edge in graph.edges:
            if edge.source_id in neighbor_ids and edge.target_id in neighbor_ids:
                subgraph_data["edges"].append({
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                    "weight": edge.weight,
                    "edge_type": edge.edge_type
                })
        
        return subgraph_data
    
    def get_metadata(self, graph: KnowledgeGraph, query: Optional[str] = None) -> Dict:
        """Get metadata about the graph or a subgraph."""
        metadata = {
            "graph_id": graph.graph_id,
            "total_nodes": len(graph.nodes),
            "total_edges": len(graph.edges),
            "total_queries": graph.metadata.total_queries if graph.metadata else 0,
            "created_at": graph.metadata.created_at if graph.metadata else "unknown",
            "last_accessed": graph.metadata.last_accessed if graph.metadata else "unknown"
        }
        
        if query:
            # Add query-specific metadata
            results = self.query(query, graph, limit=10, log_query=False)
            if results:
                metadata["query"] = query
                metadata["top_result_score"] = results[0].score
                metadata["results_count"] = len(results)
                metadata["avg_score"] = sum(r.score for r in results) / len(results)
        
        # Add retrieval statistics
        if graph.nodes:
            retrieval_counts = [node.retrieval_count for node in graph.nodes.values()]
            metadata["avg_retrieval_count"] = sum(retrieval_counts) / len(retrieval_counts)
            metadata["max_retrieval_count"] = max(retrieval_counts)
            metadata["min_retrieval_count"] = min(retrieval_counts)
        
        return metadata
    
    def save_results_to_file(self, results: List[QueryResult], output_file: str, 
                            append: bool = False) -> bool:
        """Save query results to a file."""
        try:
            mode = 'a' if append else 'w'
            output_path = Path(output_file)
            
            with open(output_path, mode, encoding='utf-8') as f:
                if not append:
                    f.write("# Query Results\n\n")
                
                for i, result in enumerate(results, 1):
                    f.write(f"## Result {i} (Score: {result.score:.4f})\n\n")
                    f.write(f"{result.content}\n\n")
                    if result.source_file:
                        f.write(f"*Source: {result.source_file}*\n\n")
                    f.write("---\n\n")
            
            return True
        except Exception as e:
            print(f"Error saving results: {e}")
            return False
    
    def save_subgraph_to_file(self, subgraph: Dict, output_file: str) -> bool:
        """Save a subgraph to a JSON file."""
        try:
            import json
            output_path = Path(output_file)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(subgraph, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving subgraph: {e}")
            return False
    
    def save_metadata_to_file(self, metadata: Dict, output_file: str) -> bool:
        """Save metadata to a markdown file."""
        try:
            output_path = Path(output_file)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# Graph Metadata\n\n")
                for key, value in metadata.items():
                    f.write(f"- **{key}**: {value}\n")
            
            return True
        except Exception as e:
            print(f"Error saving metadata: {e}")
            return False
