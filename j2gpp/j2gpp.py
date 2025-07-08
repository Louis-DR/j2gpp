# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     j2gpp - Jinja2-based General Purpose Preprocessor            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        j2gpp.py                                                     ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Legacy main entry point - now imports from cli module.       ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



# Import the main function from the CLI module
from j2gpp.cli import main



# For backward compatibility, expose main at module level
__all__ = ['main']
