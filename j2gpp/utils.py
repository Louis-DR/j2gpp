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



import time
import ast
import os
import errno



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

# Error and warning accumulators
warnings = []
errors = []

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
  global warnings
  warnings.append(text)
  print(ansi_codes['yellow']+ansi_codes['bold'], end='')
  print(f"WARNING:",text)
  print(ansi_codes['reset'], end='')

def throw_error(text):
  global errors
  errors.append(text)
  print(ansi_codes['red']+ansi_codes['bold'], end='')
  print(f"ERROR:",text)
  print(ansi_codes['reset'], end='')

def throw_fatal(text):
  print(ansi_codes['red']+ansi_codes['bold']+ansi_codes['reversed']+ansi_codes['slowblink'], end='')
  print(f"FATAL:",text)
  print(ansi_codes['reset'], end='')

def error_warning_summary():
  print("Warnings:", ansi_codes['yellow']+ansi_codes['bold']+ansi_codes['reversed'], len(warnings), ansi_codes['reset'],
        "Errors:",   ansi_codes['red']   +ansi_codes['bold']+ansi_codes['reversed'], len(errors),   ansi_codes['reset'])
  print(ansi_codes['yellow']+ansi_codes['bold'], end='')
  for warning in warnings:
    print(f"WARNING:",warning)
  print(ansi_codes['reset'], end='')
  print(ansi_codes['red']+ansi_codes['bold'], end='')
  for error in errors:
    print(f"ERROR:",error)
  print(ansi_codes['reset'], end='')
  print("Warnings:", ansi_codes['yellow']+ansi_codes['bold']+ansi_codes['reversed'], len(warnings), ansi_codes['reset'],
        "Errors:",   ansi_codes['red']   +ansi_codes['bold']+ansi_codes['reversed'], len(errors),   ansi_codes['reset'])

# Intend block of text
def intend_text(text):
  return "  "+str(text).replace('\n','\n  ')

# Print license
def print_license():
  print("""J2GPP is under MIT License

Copyright (c) 2022 Louis Duret-Robert

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.""")



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

# Cast to Python type according to syntax
def auto_cast_str(val):
  try:
    val = ast.literal_eval(val)
  except:
    pass
  return val



# ┌─────────────┐
# │ Performance │
# └─────────────┘

def perf_counter_start():
  return time.process_time_ns()

def perf_counter_stop(start_time):
  stop_time = time.process_time_ns()
  return stop_time - start_time

def perf_counter_print(counter_time):
  print(f"Execution time : {counter_time}ns")



# ┌───────────────────────┐
# │ Files and directories │
# └───────────────────────┘

# Change working directory with exception handling
def change_working_directory(dir_path):
  try:
    os.chdir(dir_path)
  except OSError as exc:
    if exc.errno == errno.ENOENT:
      throw_error(f"Cannot change working directory to '{dir_path}' : directory doesn't exist.")
    elif exc.errno == errno.EACCES:
      throw_error(f"Cannot change working directory to '{dir_path}' : missing permissions.")
    else:
      throw_error(f"Cannot change working directory to '{dir_path}'.")
