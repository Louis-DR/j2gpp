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
extra_filters['ljust']  = lambda s,l : str(s).rjust(l)
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



# ┌─────────────────────┐
# │ Dictionary and list │
# └─────────────────────┘

# Element max and min based on sub attribute
extra_filters['el_of_max_attr'] = lambda L,attr : max(L, key = lambda el : el[attr])
extra_filters['el_of_min_attr'] = lambda L,attr : min(L, key = lambda el : el[attr])

# Key of max and min based on sub attribute
extra_filters['key_of_max_attr'] = lambda d,attr : max(d, key = lambda key : d[key][attr])
extra_filters['key_of_min_attr'] = lambda d,attr : min(d, key = lambda key : d[key][attr])

# Count occurences in list
extra_filters['count'] = lambda L,x : sum([l==x for l in L])
