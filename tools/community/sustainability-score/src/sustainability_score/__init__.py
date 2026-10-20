"""GSF-grounded static sustainability score for code repositories."""
from .scanner import scan
from .report import to_json, to_markdown

__version__ = "0.1.0"
__all__ = ["scan", "to_json", "to_markdown"]
