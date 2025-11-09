"""Service for pruning knowledge graphs."""
from typing import List

from ..domain.models import KnowledgeGraph, GraphNode


class PruningService:
    """Service for pruning nodes from knowledge graphs."""
    
    def prune_bottom(self, graph: KnowledgeGraph, percentage: int = 10) -> int:
        """Prune bottom percentage of nodes based on retrieval frequency and uniqueness."""
        if not graph.nodes or percentage <= 0 or percentage >= 100:
            return 0
        
        nodes_list = list(graph.nodes.values())
        
        # Calculate pruning scores for each node
        scored_nodes = []
        for node in nodes_list:
            uniqueness = node.calculate_uniqueness(nodes_list)
            # Score: higher retrieval count = higher score, higher uniqueness = higher score
            # Lower score = more likely to be pruned
            score = node.retrieval_count + (uniqueness * 10)
            scored_nodes.append((score, node))
        
        # Sort by score (ascending - lowest first)
        scored_nodes.sort(key=lambda x: x[0])
        
        # Calculate how many to prune
        num_to_prune = max(1, int(len(nodes_list) * percentage / 100))
        nodes_to_prune = [node for _, node in scored_nodes[:num_to_prune]]
        
        # Remove nodes
        pruned_count = self._remove_nodes(graph, nodes_to_prune)
        
        return pruned_count
    
    def prune_top(self, graph: KnowledgeGraph, percentage: int = 10) -> int:
        """Prune top percentage of nodes based on retrieval frequency (to thin noise)."""
        if not graph.nodes or percentage <= 0 or percentage >= 100:
            return 0
        
        nodes_list = list(graph.nodes.values())
        
        # Sort by retrieval count (descending - highest first)
        sorted_nodes = sorted(nodes_list, key=lambda n: n.retrieval_count, reverse=True)
        
        # Calculate how many to prune
        num_to_prune = max(1, int(len(nodes_list) * percentage / 100))
        nodes_to_prune = sorted_nodes[:num_to_prune]
        
        # Remove nodes
        pruned_count = self._remove_nodes(graph, nodes_to_prune)
        
        return pruned_count
    
    def _remove_nodes(self, graph: KnowledgeGraph, nodes_to_remove: List[GraphNode]) -> int:
        """Remove nodes and their associated edges from the graph."""
        node_ids_to_remove = {node.id for node in nodes_to_remove}
        
        # Remove nodes
        for node_id in node_ids_to_remove:
            if node_id in graph.nodes:
                del graph.nodes[node_id]
        
        # Remove edges connected to removed nodes
        graph.edges = [
            edge for edge in graph.edges
            if edge.source_id not in node_ids_to_remove 
            and edge.target_id not in node_ids_to_remove
        ]
        
        # Update metadata
        if graph.metadata:
            graph.metadata.node_count = len(graph.nodes)
            graph.metadata.edge_count = len(graph.edges)
        
        return len(node_ids_to_remove)
