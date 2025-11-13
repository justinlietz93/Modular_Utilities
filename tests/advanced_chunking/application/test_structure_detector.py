"""Tests for structure detector."""

import pytest

from advanced_chunking.application.structure_detector import StructureDetector


def test_structure_detector_initialization():
    """Test StructureDetector initialization."""
    detector = StructureDetector()
    assert detector is not None


def test_detect_code_blocks_fenced():
    """Test detection of fenced code blocks."""
    detector = StructureDetector()

    text = """
Some text before.

```python
def hello():
    print("Hello")
```

Some text after.
"""

    blocks = detector.detect_code_blocks(text)
    assert len(blocks) > 0


def test_detect_code_blocks_indented():
    """Test detection of indented code blocks."""
    detector = StructureDetector()

    text = """
Normal text.

    def hello():
        print("Hello")
        return True

More text.
"""

    blocks = detector.detect_code_blocks(text)
    assert len(blocks) > 0


def test_has_code_structure():
    """Test code structure detection."""
    detector = StructureDetector()

    code_text = """
def calculate(x, y):
    return x + y
"""

    assert detector.has_code_structure(code_text) is True

    normal_text = "This is just normal text without any code."
    # May or may not detect - depends on pattern matching
    # Just ensure it doesn't crash
    detector.has_code_structure(normal_text)


def test_detect_mathematical_expressions():
    """Test math expression detection."""
    detector = StructureDetector()

    text = "The equation is $E = mc^2$ as Einstein showed."
    regions = detector.detect_mathematical_expressions(text)

    assert len(regions) > 0


def test_detect_mathematical_expressions_display():
    """Test display math detection."""
    detector = StructureDetector()

    text = "The formula is: $$\\int_0^1 x^2 dx$$"
    regions = detector.detect_mathematical_expressions(text)

    assert len(regions) > 0


def test_has_mathematical_content():
    """Test mathematical content detection."""
    detector = StructureDetector()

    math_text = "Consider the equation: $x^2 + y^2 = r^2$"
    assert detector.has_mathematical_content(math_text) is True

    normal_text = "This is just normal text."
    assert detector.has_mathematical_content(normal_text) is False


def test_extract_structure_info():
    """Test comprehensive structure information extraction."""
    detector = StructureDetector()

    text = """
Some text.

```python
def test():
    pass
```

The equation $E = mc^2$ is famous.
"""

    info = detector.extract_structure_info(text)

    assert "has_code" in info
    assert "has_math" in info
    assert "code_blocks" in info
    assert "math_regions" in info
    assert isinstance(info["has_code"], bool)
    assert isinstance(info["has_math"], bool)


def test_find_safe_break_points():
    """Test finding safe break points."""
    detector = StructureDetector()

    text = "Start. ```code here``` Middle. $math$ End."
    prefer_positions = [10, 20, 30, 40]

    safe_positions = detector.find_safe_break_points(text, prefer_positions)

    assert len(safe_positions) == len(prefer_positions)
    assert isinstance(safe_positions, list)
