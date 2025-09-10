"""Lightweight HTML -> Markdown converter used by the code crawler.

The goal here is NOT to be perfect, but to:
  * Extract meaningful textual content from HTML (body) while ignoring
    layout / navigation / script / style noise.
  * Preserve basic structure (titles, headings, lists, code, links, images).
  * Produce clean, LLM-friendly markdown without inline styling cruft.

No third‑party dependencies are used (BeautifulSoup, markdownify, etc.) to
keep the crawler self‑contained. If higher fidelity becomes necessary,
we can swap this module behind the same function signature.
"""

from html.parser import HTMLParser
from typing import List, Tuple
import re

BLOCK_TAGS = {
    'p','div','section','article','main','header','footer','aside','nav','ul','ol',
    'li','pre','code','blockquote','h1','h2','h3','h4','h5','h6','br','hr','table',
    'tr','td','th'
}

SKIP_CONTENT_TAGS = {'script','style','noscript'}
IGNORE_STRUCTURE_TAGS = {'nav','footer','header','aside'}  # We just skip their content.

HEADING_TAGS = {f'h{i}': i for i in range(1,7)}

def _collapse_whitespace(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()

class _HTMLToMarkdownParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out: List[str] = []
        self.list_stack: List[Tuple[str,int]] = []  # (type, indent_level)
        self.skip_depth = 0
        self.in_pre = False
        self.current_link = None  # (href, text_buffer_index)
        self.title: str | None = None
        self.capture_title = False

    # --- Helpers ---------------------------------------------------------
    def _newline(self, ensure: bool = True):
        if ensure:
            if not self.out or self.out[-1] != '\n':
                self.out.append('\n')
        else:
            self.out.append('\n')

    def _append_text(self, text: str):
        if not text:
            return
        if self.in_pre:
            self.out.append(text)
            return
        cleaned = _collapse_whitespace(text)
        if not cleaned:
            return
        # If previous char not whitespace, prepend space when needed
        if self.out and not self.out[-1].endswith((' ','\n')):
            self.out.append(' ' + cleaned)
        else:
            self.out.append(cleaned)

    # --- HTMLParser Overrides -------------------------------------------
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == 'title':
            self.capture_title = True
        if tag in SKIP_CONTENT_TAGS or tag in IGNORE_STRUCTURE_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return

        attr_dict = {k.lower(): v for k,v in attrs}
        if tag in HEADING_TAGS:
            self._newline()
            level = HEADING_TAGS[tag]
            self.out.append('#'*level + ' ')
        elif tag == 'br':
            self.out.append('  \n')
        elif tag in ('p','div','section','article','main','blockquote'):
            self._newline()
        elif tag in ('ul','ol'):
            self.list_stack.append((tag, len(self.list_stack)))
            self._newline()
        elif tag == 'li':
            self._newline()
            indent = '  ' * len(self.list_stack)
            bullet = '-' if not self.list_stack or self.list_stack[-1][0]=='ul' else '1.'
            self.out.append(f"{indent}{bullet} ")
        elif tag == 'pre':
            self._newline()
            self.out.append("```\n")
            self.in_pre = True
        elif tag == 'code' and not self.in_pre:
            self.out.append('`')
        elif tag == 'a':
            href = attr_dict.get('href','')
            self.current_link = (href, len(self.out))
            self.out.append('[')
        elif tag == 'img':
            alt = attr_dict.get('alt','')
            src = attr_dict.get('src','')
            if src:
                self._newline()
                self.out.append(f"![{_collapse_whitespace(alt)}]({src})\n")
        elif tag == 'hr':
            self._newline()
            self.out.append("\n---\n")
        elif tag in ('strong','b'):
            self.out.append('**')
        elif tag in ('em','i'): 
            self.out.append('*')

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == 'title':
            self.capture_title = False
        if tag in SKIP_CONTENT_TAGS or tag in IGNORE_STRUCTURE_TAGS:
            if self.skip_depth:
                self.skip_depth -= 1
            return
        if self.skip_depth:
            return

        if tag in HEADING_TAGS:
            self._newline()
        elif tag in ('p','div','section','article','main','blockquote'):
            self._newline()
        elif tag in ('ul','ol'):
            if self.list_stack:
                self.list_stack.pop()
            self._newline()
        elif tag == 'pre':
            if self.in_pre:
                self.out.append('\n```\n')
                self.in_pre = False
            self._newline()
        elif tag == 'code' and not self.in_pre:
            self.out.append('`')
        elif tag == 'a':
            if self.current_link:
                href, idx = self.current_link
                self.out.append(']')
                if href:
                    self.out.append(f'({href})')
                self.current_link = None
        elif tag in ('strong','b'):
            self.out.append('**')
        elif tag in ('em','i'): 
            self.out.append('*')

    def handle_data(self, data):
        if self.skip_depth:
            return
        if self.capture_title:
            title_text = _collapse_whitespace(data)
            if title_text:
                self.title = (self.title or '') + title_text
        self._append_text(data)

    def handle_entityref(self, name):
        self.out.append(f"&{name};")

    def handle_charref(self, name):
        self.out.append(f"&#{name};")

def convert_html_to_markdown(html: str) -> str:
    """Convert HTML to simplified markdown.

    Strategy:
      * Parse, ignoring script/style/nav/etc.
      * Collect a <title> (if any) and emit it as first H1 if not already present.
      * Normalize consecutive blank lines to a single blank line.
    """
    parser = _HTMLToMarkdownParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        # Fallback: naive strip of tags
        text = re.sub(r'<[^>]+>', ' ', html)
        text = _collapse_whitespace(text)
        return text + '\n'

    md = ''.join(parser.out)
    # Ensure first heading present
    if parser.title and not re.search(r'^# ', md.strip()):
        md = f"# {parser.title}\n\n" + md.lstrip()

    # Cleanup: collapse excessive blank lines
    md = re.sub(r'\n{3,}', '\n\n', md)
    md = md.strip() + '\n'
    return md

__all__ = ["convert_html_to_markdown"]
