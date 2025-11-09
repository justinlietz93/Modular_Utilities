"""Storage infrastructure for knowledge graphs."""
import json
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from ..domain.models import KnowledgeGraph, GraphNode, GraphEdge, GraphMetadata, Settings, VerbosityLevel


class GraphStorage:
    """Handles persistence of knowledge graphs to disk."""
    
    def __init__(self, storage_dir: str = ".knowledge_graphs"):
        """Initialize storage with directory."""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
    
    def save_graph(self, graph: KnowledgeGraph) -> bool:
        """Save a graph to disk."""
        try:
            graph_file = self.storage_dir / f"{graph.graph_id}.json"
            
            # Convert graph to serializable format
            data = {
                "graph_id": graph.graph_id,
                "nodes": {
                    node_id: {
                        "id": node.id,
                        "content": node.content,
                        "source_file": node.source_file,
                        "metadata": node.metadata,
                        "retrieval_count": node.retrieval_count,
                        "created_at": node.created_at
                    }
                    for node_id, node in graph.nodes.items()
                },
                "edges": [
                    {
                        "source_id": edge.source_id,
                        "target_id": edge.target_id,
                        "weight": edge.weight,
                        "edge_type": edge.edge_type
                    }
                    for edge in graph.edges
                ],
                "metadata": graph.metadata.to_dict() if graph.metadata else None
            }
            
            with open(graph_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving graph: {e}")
            return False
    
    def load_graph(self, graph_id: str) -> Optional[KnowledgeGraph]:
        """Load a graph from disk."""
        try:
            graph_file = self.storage_dir / f"{graph_id}.json"
            
            if not graph_file.exists():
                return None
            
            with open(graph_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruct graph
            graph = KnowledgeGraph(graph_id=data["graph_id"])
            
            # Load nodes
            for node_data in data["nodes"].values():
                node = GraphNode(
                    id=node_data["id"],
                    content=node_data["content"],
                    source_file=node_data.get("source_file"),
                    metadata=node_data.get("metadata", {}),
                    retrieval_count=node_data.get("retrieval_count", 0),
                    created_at=node_data.get("created_at", datetime.now().isoformat())
                )
                graph.add_node(node)
            
            # Load edges
            for edge_data in data["edges"]:
                edge = GraphEdge(
                    source_id=edge_data["source_id"],
                    target_id=edge_data["target_id"],
                    weight=edge_data.get("weight", 1.0),
                    edge_type=edge_data.get("edge_type", "similarity")
                )
                graph.add_edge(edge)
            
            # Load metadata
            if data.get("metadata"):
                meta = data["metadata"]
                graph.metadata = GraphMetadata(
                    graph_id=meta["graph_id"],
                    node_count=meta.get("node_count", 0),
                    edge_count=meta.get("edge_count", 0),
                    total_queries=meta.get("total_queries", 0),
                    created_at=meta.get("created_at", datetime.now().isoformat()),
                    last_accessed=meta.get("last_accessed", datetime.now().isoformat())
                )
            
            return graph
        except Exception as e:
            print(f"Error loading graph: {e}")
            return None
    
    def delete_graph(self, graph_id: str) -> bool:
        """Delete a graph from disk."""
        try:
            graph_file = self.storage_dir / f"{graph_id}.json"
            if graph_file.exists():
                graph_file.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting graph: {e}")
            return False
    
    def list_graphs(self) -> List[str]:
        """List all available graph IDs."""
        try:
            return [f.stem for f in self.storage_dir.glob("*.json")]
        except Exception:
            return []
    
    def graph_exists(self, graph_id: str) -> bool:
        """Check if a graph exists."""
        graph_file = self.storage_dir / f"{graph_id}.json"
        return graph_file.exists()


class LastGraphTracker:
    """Tracks the last graph that was interacted with."""
    
    def __init__(self, storage_dir: str = ".knowledge_graphs"):
        """Initialize tracker."""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.tracker_file = self.storage_dir / ".last_graph"
    
    def set_last_graph(self, graph_id: str):
        """Set the last accessed graph."""
        try:
            self.tracker_file.write_text(graph_id, encoding='utf-8')
        except Exception as e:
            print(f"Warning: Could not save last graph tracker: {e}")
    
    def get_last_graph(self) -> Optional[str]:
        """Get the last accessed graph ID."""
        try:
            if self.tracker_file.exists():
                return self.tracker_file.read_text(encoding='utf-8').strip()
            return None
        except Exception:
            return None


class QueryDatabase:
    """SQLite database for tracking queries."""
    
    def __init__(self, storage_dir: str = ".knowledge_graphs"):
        """Initialize database."""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.db_file = self.storage_dir / "queries.db"
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(str(self.db_file)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    graph_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    result_count INTEGER,
                    top_result TEXT
                )
            """)
            conn.commit()
    
    def log_query(self, graph_id: str, query: str, result_count: int, top_result: Optional[str] = None):
        """Log a query to the database."""
        try:
            with sqlite3.connect(str(self.db_file)) as conn:
                conn.execute(
                    "INSERT INTO queries (graph_id, query, timestamp, result_count, top_result) VALUES (?, ?, ?, ?, ?)",
                    (graph_id, query, datetime.now().isoformat(), result_count, top_result)
                )
                conn.commit()
        except Exception as e:
            print(f"Warning: Could not log query: {e}")
    
    def get_query_history(self, graph_id: str, limit: int = 100) -> List[Dict]:
        """Get query history for a graph."""
        try:
            with sqlite3.connect(str(self.db_file)) as conn:
                cursor = conn.execute(
                    "SELECT query, timestamp, result_count, top_result FROM queries WHERE graph_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (graph_id, limit)
                )
                rows = cursor.fetchall()
                return [
                    {
                        "query": row[0],
                        "timestamp": row[1],
                        "result_count": row[2],
                        "top_result": row[3]
                    }
                    for row in rows
                ]
        except Exception:
            return []


class SettingsStorage:
    """Storage for user settings."""
    
    def __init__(self, storage_dir: str = ".knowledge_graphs"):
        """Initialize settings storage."""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.settings_file = self.storage_dir / "settings.json"
    
    def save_settings(self, settings: Settings) -> bool:
        """Save settings to disk."""
        try:
            data = {
                "verbosity": settings.verbosity.value,
                "database_enabled": settings.database_enabled,
                "storage_dir": settings.storage_dir
            }
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def load_settings(self) -> Settings:
        """Load settings from disk."""
        try:
            if not self.settings_file.exists():
                return Settings()
            
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return Settings(
                verbosity=VerbosityLevel(data.get("verbosity", "medium")),
                database_enabled=data.get("database_enabled", True),
                storage_dir=data.get("storage_dir", ".knowledge_graphs")
            )
        except Exception:
            return Settings()
