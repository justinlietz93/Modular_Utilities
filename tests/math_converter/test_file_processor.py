"""Tests for file processor."""
import pytest
from pathlib import Path
import tempfile
import shutil

from math_converter.application.file_processor import FileProcessor
from math_converter.domain.syntax_types import SyntaxType, ConversionRequest


class TestFileProcessor:
    """Test FileProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create file processor."""
        return FileProcessor()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_discover_files_single_file(self, processor, temp_dir):
        """Test discovering a single file."""
        test_file = temp_dir / "test.md"
        test_file.write_text("content")
        
        files = processor.discover_files([str(test_file)])
        assert len(files) == 1
        assert files[0] == test_file
    
    def test_discover_files_directory(self, processor, temp_dir):
        """Test discovering files in a directory."""
        (temp_dir / "test1.md").write_text("content1")
        (temp_dir / "test2.txt").write_text("content2")
        (temp_dir / "test3.py").write_text("content3")  # Not supported
        
        files = processor.discover_files([str(temp_dir)])
        assert len(files) == 2
        assert any(f.name == "test1.md" for f in files)
        assert any(f.name == "test2.txt" for f in files)
    
    def test_discover_files_supported_extensions(self, processor, temp_dir):
        """Test that only supported extensions are discovered."""
        for ext in [".md", ".tex", ".txt", ".rst", ".html"]:
            (temp_dir / f"test{ext}").write_text("content")
        (temp_dir / "test.py").write_text("content")
        
        files = processor.discover_files([str(temp_dir)])
        assert len(files) == 5
        assert not any(f.suffix == ".py" for f in files)
    
    def test_process_file_in_place(self, processor, temp_dir):
        """Test processing file in place."""
        test_file = temp_dir / "test.md"
        test_file.write_text(r"Math: \( x + y \)")
        
        success = processor.process_file(
            test_file,
            SyntaxType.LATEX,
            SyntaxType.MATHJAX,
            in_place=True
        )
        
        assert success
        content = test_file.read_text()
        assert "$`" in content
        assert "x + y" in content
    
    def test_process_file_to_output_dir(self, processor, temp_dir):
        """Test processing file to output directory."""
        test_file = temp_dir / "test.md"
        test_file.write_text(r"Math: \( x + y \)")
        output_dir = temp_dir / "output"
        
        success = processor.process_file(
            test_file,
            SyntaxType.LATEX,
            SyntaxType.MATHJAX,
            output_dir=str(output_dir),
            in_place=False
        )
        
        assert success
        output_file = output_dir / "test.md"
        assert output_file.exists()
        content = output_file.read_text()
        assert "$`" in content
        
        # Original should be unchanged
        original = test_file.read_text()
        assert r"\(" in original
    
    def test_process_files_with_request(self, processor, temp_dir):
        """Test processing multiple files with ConversionRequest."""
        (temp_dir / "test1.md").write_text(r"Math: \( a \)")
        (temp_dir / "test2.md").write_text(r"Math: \( b \)")
        
        request = ConversionRequest(
            from_syntax=SyntaxType.LATEX,
            to_syntax=SyntaxType.MATHJAX,
            input_paths=[str(temp_dir)],
            output_dir=None,
            in_place=True,
            auto_yes=False,
            auto_no=False
        )
        
        count = processor.process_files(request)
        assert count == 2
    
    def test_process_files_empty_directory(self, processor, temp_dir):
        """Test processing empty directory."""
        request = ConversionRequest(
            from_syntax=SyntaxType.LATEX,
            to_syntax=SyntaxType.MATHJAX,
            input_paths=[str(temp_dir)],
            output_dir=None,
            in_place=True,
            auto_yes=False,
            auto_no=False
        )
        
        count = processor.process_files(request)
        assert count == 0
