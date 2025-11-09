"""CLI entry point for math syntax converter."""
import argparse
import sys
from pathlib import Path
from typing import Optional

from ...domain.syntax_types import SyntaxType, ConversionRequest
from ...application.file_processor import FileProcessor


def prompt_user(message: str, options: list, allow_cancel: bool = False) -> Optional[str]:
    """
    Prompt user to select from options.
    
    Args:
        message: Message to display
        options: List of options
        allow_cancel: Whether to allow canceling
        
    Returns:
        Selected option or None if canceled
    """
    print(f"\n{message}")
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    if allow_cancel:
        print("  0. Cancel")
    
    while True:
        try:
            choice = input("\nEnter your choice: ").strip()
            choice_num = int(choice)
            
            if allow_cancel and choice_num == 0:
                return None
            
            if 1 <= choice_num <= len(options):
                return options[choice_num - 1]
            
            print("Invalid choice. Please try again.")
        except (ValueError, KeyboardInterrupt):
            print("\nInvalid input.")
            if allow_cancel:
                return None


def prompt_yes_no(message: str) -> bool:
    """
    Prompt user for yes/no response.
    
    Args:
        message: Message to display
        
    Returns:
        True for yes, False for no
    """
    while True:
        response = input(f"{message} (y/n): ").strip().lower()
        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        print("Please enter 'y' or 'n'.")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='convert-math',
        description='Convert math syntax between LaTeX, MathJax, ASCII, and Unicode, or extract math from PDFs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert between syntax formats
  convert-math --from latex --to mathjax --input math_writeups/
  convert-math --from latex --to mathjax --input math_writeups/ --output-dir converted/
  convert-math --from latex --to mathjax
  convert-math --to mathjax
  convert-math --from latex
  
  # Extract math from PDF
  convert-math --input research-paper.pdf --output research-equations.md
  convert-math --input research-paper.pdf  # Creates research-paper.md
        """
    )
    
    parser.add_argument(
        '--from',
        dest='from_syntax',
        type=str,
        help='Source math syntax (latex, mathjax, ascii, unicode)'
    )
    
    parser.add_argument(
        '--to',
        dest='to_syntax',
        type=str,
        help='Target math syntax (latex, mathjax, ascii, unicode)'
    )
    
    parser.add_argument(
        '--input',
        dest='input_paths',
        type=str,
        nargs='*',
        default=[],
        help='Input file(s) or directory. Default: current directory. Supports PDF extraction.'
    )
    
    parser.add_argument(
        '--output',
        dest='output_file',
        type=str,
        help='Output file for PDF extraction (defaults to input name with .md extension)'
    )
    
    parser.add_argument(
        '--output-dir',
        dest='output_dir',
        type=str,
        help='Output directory for converted files'
    )
    
    parser.add_argument(
        '-Y',
        dest='auto_yes',
        action='store_true',
        help='Automatically answer yes to prompts'
    )
    
    parser.add_argument(
        '-N',
        dest='auto_no',
        action='store_true',
        help='Automatically answer no to prompts'
    )
    
    args = parser.parse_args()
    
    # Check if input is a PDF file
    processor = FileProcessor()
    
    if args.input_paths:
        input_path = Path(args.input_paths[0]) if args.input_paths else None
        
        # Handle PDF extraction
        if input_path and input_path.is_file() and processor.is_pdf_file(input_path):
            # PDF extraction mode
            output_path = None
            if args.output_file:
                output_path = Path(args.output_file)
            
            success = processor.process_pdf_extraction(input_path, output_path)
            sys.exit(0 if success else 1)
    
    # Standard conversion mode
    # Parse syntax types
    from_syntax = None
    to_syntax = None
    
    if args.from_syntax:
        try:
            from_syntax = SyntaxType.from_string(args.from_syntax)
        except ValueError:
            print(f"Error: Unknown syntax type '{args.from_syntax}'")
            print(f"Supported types: {', '.join(t.value for t in SyntaxType.all_types())}")
            sys.exit(1)
    
    if args.to_syntax:
        try:
            to_syntax = SyntaxType.from_string(args.to_syntax)
        except ValueError:
            print(f"Error: Unknown syntax type '{args.to_syntax}'")
            print(f"Supported types: {', '.join(t.value for t in SyntaxType.all_types())}")
            sys.exit(1)
    
    # Handle missing from/to with prompts
    if from_syntax is None and to_syntax is None:
        print("Error: At least one of --from or --to must be specified")
        sys.exit(1)
    
    # Handle missing --to
    if to_syntax is None:
        if args.auto_no:
            print("Error: --to flag is required (auto-no mode)")
            sys.exit(1)
        
        syntax_options = [t.value for t in SyntaxType.all_types() if t != from_syntax]
        to_syntax_str = prompt_user(
            "Select target syntax:",
            syntax_options,
            allow_cancel=True
        )
        
        if to_syntax_str is None:
            print("Conversion canceled.")
            sys.exit(0)
        
        to_syntax = SyntaxType.from_string(to_syntax_str)
    
    # Handle missing --from
    if from_syntax is None:
        if args.auto_no:
            print("Error: --from flag is required (auto-no mode)")
            sys.exit(1)
        
        all_types_str = ', '.join(t.value for t in SyntaxType.all_types())
        print(f"\nAll files with any of the following math types will be converted: {all_types_str}")
        
        if not args.auto_yes:
            should_specify = prompt_yes_no("Do you want to specify a source syntax?")
            
            if should_specify:
                syntax_options = [t.value for t in SyntaxType.all_types() if t != to_syntax]
                from_syntax_str = prompt_user(
                    "Select source syntax:",
                    syntax_options,
                    allow_cancel=True
                )
                
                if from_syntax_str is None:
                    print("Using auto-detect mode for all syntax types.")
                else:
                    from_syntax = SyntaxType.from_string(from_syntax_str)
        
        # If still None, default to LaTeX (most common)
        if from_syntax is None:
            from_syntax = SyntaxType.LATEX
            print(f"Defaulting to source syntax: {from_syntax.value}")
    
    # Create conversion request
    request = ConversionRequest(
        from_syntax=from_syntax,
        to_syntax=to_syntax,
        input_paths=args.input_paths,
        output_dir=args.output_dir,
        in_place=(args.output_dir is None),
        auto_yes=args.auto_yes,
        auto_no=args.auto_no
    )
    
    # Process files
    processor = FileProcessor()
    count = processor.process_files(request)
    
    print(f"\nConversion complete: {count} file(s) processed successfully.")
    
    if count == 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
