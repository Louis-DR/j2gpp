# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     j2gpp - Jinja2-based General Purpose Preprocessor            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        globals.py                                                   ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Additional useful global variables and functions.            ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



import os
from datetime import datetime
from platform import python_version

from jinja2 import __version__ as jinja2_version

from j2gpp.utils import (
  get_j2gpp_version,
  throw_warning,
)



extra_globals = {}



# Global context variables
try:                     extra_globals['__python_version__'] = python_version()
except Exception as exc: throw_warning(f"Could not set the context global variable '__python_version__'.")
try:                     extra_globals['__jinja2_version__'] = jinja2_version
except Exception as exc: throw_warning(f"Could not set the context global variable '__jinja2_version__'.")
try:                     extra_globals['__j2gpp_version__'] = get_j2gpp_version()
except Exception as exc: throw_warning(f"Could not set the context global variable '__j2gpp_version__'.")
try:                     extra_globals['__user__'] = os.getlogin()
except Exception as exc: throw_warning(f"Could not set the context global variable '__user__'.")
try:                     extra_globals['__pid__'] = os.getpid()
except Exception as exc: throw_warning(f"Could not set the context global variable '__pid__'.")
try:                     extra_globals['__ppid__'] = os.getppid()
except Exception as exc: throw_warning(f"Could not set the context global variable '__ppid__'.")
try:                     extra_globals['__working_directory__'] = os.getcwd()
except Exception as exc: throw_warning(f"Could not set the context global variable '__working_directory__'.")
try:                     extra_globals['__date__'] = datetime.now().strftime("%d-%m-%Y")
except Exception as exc: throw_warning(f"Could not set the context global variable '__date__'.")
try:                     extra_globals['__date_inv__'] = datetime.now().strftime("%Y-%m-%d")
except Exception as exc: throw_warning(f"Could not set the context global variable '__date_inv__'.")
try:                     extra_globals['__time__'] = datetime.now().strftime("%H:%M:%S")
except Exception as exc: throw_warning(f"Could not set the context global variable '__time__'.")
try:                     extra_globals['__datetime__'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
except Exception as exc: throw_warning(f"Could not set the context global variable '__datetime__'.")
