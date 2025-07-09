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
import sys
import importlib.util
import importlib.machinery
from importlib.metadata import version



# ┌───────────────┐
# │ J2GPP version │
# └───────────────┘

def get_j2gpp_version():
  try:
    return version('j2gpp')
  except Exception:
    return "error"



# ┌───────────────────┐
# │ Importing modules │
# └───────────────────┘

def load_module(module_name, file_path):
  loader = importlib.machinery.SourceFileLoader(module_name, file_path)
  spec   = importlib.util.spec_from_file_location(module_name, file_path, loader=loader)
  module = importlib.util.module_from_spec(spec)
  sys.modules[module.__name__] = module
  loader.exec_module(module)
  return module



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
  print(ansi_codes['reset'], end='')
  print(ansi_codes['bold'], end='')
  print('╔'+width*'═'+'╗')
  print('║',text.center(width-2),'║')
  print('╚'+width*'═'+'╝')
  print(ansi_codes['reset'], end='')

def throw_h2(text, min_width=40):
  width = max(min_width-2,len(text)+2)
  print(ansi_codes['reset'], end='')
  print(ansi_codes['bold'], end='')
  print('┏'+width*'━'+'┓')
  print('┃',text.center(width-2),'┃')
  print('┗'+width*'━'+'┛')
  print(ansi_codes['reset'], end='')

def throw_h3(text, min_width=40):
  width = max(min_width-2,len(text)+2)
  print(ansi_codes['reset'], end='')
  print('┌'+width*'─'+'┐')
  print('│',text.center(width-2),'│')
  print('└'+width*'─'+'┘')

# Error and warning accumulators
warnings = []
errors   = []

# Global setting for error output stream (set by main script)
errors_output_stream = sys.stderr
def set_errors_output_stream(stream):
  global errors_output_stream
  errors_output_stream = stream

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
  print(ansi_codes['red']+ansi_codes['bold'], end='', file=errors_output_stream)
  print(f"ERROR:",text, file=errors_output_stream)
  print(ansi_codes['reset'], end='', file=errors_output_stream)

def throw_fatal(text):
  global errors
  errors.append(text)
  print(ansi_codes['red']+ansi_codes['bold']+ansi_codes['reversed']+ansi_codes['slowblink'], end='', file=errors_output_stream)
  print(f"FATAL:",text, file=errors_output_stream)
  print(ansi_codes['reset'], end='', file=errors_output_stream)

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

Copyright (c) 2022-2024 Louis Duret-Robert

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

# Flatten to shallow list, keep only values for dictionaries
def flatten(a):
  return [c for b in a.values() for c in flatten(b) if c is not None] if isinstance(a,dict) else [c for b in a for c in flatten(b) if c is not None]


# ┌─────────────────────┐
# │ Variable processing │
# └─────────────────────┘

