"""CLI interface for the advanced chunking module."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from advanced_chunking.domain.models import ChunkingConfig, ChunkingStrategy
from advanced_chunking.application.input_handler import InputHandler
from advanced_chunking.application.output_formatter import OutputFormatter


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser.
    
    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Advanced text chunking with structural awareness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Chunk a file by sentences
  %(prog)s --input document.txt --strategy sentence

  # Chunk by word count
  %(prog)s --input document.txt --strategy word_count --word-count 100

  # Process a directory recursively
  %(prog)s --input /path/to/docs --strategy paragraph --output chunks/

  # Chunk with OCR enabled
  %(prog)s --input scanned.pdf --strategy paragraph --enable-ocr

  # Output as aggregated JSON
  %(prog)s --input docs/ --strategy token_count --token-count 500 --aggregated
        """,
    )

    # Input/Output
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Input file or directory path",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("chunks_output"),
        help="Output directory (default: chunks_output)",
    )

    # Chunking strategy
    parser.add_argument(
        "--strategy",
        "-s",
        type=str,
        choices=[s.value for s in ChunkingStrategy],
        required=True,
        help="Chunking strategy to use",
    )

    # Strategy parameters
    parser.add_argument(
        "--word-count",
        type=int,
        help="Number of words per chunk (for word_count strategy)",
    )
    parser.add_argument(
        "--character-count",
        type=int,
        help="Number of characters per chunk (for character_count strategy)",
    )
    parser.add_argument(
        "--token-count",
        type=int,
        help="Number of tokens per chunk (for token_count strategy)",
    )
    parser.add_argument(
        "--tokenizer-model",
        type=str,
        default="gpt-3.5-turbo",
        help="Tokenizer model for token counting (default: gpt-3.5-turbo)",
    )

    # Structural preservation
    parser.add_argument(
        "--preserve-code",
        action="store_true",
        default=True,
        help="Preserve code blocks within chunks (default: True)",
    )
    parser.add_argument(
        "--no-preserve-code",
        action="store_false",
        dest="preserve_code",
        help="Don't preserve code blocks",
    )
    parser.add_argument(
        "--preserve-math",
        action="store_true",
        default=True,
        help="Preserve mathematical expressions (default: True)",
    )
    parser.add_argument(
        "--no-preserve-math",
        action="store_false",
        dest="preserve_math",
        help="Don't preserve math expressions",
    )

    # OCR and text repair
    parser.add_argument(
        "--enable-ocr",
        action="store_true",
        help="Enable OCR for image-based documents",
    )
    parser.add_argument(
        "--no-repair-ocr",
        action="store_false",
        dest="repair_ocr",
        default=True,
        help="Disable OCR artifact repair",
    )
    parser.add_argument(
        "--no-repair-mojibake",
        action="store_false",
        dest="repair_mojibake",
        default=True,
        help="Disable mojibake repair",
    )

    # Output format
    parser.add_argument(
        "--aggregated",
        action="store_true",
        help="Output all chunks to a single JSON file",
    )
    parser.add_argument(
        "--text-output",
        action="store_true",
        help="Output in plain text format instead of JSON",
    )

    # Directory processing
    parser.add_argument(
        "--no-recursive",
        action="store_false",
        dest="recursive",
        default=True,
        help="Don't process subdirectories recursively",
    )

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """Main CLI entry point.
    
    Args:
        argv: Command line arguments (for testing)
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    try:
        # Create configuration
        config = ChunkingConfig(
            strategy=ChunkingStrategy(args.strategy),
            word_count=args.word_count,
            character_count=args.character_count,
            token_count=args.token_count,
            tokenizer_model=args.tokenizer_model,
            preserve_code_blocks=args.preserve_code,
            preserve_math_expressions=args.preserve_math,
            enable_ocr=args.enable_ocr,
            repair_ocr_artifacts=args.repair_ocr,
            repair_mojibake=args.repair_mojibake,
        )

        # Validate configuration
        config.validate()

        # Create input handler
        handler = InputHandler(config)

        # Process input
        input_path = args.input.resolve()
        if input_path.is_file():
            print(f"Processing file: {input_path}")
            chunks = handler.process_file(input_path)
            file_chunks = {input_path: chunks}
            print(f"Generated {len(chunks)} chunks")
        elif input_path.is_dir():
            print(f"Processing directory: {input_path}")
            file_chunks = handler.process_directory(input_path, args.recursive)
            total_chunks = sum(len(chunks) for chunks in file_chunks.values())
            print(f"Processed {len(file_chunks)} files, generated {total_chunks} chunks")
        else:
            print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
            return 1

        # Create output formatter
        formatter = OutputFormatter(args.output)

        # Write output
        if args.text_output:
            output_file = formatter.write_text_output(file_chunks)
            print(f"Output written to: {output_file}")
        elif args.aggregated:
            output_file = formatter.write_aggregated_json(file_chunks)
            print(f"Aggregated output written to: {output_file}")
        else:
            output_files = formatter.write_per_file_json(file_chunks, input_path.parent)
            print(f"Output written to {len(output_files)} files in: {args.output}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
