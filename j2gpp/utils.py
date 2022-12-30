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
import re
import errno
from sys import exc_info



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



# ┌────────────────┐
# │ Error handling │
# └────────────────┘

# Return pretty traceback string of Jinja2 render
tb_frame_re = re.compile(r"<frame at 0x[a-z0-9]*, file '(.*)', line (\d+), (?:(code top-level template code|code template|code block '.*')|.*)>")
def jinja2_render_traceback(src_path, including_non_template=False):
  traceback_print = ""
  tb_frame_isj2gpp = False
  # Get traceback objects
  typ, value, tb = exc_info()
  # Iterate over nested traceback frames
  while tb:
    # Parse traceback frame string
    tb_frame_str = str(tb.tb_frame)
    tb_frame_match = tb_frame_re.match(tb_frame_str)
    # If we include non-templates, then we don't reset the flag
    if not including_non_template: tb_frame_isj2gpp = False
    # Identify frames corresponding to Jinja2 templates
    if tb.tb_frame.f_code.co_filename == '<template>':
      # Top-most template
      tb_src_path = src_path
      tb_lineno = tb.tb_lineno
      tb_frame_isj2gpp = True
    elif tb_frame_match and (tb_frame_match.group(3) or tb_frame_isj2gpp):
      # Nested child templates
      tb_src_path = tb_frame_match.group(1)
      tb_lineno = tb_frame_match.group(2)
      tb_frame_isj2gpp = True
    # Factorized string formatting
    if tb_frame_isj2gpp:
      traceback_print += f"  File '{tb_src_path}', line {tb_lineno}\n"
      # Fetch the line raising the exception
      with open(tb_src_path,'r') as tb_src_file:
        for lineno,line in enumerate(tb_src_file):
          if lineno == int(tb_lineno)-1:
            traceback_print += "    "+line.strip()+"\n"
            break
    tb = tb.tb_next
  # Strip the final line jump
  return traceback_print[:-1]
