# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     j2gpp - Jinja2-based General Purpose Preprocessor            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        tests.py                                                     ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Additional useful tests.                                     ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



extra_tests = {}



# ┌──────┐
# │ Text │
# └──────┘

extra_tests['decimal']    = lambda s : str(s).isdecimal()
extra_tests['digit']      = lambda s : str(s).isdigit()
extra_tests['numeric']    = lambda s : str(s).isnumeric()

extra_tests['alpha']      = lambda s : str(s).isalpha()
extra_tests['alnum']      = lambda s : str(s).isalnum()
extra_tests['identifier'] = lambda s : str(s).isidentifier()

extra_tests['space']      = lambda s : str(s).isspace()
extra_tests['lower']      = lambda s : str(s).islower()
extra_tests['upper']      = lambda s : str(s).isupper()
extra_tests['title']      = lambda s : str(s).istitle()
extra_tests['printable']  = lambda s : str(s).isprintable()
