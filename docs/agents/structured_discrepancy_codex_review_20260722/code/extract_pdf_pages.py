#!/usr/bin/env python3
"""Print page-numbered PDF text for pages matching any supplied regex."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from pypdf import PdfReader


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("patterns", nargs="+")
    args = parser.parse_args()

    regexes = [re.compile(pattern, re.IGNORECASE) for pattern in args.patterns]
    reader = PdfReader(str(args.pdf))
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if any(regex.search(text) for regex in regexes):
            print(f"\n===== PDF PAGE {page_number} =====\n")
            print(text)


if __name__ == "__main__":
    main()
