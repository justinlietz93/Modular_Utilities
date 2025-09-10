"""HTML -> Markdown converter plugin (simple heuristic, no config file)."""

import os
import re
from ..conversion_registry import register
from .. import html_to_markdown

class HtmlToMarkdownConverter:
    from_fmt = 'html'
    to_fmt = 'md'
    name = 'html_md_default'

    link_re = re.compile(r'\[[^\]]+\]\([^\)]+\)')
    user_patterns_env = os.getenv('CODE_CRAWLER_STRIP_PATTERNS','').strip()
    user_patterns = [re.compile(p, re.IGNORECASE) for p in user_patterns_env.split(';;') if p]

    def can_handle(self, path: str, ext: str) -> bool:  # pragma: no cover (trivial)
        return ext.lower() in ('html','htm')

    def _is_nav_line(self, line: str) -> bool:
        ls = line.strip()
        if not ls:
            return False
        link_count = len(self.link_re.findall(ls))
        if link_count >= 3:
            return True
        if any(sep in ls for sep in ('>>','›',' / ')) and link_count >= 2:
            return True
        low = ls.lower()
        if low.startswith('expand all') or low.startswith('collapse all'):
            return True
        for pat in self.user_patterns:
            if pat.search(ls):
                return True
        return False

    def _filter_lines(self, md: str) -> str:
        out = []
        prev_blank = False
        for raw in md.splitlines():
            if self._is_nav_line(raw):
                continue
            if raw.strip() == '':
                if prev_blank:
                    continue
                prev_blank = True
                out.append('')
            else:
                prev_blank = False
                out.append(raw.rstrip())
        while out and out[0] == '':
            out.pop(0)
        while out and out[-1] == '':
            out.pop()
        return '\n'.join(out).rstrip() + '\n'

    def convert(self, text: str, path: str) -> str:
        md = html_to_markdown.convert_html_to_markdown(text)
        return self._filter_lines(md)

register(HtmlToMarkdownConverter())

__all__ = ['HtmlToMarkdownConverter']
