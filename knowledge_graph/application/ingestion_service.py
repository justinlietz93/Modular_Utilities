"""Service for ingesting content into knowledge graphs."""
import uuid
from pathlib import Path
from typing import List, Optional
import re

from ..domain.models import KnowledgeGraph, GraphNode, GraphEdge
from ..infrastructure.similarity import SimilarityService


class IngestionService:
    """Service for ingesting content into knowledge graphs."""
    
    def __init__(self):
        """Initialize ingestion service."""
        self.similarity = SimilarityService()
    
    def ingest_directory(self, directory: Path, graph: KnowledgeGraph, 
                        recursive: bool = False) -> int:
        """Ingest all files from a directory into the graph."""
        count = 0
        
        if recursive:
            files = list(directory.rglob("*"))
        else:
            files = list(directory.glob("*"))
        
        # Filter to only files
        files = [f for f in files if f.is_file()]
        
        for file_path in files:
            if self._is_text_file(file_path):
                if self.ingest_file(file_path, graph):
                    count += 1
        
        # Build edges after ingestion
        self._build_edges(graph)
        
        return count
    
    def ingest_file(self, file_path: Path, graph: KnowledgeGraph) -> bool:
        """Ingest a single file into the graph."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Split content into chunks (paragraphs or sections)
            chunks = self._split_content(content)
            
            for chunk in chunks:
                if len(chunk.strip()) < 10:  # Skip very short chunks
                    continue
                
                node_id = str(uuid.uuid4())
                node = GraphNode(
                    id=node_id,
                    content=chunk,
                    source_file=str(file_path),
                    metadata={"file_name": file_path.name}
                )
                graph.add_node(node)
            
            return True
        except Exception as e:
            print(f"Warning: Could not ingest {file_path}: {e}")
            return False
    
    def _is_text_file(self, file_path: Path) -> bool:
        """Check if a file is likely a text file."""
        text_extensions = {
            '.txt', '.md', '.markdown', '.rst', '.log',
            '.py', '.js', '.java', '.cpp', '.c', '.h',
            '.html', '.css', '.json', '.xml', '.yaml', '.yml',
            '.sh', '.bash', '.csv', '.tex', '.org'
        }
        return file_path.suffix.lower() in text_extensions
    
    def _split_content(self, content: str) -> List[str]:
        """Split content into meaningful chunks."""
        # Split by double newlines (paragraphs)
        chunks = re.split(r'\n\s*\n', content)
        
        # Also split very long chunks
        result = []
        max_chunk_size = 1000
        
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            
            if len(chunk) <= max_chunk_size:
                result.append(chunk)
            else:
                # Split by sentences
                sentences = re.split(r'[.!?]+\s+', chunk)
                current = []
                current_len = 0
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    if current_len + len(sentence) > max_chunk_size and current:
                        result.append(' '.join(current))
                        current = [sentence]
                        current_len = len(sentence)
                    else:
                        current.append(sentence)
                        current_len += len(sentence)
                
                if current:
                    result.append(' '.join(current))
        
        return result
    
    def _build_edges(self, graph: KnowledgeGraph, similarity_threshold: float = 0.3):
        """Build edges between similar nodes."""
        nodes_list = list(graph.nodes.values())
        
        # Only create edges for graphs with reasonable size
        if len(nodes_list) > 1000:
            # For large graphs, limit edge creation
            similarity_threshold = 0.5
        
        for i, node1 in enumerate(nodes_list):
            # Limit edges per node
            edges_added = 0
            max_edges_per_node = 10
            
            for j, node2 in enumerate(nodes_list):
                if i >= j:  # Skip self and already processed pairs
                    continue
                
                if edges_added >= max_edges_per_node:
                    break
                
                weight = self.similarity.calculate_edge_weight(node1, node2, nodes_list)
                
                if weight >= similarity_threshold:
                    edge = GraphEdge(
                        source_id=node1.id,
                        target_id=node2.id,
                        weight=weight
                    )
                    graph.add_edge(edge)
                    edges_added += 1
