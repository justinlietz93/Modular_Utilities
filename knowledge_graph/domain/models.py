"""Domain models for knowledge graph."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime
from enum import Enum


class VerbosityLevel(Enum):
    """Verbosity levels for CLI output."""
    OFF = "off"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAX = "max"


@dataclass
class GraphNode:
    """Represents a node in the knowledge graph."""
    id: str
    content: str
    source_file: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)
    retrieval_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def calculate_uniqueness(self, all_nodes: List['GraphNode']) -> float:
        """Calculate uniqueness score based on content similarity to other nodes."""
        # Simple uniqueness: inverse of content overlap
        if not all_nodes or len(all_nodes) == 1:
            return 1.0
        
        words = set(self.content.lower().split())
        if not words:
            return 0.0
        
        total_overlap = 0
        for other in all_nodes:
            if other.id == self.id:
                continue
            other_words = set(other.content.lower().split())
            if other_words:
                overlap = len(words & other_words) / len(words | other_words)
                total_overlap += overlap
        
        # Normalize by number of other nodes
        avg_overlap = total_overlap / (len(all_nodes) - 1) if len(all_nodes) > 1 else 0
        return 1.0 - avg_overlap


@dataclass
class GraphEdge:
    """Represents an edge between nodes in the knowledge graph."""
    source_id: str
    target_id: str
    weight: float = 1.0
    edge_type: str = "similarity"


@dataclass
class GraphMetadata:
    """Metadata about a knowledge graph."""
    graph_id: str
    node_count: int = 0
    edge_count: int = 0
    total_queries: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert metadata to dictionary."""
        return {
            "graph_id": self.graph_id,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "total_queries": self.total_queries,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed
        }


@dataclass
class KnowledgeGraph:
    """Represents a complete knowledge graph."""
    graph_id: str
    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: List[GraphEdge] = field(default_factory=list)
    metadata: Optional[GraphMetadata] = None
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = GraphMetadata(graph_id=self.graph_id)
    
    def add_node(self, node: GraphNode):
        """Add a node to the graph."""
        self.nodes[node.id] = node
        if self.metadata:
            self.metadata.node_count = len(self.nodes)
    
    def add_edge(self, edge: GraphEdge):
        """Add an edge to the graph."""
        self.edges.append(edge)
        if self.metadata:
            self.metadata.edge_count = len(self.edges)
    
    def get_neighbors(self, node_id: str, hops: int = 1) -> Set[str]:
        """Get all neighbors within specified number of hops."""
        if hops <= 0:
            return set()
        
        neighbors = set()
        current_level = {node_id}
        
        for _ in range(hops):
            next_level = set()
            for current_id in current_level:
                for edge in self.edges:
                    if edge.source_id == current_id:
                        next_level.add(edge.target_id)
                    elif edge.target_id == current_id:
                        next_level.add(edge.source_id)
            
            neighbors.update(next_level)
            current_level = next_level
        
        return neighbors


@dataclass
class QueryResult:
    """Result from a query operation."""
    node_id: str
    content: str
    score: float
    source_file: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class Settings:
    """Configuration settings for the knowledge graph system."""
    verbosity: VerbosityLevel = VerbosityLevel.MEDIUM
    database_enabled: bool = True
    storage_dir: str = ".knowledge_graphs"
