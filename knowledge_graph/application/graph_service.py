"""Application services for knowledge graph operations."""
from typing import Optional, List
from pathlib import Path
import uuid
from datetime import datetime

from ..domain.models import KnowledgeGraph, GraphNode, GraphEdge, QueryResult, Settings, VerbosityLevel
from ..infrastructure.storage import GraphStorage, LastGraphTracker, QueryDatabase, SettingsStorage
from ..infrastructure.similarity import SimilarityService


class GraphService:
    """Service for managing knowledge graphs."""
    
    def __init__(self, storage_dir: str = ".knowledge_graphs"):
        """Initialize graph service."""
        self.storage = GraphStorage(storage_dir)
        self.tracker = LastGraphTracker(storage_dir)
        self.settings_storage = SettingsStorage(storage_dir)
        self.settings = self.settings_storage.load_settings()
    
    def create_graph(self, graph_id: str) -> bool:
        """Create a new empty graph."""
        if self.storage.graph_exists(graph_id):
            return False
        
        graph = KnowledgeGraph(graph_id=graph_id)
        success = self.storage.save_graph(graph)
        if success:
            self.tracker.set_last_graph(graph_id)
        return success
    
    def delete_graph(self, graph_id: str) -> bool:
        """Delete a graph."""
        return self.storage.delete_graph(graph_id)
    
    def get_graph(self, graph_id: Optional[str] = None) -> Optional[KnowledgeGraph]:
        """Get a graph by ID or the last accessed graph."""
        if graph_id is None:
            graph_id = self.tracker.get_last_graph()
            if graph_id is None:
                return None
        
        graph = self.storage.load_graph(graph_id)
        if graph:
            self.tracker.set_last_graph(graph_id)
            if graph.metadata:
                graph.metadata.last_accessed = datetime.now().isoformat()
                self.storage.save_graph(graph)
        return graph
    
    def save_graph(self, graph: KnowledgeGraph) -> bool:
        """Save a graph."""
        success = self.storage.save_graph(graph)
        if success:
            self.tracker.set_last_graph(graph.graph_id)
        return success
    
    def list_graphs(self) -> List[str]:
        """List all available graphs."""
        return self.storage.list_graphs()
    
    def dump_graph(self, graph_id: Optional[str] = None, output_file: Optional[str] = None) -> bool:
        """Dump a graph to a file."""
        graph = self.get_graph(graph_id)
        if not graph:
            return False
        
        # Determine output file
        if output_file is None:
            output_file = f"{graph.graph_id}_dump.json"
        
        import json
        output_path = Path(output_file)
        
        try:
            # Create a complete representation
            data = {
                "graph_id": graph.graph_id,
                "metadata": graph.metadata.to_dict() if graph.metadata else None,
                "nodes": [
                    {
                        "id": node.id,
                        "content": node.content,
                        "source_file": node.source_file,
                        "metadata": node.metadata,
                        "retrieval_count": node.retrieval_count,
                        "created_at": node.created_at
                    }
                    for node in graph.nodes.values()
                ],
                "edges": [
                    {
                        "source_id": edge.source_id,
                        "target_id": edge.target_id,
                        "weight": edge.weight,
                        "edge_type": edge.edge_type
                    }
                    for edge in graph.edges
                ]
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error dumping graph: {e}")
            return False


class SettingsService:
    """Service for managing settings."""
    
    def __init__(self, storage_dir: str = ".knowledge_graphs"):
        """Initialize settings service."""
        self.storage = SettingsStorage(storage_dir)
        self.settings = self.storage.load_settings()
    
    def get_settings(self) -> Settings:
        """Get current settings."""
        return self.settings
    
    def update_verbosity(self, level: VerbosityLevel) -> bool:
        """Update verbosity level."""
        self.settings.verbosity = level
        return self.storage.save_settings(self.settings)
    
    def update_database(self, enabled: bool) -> bool:
        """Enable or disable query database."""
        self.settings.database_enabled = enabled
        return self.storage.save_settings(self.settings)
    
    def should_log(self, level: VerbosityLevel) -> bool:
        """Check if a message at the given level should be logged."""
        levels = [VerbosityLevel.OFF, VerbosityLevel.LOW, VerbosityLevel.MEDIUM, 
                 VerbosityLevel.HIGH, VerbosityLevel.MAX]
        current_idx = levels.index(self.settings.verbosity)
        required_idx = levels.index(level)
        return current_idx >= required_idx
