# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     j2gpp - Jinja2-based General Purpose Preprocessor            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        filters.py                                                   ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Additional useful filters.                                   ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



import math
import statistics
import re
import os
import errno
import itertools
from j2gpp.utils import *

extra_filters = {}



# ┌──────┐
# │ Math │
# └──────┘

# Load everything from libraries
def load_from_lib(lib):
  for function_name in dir(lib):
    if function_name[0] != '_':
      math_function = getattr(lib, function_name)
      if callable(math_function):
        extra_filters[function_name] = math_function
load_from_lib(math)
load_from_lib(statistics)

# List operations
extra_filters['list_add']  = lambda X,y : [x+y  for x in X]
extra_filters['list_sub']  = lambda X,y : [x-y  for x in X]
extra_filters['list_mult'] = lambda X,y : [x*y  for x in X]
extra_filters['list_div']  = lambda X,y : [x/y  for x in X]
extra_filters['list_mod']  = lambda X,y : [x%y  for x in X]
extra_filters['list_rem']  = lambda X,y : [x//y for x in X]
extra_filters['list_exp']  = lambda X,y : [x**y for x in X]



# ┌─────────────────────┐
# │ String manipulation │
# └─────────────────────┘

# Alignment
extra_filters['ljust']  = lambda s,l : str(s).ljust(l)
extra_filters['rjust']  = lambda s,l : str(s).rjust(l)
extra_filters['center'] = lambda s,l : str(s).center(l)

# Case
extra_filters['title']    = lambda s : str(s).title()
extra_filters['swapcase'] = lambda s : str(s).swapcase()

def camel(s, remove_underscore=True, remove_hyphen=True, remove_dot=False):
  if remove_underscore: s = s.replace('_', '')
  if remove_hyphen:     s = s.replace('-', '')
  if remove_dot:        s = s.replace('.', '')
  s = re.sub(r'[A-Z]', lambda m : m.group(0).lower() ,s,1)
  return s

def pascal(s, remove_underscore=True, remove_hyphen=True, remove_dot=False):
  if remove_underscore: s = s.replace('_', '')
  if remove_hyphen:     s = s.replace('-', '')
  if remove_dot:        s = s.replace('.', '')
  s = re.sub(r'[a-z]', lambda m : m.group(0).upper() ,s,1)
  return s

extra_filters['camel']  = camel
extra_filters['pascal'] = pascal

re_caps_boundary       = re.compile(r'(?<!^)(?=[A-Z])')
re_caps_boundary_group = re.compile(r'(?<!^)(?<![A-Z])(?=[A-Z])')

def snake(s, preserve_caps=True, group_caps=True):
  if group_caps: s = re_caps_boundary_group.sub('_', s)
  else: s = re_caps_boundary.sub('_', s)
  if not preserve_caps: s = s.lower()
  return s

def kebab(s, preserve_caps=True, group_caps=True):
  if group_caps: s = re_caps_boundary_group.sub('-', s)
  else: s = re_caps_boundary.sub('-', s)
  if not preserve_caps: s = s.lower()
  return s

extra_filters['snake'] = snake
extra_filters['kebab'] = kebab



# ┌──────────────────────┐
# │ Paragraph formatting │
# └──────────────────────┘

# Removes pre-existing indentation and sets new one
def reindent(content, depth=1, spaces=2, tabs=False, first=False, blank=False):
  indent = depth * ('\t' if tabs else ' '*spaces)
  is_first = True

  # Iterate line by line
  lines = content.split('\n')
  for idx,line in enumerate(lines):

    # First line skipped according to argument
    if is_first and not first:
      is_first = False
      continue

    # Update the line with the correct indentation
    line = line.lstrip()
    if line != '' and not blank:
      line = indent + line
    lines[idx] = line

  # Return paragraph of lines
  return '\n'.join(lines)

extra_filters['reindent'] = reindent


# Removes pre-existing indentation and sets new indent based on rules
def autoindent(content, starts=['{'], ends=['}'], spaces=2, tabs=False, first=False, blank=False):
  is_first = True
  depth = 0
  next_depth = 0

  # Iterate line by line
  lines = content.split('\n')
  for idx,line in enumerate(lines):
    depth = next_depth

    # First line
    if is_first:
      is_first = False

      # Count the indentation of the first line
      if tabs:
        line_strip = line.lstrip('\t')
        depth = len(line) - len(line_strip)
      else:
        line_strip = line.lstrip(' ')
        depth = math.ceil((len(line) - len(line_strip)) / spaces)

      next_depth = depth
      for start in starts:
        next_depth += line.count(start)

      # Skip first line according to argument
      if not first:
        continue

    # Updated the depth information based on block delimiters
    for end in ends:
      depth -= line.count(end)
    next_depth = depth
    for start in starts:
      next_depth += line.count(start)

    # Update the line with the correct indentation
    line = line.lstrip()
    indent = depth * ('\t' if tabs else ' '*spaces)
    if line != '' and not blank:
      line = indent + line
    lines[idx] = line

  # Return paragraph of lines
  return '\n'.join(lines)

extra_filters['autoindent'] = autoindent


# Align every line of the paragraph, left before §, right before §§
def align(content, margin=1):
  lines = content.split('\n')

  # First split the line by column and measure the width of the columns
  lines_objs = []
  columns_widths = []
  for line in lines:
    line_obj = []
    column_idx = 0
    # First split at the right align boundaries
    line_split_rjust = line.split('§§')
    for rjust_idx, text_rjust in enumerate(line_split_rjust):
      # Then split at the left align boundaries
      text_rjust_split_ljust = text_rjust.split('§')
      for ljust_idx, text in enumerate(text_rjust_split_ljust):
        # Preserve the indentation of the line
        if column_idx == 0:
          text = text.rstrip()
        else:
          text = text.strip()
        # Build object with dict for each column
        if ljust_idx == len(text_rjust_split_ljust)-1 and rjust_idx != len(line_split_rjust)-1:
          line_obj.append({
            'text': text,
            'just': 'right'
          })
        else:
          line_obj.append({
            'text': text,
            'just': 'left'
          })
        # Lines without alignment do not affect column width
        if len(line_split_rjust) + len(text_rjust_split_ljust) > 2:
          # Update the column widths
          column_width = len(text)
          if column_idx == len(columns_widths):
            columns_widths.append(column_width)
          else:
            columns_widths[column_idx] = max(columns_widths[column_idx], column_width)
        column_idx += 1
    lines_objs.append(line_obj)

  # Then apply the alignment to all the lines
  lines = []
  for line_idx,line_obj in enumerate(lines_objs):
    line = ""
    for column_idx, column in enumerate(line_obj):
      column_width = columns_widths[column_idx]
      column_text = column['text']
      column_just = column['just']
      if column_idx == len(line_obj)-1:
        line += column_text
      elif column_just == 'left':
        line += column_text.ljust(column_width)
      else:
        line += column_text.rjust(column_width)
      if column_idx != len(line_obj)-1:
        line += ' '*margin
    lines.append(line)

  # Return paragraph of lines
  return '\n'.join(lines)

extra_filters['align'] = align



# ┌─────────────────────┐
# │ Dictionary and list │
# └─────────────────────┘

# Element max and min based on sub attribute
extra_filters['el_of_max_attr'] = lambda L,attr : max(L, key = lambda el : el[attr])
extra_filters['el_of_min_attr'] = lambda L,attr : min(L, key = lambda el : el[attr])

# Key of max and min based on sub attribute
extra_filters['key_of_max_attr'] = lambda d,attr : max(d, key = lambda key : d[key][attr])
extra_filters['key_of_min_attr'] = lambda d,attr : min(d, key = lambda key : d[key][attr])

# Accumulate elements of integer/float list
extra_filters['accumulate'] = lambda L : itertools.accumulate(L)

# Count occurences in list
extra_filters['count'] = lambda L,x : sum([l==x for l in L])



# ┌───────────────┐
# │ Combinatorial │
# └───────────────┘

# Generators from itertools
extra_filters['pairwise']                      = lambda L        : itertools.pairwise(L)
extra_filters['product']                       = lambda L        : itertools.product(L)
extra_filters['permutations']                  = lambda L,r=None : itertools.permutations(L,r)
extra_filters['combinations']                  = lambda L,r      : itertools.combinations(L,r)
extra_filters['combinations_with_replacement'] = lambda L,r      : itertools.combinations_with_replacement(L,r)

# Generators with range of lengths
extra_filters['permutations_range']                  = lambda L,start,stop : itertools.chain(*[itertools.permutations(L,x)                  for x in range(start,stop)])
extra_filters['combinations_range']                  = lambda L,start,stop : itertools.chain(*[itertools.combinations(L,x)                  for x in range(start,stop)])
extra_filters['combinations_with_replacement_range'] = lambda L,start,stop : itertools.chain(*[itertools.combinations_with_replacement(L,x) for x in range(start,stop)])



# ┌─────────────┐
# │ File output │
# └─────────────┘

# Flag to skip rendering source template according to export filter option
write_source_toggle = [True]

# Write content of the block to a file
def write(content, path, preserve=False, write_source=True):
  # Skip source template according to argument option
  global write_source_toggle
  write_source_toggle[0] = write_source_toggle[0] and write_source

  # Get full path
  path = os.path.expandvars(os.path.expanduser(os.path.abspath(path)))
  print(f"Exporting block content to {path}")

  # Create directories for output path
  dirpath = os.path.dirname(path)
  try:
    os.makedirs(dirpath, exist_ok=True)
  except OSError as exc:
      throw_error(f"Cannot create directory '{dirpath}' to export block.")

  # Write to file
  try:
    with open(path,'w') as file:
      file.write(content)
  except OSError as exc:
    # Catch file write exceptions
    if exc.errno == errno.EISDIR:
      throw_error(f"Cannot write '{path}' : path is a directory.")
    elif exc.errno == errno.EACCES:
      throw_error(f"Cannot write '{path}' : missing write permission.")
    else:
      throw_error(f"Cannot write '{path}'.")

  # Replacement in original file
  if preserve:
    return content
  else:
    return ""

extra_filters['write'] = write


# Append content of the block to a file
def append(content, path, preserve=False, write_source=True):
  # Skip source template according to argument option
  global write_source_toggle
  write_source_toggle[0] = write_source_toggle[0] and write_source

  # Get full path
  path = os.path.expandvars(os.path.expanduser(os.path.abspath(path)))
  print(f"Exporting block content to {path}")

  # Create directories for output path
  dirpath = os.path.dirname(path)
  try:
    os.makedirs(dirpath, exist_ok=True)
  except OSError as exc:
      throw_error(f"Cannot create directory '{dirpath}' to export block.")

  # Append to file
  try:
    with open(path,'a') as file:
      file.write(content)
  except OSError as exc:
    # Catch file write exceptions
    if exc.errno == errno.EISDIR:
      throw_error(f"Cannot write '{path}' : path is a directory.")
    elif exc.errno == errno.EACCES:
      throw_error(f"Cannot write '{path}' : missing write permission.")
    else:
      throw_error(f"Cannot write '{path}'.")

  # Replacement in original file
  if preserve:
    return content
  else:
    return ""

extra_filters['append'] = append
