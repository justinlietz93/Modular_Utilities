"""Tests for ingestion service with PDF and image support."""
import pytest
import tempfile
import shutil
from pathlib import Path

from knowledge_graph.application.ingestion_service import IngestionService
from knowledge_graph.domain.models import KnowledgeGraph


@pytest.fixture
def temp_dir():
    """Create temporary directory."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_graph():
    """Create a sample knowledge graph."""
    return KnowledgeGraph(graph_id="test-graph")


def test_text_file_ingestion(temp_dir, sample_graph):
    """Test ingesting a text file."""
    # Create a text file
    text_file = temp_dir / "sample.txt"
    text_file.write_text("This is a test paragraph.\n\nThis is another paragraph.", encoding='utf-8')
    
    service = IngestionService()
    result = service.ingest_file(text_file, sample_graph)
    
    assert result is True
    assert len(sample_graph.nodes) > 0


def test_markdown_file_ingestion(temp_dir, sample_graph):
    """Test ingesting a markdown file."""
    # Create a markdown file
    md_file = temp_dir / "sample.md"
    md_file.write_text("# Header\n\nThis is markdown content.\n\n## Section\n\nMore content here.", encoding='utf-8')
    
    service = IngestionService()
    result = service.ingest_file(md_file, sample_graph)
    
    assert result is True
    assert len(sample_graph.nodes) > 0


def test_directory_ingestion(temp_dir, sample_graph):
    """Test ingesting files from a directory."""
    # Create multiple files
    (temp_dir / "file1.txt").write_text("Content of file 1.", encoding='utf-8')
    (temp_dir / "file2.txt").write_text("Content of file 2.", encoding='utf-8')
    (temp_dir / "file3.md").write_text("Content of file 3.", encoding='utf-8')
    
    service = IngestionService()
    count = service.ingest_directory(temp_dir, sample_graph, recursive=False)
    
    assert count == 3
    assert len(sample_graph.nodes) > 0


def test_recursive_directory_ingestion(temp_dir, sample_graph):
    """Test recursive directory ingestion."""
    # Create nested directories with files
    sub_dir = temp_dir / "subdir"
    sub_dir.mkdir()
    
    (temp_dir / "root.txt").write_text("Root file content.", encoding='utf-8')
    (sub_dir / "nested.txt").write_text("Nested file content.", encoding='utf-8')
    
    service = IngestionService()
    count = service.ingest_directory(temp_dir, sample_graph, recursive=True)
    
    assert count == 2
    assert len(sample_graph.nodes) > 0


def test_is_text_file(temp_dir):
    """Test text file detection."""
    service = IngestionService()
    
    assert service._is_text_file(Path("file.txt"))
    assert service._is_text_file(Path("file.md"))
    assert service._is_text_file(Path("file.py"))
    assert not service._is_text_file(Path("file.pdf"))
    assert not service._is_text_file(Path("file.jpg"))


def test_is_pdf_file(temp_dir):
    """Test PDF file detection."""
    service = IngestionService()
    
    assert service._is_pdf_file(Path("document.pdf"))
    assert service._is_pdf_file(Path("document.PDF"))
    assert not service._is_pdf_file(Path("document.txt"))


def test_is_image_file(temp_dir):
    """Test image file detection."""
    service = IngestionService()
    
    assert service._is_image_file(Path("image.png"))
    assert service._is_image_file(Path("image.jpg"))
    assert service._is_image_file(Path("image.jpeg"))
    assert service._is_image_file(Path("image.gif"))
    assert not service._is_image_file(Path("image.pdf"))


def test_is_supported_file(temp_dir):
    """Test supported file detection."""
    service = IngestionService()
    
    assert service._is_supported_file(Path("file.txt"))
    assert service._is_supported_file(Path("file.pdf"))
    assert service._is_supported_file(Path("file.png"))
    assert not service._is_supported_file(Path("file.exe"))
    assert not service._is_supported_file(Path("file.bin"))


def test_pdf_extractor_availability():
    """Test PDF extractor availability check."""
    service = IngestionService()
    # This just checks that the extractor is instantiated
    assert hasattr(service, 'pdf_extractor')


def test_image_extractor_availability():
    """Test image extractor availability check."""
    service = IngestionService()
    # This just checks that the extractor is instantiated
    assert hasattr(service, 'image_extractor')


def test_short_content_filtering(temp_dir, sample_graph):
    """Test that very short content chunks are filtered out."""
    # Create a file with very short content
    text_file = temp_dir / "short.txt"
    text_file.write_text("Hi", encoding='utf-8')
    
    service = IngestionService()
    result = service.ingest_file(text_file, sample_graph)
    
    # File processes successfully but no nodes added due to short content
    assert result is True
    assert len(sample_graph.nodes) == 0


def test_empty_file(temp_dir, sample_graph):
    """Test ingesting an empty file."""
    # Create an empty file
    empty_file = temp_dir / "empty.txt"
    empty_file.write_text("", encoding='utf-8')
    
    service = IngestionService()
    result = service.ingest_file(empty_file, sample_graph)
    
    # File processes successfully but no nodes added
    assert result is True
    assert len(sample_graph.nodes) == 0


def test_extract_content_text_file(temp_dir):
    """Test extracting content from text files."""
    service = IngestionService()
    
    text_file = temp_dir / "test.txt"
    text_file.write_text("Test content", encoding='utf-8')
    
    content = service._extract_content(text_file)
    
    assert content == "Test content"


def test_extract_content_unsupported_file(temp_dir):
    """Test extracting content from unsupported file types."""
    service = IngestionService()
    
    # Create an unsupported file type
    unsupported_file = temp_dir / "test.exe"
    unsupported_file.write_bytes(b'\x00\x01\x02\x03')
    
    content = service._extract_content(unsupported_file)
    
    assert content is None
