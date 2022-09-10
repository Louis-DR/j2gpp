# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     j2gpp - Jinja2-based General Purpose Preprocessor            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        utils.py                                                     ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Miscellaneous utility functions.                             ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



# ┌───────────────────────┐
# │ Drawing and messaging │
# └───────────────────────┘

# ANSI escape codes
ansi_codes = {
  'reset':      '\u001b[0m',
  'bold':       '\u001b[1m',
  'faint':      '\u001b[2m',
  'italic':     '\u001b[3m',
  'underline':  '\u001b[4m',
  'slowblink':  '\u001b[5m',
  'fastblink':  '\u001b[6m',
  'reversed':   '\u001b[7m',
  'concealed':  '\u001b[8m',
  'crossedout': '\u001b[9m',
  'black':      '\u001b[30m',
  'red':        '\u001b[31m',
  'green':      '\u001b[32m',
  'yellow':     '\u001b[33m',
  'blue':       '\u001b[34m',
  'magenta':    '\u001b[35m',
  'cyan':       '\u001b[36m',
  'white':      '\u001b[37m'
}

# Totally sick program header
def j2gpp_title():
  print(ansi_codes['bold'],end='')
  print("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
  print("┃     ╻┏━┓┏━┓┏━┓┏━┓  JINJA2-BASED      ┃")
  print("┃     ┃┏━┛┃╺┓┣━┛┣━┛  GENERAL-PURPOSE   ┃")
  print("┃   ┗━┛┗━╸┗━┛╹  ╹    PREPROCESSOR      ┃")
  print("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛")
  print(ansi_codes['reset'],end='')

# Cool looking headers
def throw_h1(text, min_width=40):
  width = max(min_width-2,len(text)+2)
  print(ansi_codes['bold'], end='')
  print('╔'+width*'═'+'╗')
  print('║',text.center(width-2),'║')
  print('╚'+width*'═'+'╝')
  print(ansi_codes['reset'], end='')

def throw_h2(text, min_width=40):
  width = max(min_width-2,len(text)+2)
  print(ansi_codes['bold'], end='')
  print('┏'+width*'━'+'┓')
  print('┃',text.center(width-2),'┃')
  print('┗'+width*'━'+'┛')
  print(ansi_codes['reset'], end='')

def throw_h3(text, min_width=40):
  width = max(min_width-2,len(text)+2)
  print('┌'+width*'─'+'┐')
  print('│',text.center(width-2),'│')
  print('└'+width*'─'+'┘')

# Cool looking messages
def throw_note(text):
  print(ansi_codes['blue']+ansi_codes['bold'], end='')
  print(f"NOTE:",text)
  print(ansi_codes['reset'], end='')

def throw_done(text):
  print(ansi_codes['green']+ansi_codes['bold'], end='')
  print(f"DONE:",text)
  print(ansi_codes['reset'], end='')

def throw_warning(text):
  print(ansi_codes['yellow']+ansi_codes['bold'], end='')
  print(f"WARNING:",text)
  print(ansi_codes['reset'], end='')

def throw_error(text):
  print(ansi_codes['red']+ansi_codes['bold'], end='')
  print(f"ERROR:",text)
  print(ansi_codes['reset'], end='')

def throw_fatal(text):
  print(ansi_codes['red']+ansi_codes['bold']+ansi_codes['reversed']+ansi_codes['slowblink'], end='')
  print(f"FATAL:",text)
  print(ansi_codes['reset'], end='')



# ┌─────────────────────┐
# │ Data and structures │
# └─────────────────────┘

# Tests if string can be cast into float
def str_isfloat(str):
  try:
    float(str)
    return True
  except ValueError:
    return False
