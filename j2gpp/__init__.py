# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     j2gpp - Jinja2-based General Purpose Preprocessor            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        __init__.py                                                  ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Public API for J2GPP.                                        ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



# Main programmatic API
from j2gpp.engine import J2GPP, render_template
from j2gpp.results import RenderResult, FileRenderResult

# Core functions for advanced use
from j2gpp.core import render_template_string

# CLI entry point (for backward compatibility)
from j2gpp.j2gpp import main

# Version information
from j2gpp.utils import get_j2gpp_version



__version__ = get_j2gpp_version()

__all__ = [
  'J2GPP',
  'RenderResult',
  'FileRenderResult',
  'render_template',
  'render_template_string',
  'main',
  '__version__'
]

if __name__ == '__main__':
  main()