def var_dict_update(var_dict1, var_dict2, val_scope="", context=""):
  """Merge two dictionaries with conflict resolution and warnings"""
  var_dict_res = var_dict1.copy()
  for key, val in var_dict2.items():
    # Conflict
    if key in var_dict1.keys() and var_dict1[key] != val:
      val_ori = var_dict1[key]
      # Recursively merge dictionary
      if isinstance(val_ori, dict) and isinstance(val, dict):
        val_scope = f"{val_scope}{key}."
        var_dict_res[key] = var_dict_update(val_ori, val, val_scope, context)
      # Special case: try to merge dict into string that looks like a dictionary
      elif isinstance(val_ori, str) and isinstance(val, dict) and val_ori.strip().startswith('{') and val_ori.strip().endswith('}'):
        # Try to parse the string as a dictionary with more flexible parsing
        try:
          # First, try standard ast.literal_eval
          parsed_dict = ast.literal_eval(val_ori)
          if isinstance(parsed_dict, dict):
            var_dict_res[key] = var_dict_update(parsed_dict, val, val_scope, context)
          else:
            var_dict_res[key] = val
            throw_warning(f"Variable '{val_scope}{key}' got overwritten from '{val_ori}' to '{val}'{context}.")
        except (ValueError, SyntaxError):
          # Convert JSON-style syntax to Python syntax and try again
          try:
            # Convert JSON booleans and null to Python equivalents
            json_to_python = val_ori.replace('true', 'True').replace('false', 'False').replace('null', 'None')
            parsed_dict = ast.literal_eval(json_to_python)
            if isinstance(parsed_dict, dict):
              var_dict_res[key] = var_dict_update(parsed_dict, val, val_scope, context)
            else:
              var_dict_res[key] = val
              throw_warning(f"Variable '{val_scope}{key}' got overwritten from '{val_ori}' to '{val}'{context}.")
          except (ValueError, SyntaxError):
            # If that fails, try a more flexible approach for unquoted values
            try:
              # Replace unquoted words with quoted strings (improved heuristic)
              import re
              fixed_str = val_ori
              # Convert JSON syntax first
              fixed_str = fixed_str.replace('true', 'True').replace('false', 'False').replace('null', 'None')
              # Handle single-quoted keys with unquoted values
              fixed_str = re.sub(r"'([^']*)':\s*([a-zA-Z_][a-zA-Z0-9_]*)", r"'\1': '\2'", fixed_str)
              # Handle double-quoted keys with unquoted values
              fixed_str = re.sub(r'"([^"]*)":\s*([a-zA-Z_][a-zA-Z0-9_]*)', r'"\1": "\2"', fixed_str)
              # Handle unquoted keys with unquoted values
              fixed_str = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*):\s*([a-zA-Z_][a-zA-Z0-9_]*)', r'"\1": "\2"', fixed_str)
              # Don't quote numbers, booleans, or null
              fixed_str = re.sub(r':\s*"(\d+(?:\.\d+)?)"', r': \1', fixed_str)  # Numbers
              fixed_str = re.sub(r':\s*"(True|False|None)"', r': \1', fixed_str)  # Python booleans and None
              parsed_dict = ast.literal_eval(fixed_str)
              if isinstance(parsed_dict, dict):
                var_dict_res[key] = var_dict_update(parsed_dict, val, val_scope, context)
              else:
                var_dict_res[key] = val
                throw_warning(f"Variable '{val_scope}{key}' got overwritten from '{val_ori}' to '{val}'{context}.")
            except (ValueError, SyntaxError):
              # If all parsing fails, just overwrite with warning
              var_dict_res[key] = val
              throw_warning(f"Variable '{val_scope}{key}' got overwritten from '{val_ori}' to '{val}'{context}.")
      else:
        var_dict_res[key] = val
        throw_warning(f"Variable '{val_scope}{key}' got overwritten from '{val_ori}' to '{val}'{context}.")
    else:
      var_dict_res[key] = val
  return var_dict_res

def rec_check_valid_identifier(var_dict, context_file=None, val_scope=""):
  """Check that attributes names are valid Python identifier that can be accessed in Jinja2"""
  for key, val in var_dict.copy().items():
    # Valid identifier contains only alphanumeric letters and underscores, and cannot start with a number
    if not key.isidentifier():
      # Note: fix_identifiers option would be handled by caller
      throw_warning(f"Variable '{val_scope}{key}' from '{context_file}' is not a valid Python identifier and may not be accessible in the templates.")
    if isinstance(val, dict):
      val_scope_new = f"{val_scope}{key}."
      # Traverse the dictionary recursively
      rec_check_valid_identifier(var_dict[key], context_file, val_scope_new)



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
  typ, value, tb = sys.exc_info()
  # Iterate over nested traceback frames
  while tb:
    # Parse traceback frame string
    tb_frame_str = str(tb.tb_frame)
    tb_frame_match = tb_frame_re.match(tb_frame_str)
    # If we include non-templates, then we don't reset the flag
    if not including_non_template: tb_frame_isj2gpp = False
    # Identify frames corresponding to Jinja2 templates
    if tb.tb_frame.f_code.co_filename in ['<template>', '<unknown>']:
      # Top-most template
      tb_src_path = src_path
      tb_lineno = tb.tb_lineno
      tb_frame_isj2gpp = True
    elif tb_frame_match and (tb_frame_match.group(3) or tb_frame_isj2gpp):
      # Nested child templates
      tb_src_path = tb_frame_match.group(1)
      tb_lineno   = tb_frame_match.group(2)
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
