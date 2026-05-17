#!/usr/bin/env python3
"""Make tools directory runnable: python -m tools"""

import sys

TOOLS = {
    "extract": "Trigger LLM extraction on a source",
    "query": "Search and retrieve research data",
    "export": "Export research data in various formats",
}


def main():
    print("Northstar Research CLI Tools")
    print()
    for name, desc in TOOLS.items():
        print(f"  python tools/{name}.py --help")
        print(f"      {desc}")
    print()
    print("Usage: python tools/<tool>.py <args>")
    sys.exit(0)


if __name__ == "__main__":
    main()
