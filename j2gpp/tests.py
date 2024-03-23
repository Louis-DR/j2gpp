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



from jinja2.tests import test_defined



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



# ┌──────┐
# │ List │
# └──────┘

extra_tests['empty']     = lambda l : len(l) == 0
extra_tests['singleton'] = lambda l : len(l) == 1



# ┌──────┐
# │ Type │
# └──────┘

extra_tests['list'] = lambda x : isinstance(x,list)
extra_tests['dict'] = lambda x : isinstance(x,dict)



# ┌───────────┐
# │ Attribute │
# └───────────┘

extra_tests['defined_and_true']  = lambda x   : test_defined(x) and x
extra_tests['defined_and_false'] = lambda x   : test_defined(x) and not x
extra_tests['defined_and_eq']    = lambda x,y : test_defined(x) and x == y
extra_tests['defined_and_ne']    = lambda x,y : test_defined(x) and x != y
extra_tests['defined_and_lt']    = lambda x,y : test_defined(x) and x <  y
extra_tests['defined_and_le']    = lambda x,y : test_defined(x) and x <= y
extra_tests['defined_and_gt']    = lambda x,y : test_defined(x) and x >  y
extra_tests['defined_and_ge']    = lambda x,y : test_defined(x) and x >= y
