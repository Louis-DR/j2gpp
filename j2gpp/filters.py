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
import hashlib
import zlib
import dataclasses
import datetime
import json
import re
import os
import errno
import itertools
from j2gpp.utils import *



# If using fork of Jinja2, then import the render_time_only decorator
try: from jinja2.utils import render_time_only
except ImportError:
  def render_time_only(func):
    def decorated(*args, **kwargs):
      throw_warning(f"The installed Jinja2 library doesn't support the @render_time_only decorator. The function {func.__name__} may get executed regarless of conditional block.")
      return func(*args, **kwargs)
    return decorated



extra_filters = {}



# ┌─────────────────────┐
# │ Warnings and errors │
# └─────────────────────┘

@render_time_only
def filter_warning(text):
  throw_warning(text)
  return ""
extra_filters['warning'] = filter_warning

@render_time_only
def filter_error(text):
  throw_error(text)
  return ""
extra_filters['error'] = filter_error



# ┌───────────────────┐
# │ Casting and types │
# └───────────────────┘

extra_filters['type'] = lambda x : type(x).__name__



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



# ┌────────────────────────┐
# │ Binary and other bases │
# └────────────────────────┘

extra_filters['bin'] = lambda x,l=0 : bin(x)[2:].rjust(l,'0')
extra_filters['hex'] = lambda x,l=0 : hex(x)[2:].rjust(l,'0')
extra_filters['oct'] = lambda x,l=0 : oct(x)[2:].rjust(l,'0')

def int_to_duodecimal(value, length=0, ten='a', eleven='b'):
  digits = []
  while value > 0:
    remainder = value % 12
    if remainder < 10:
      digits.append(str(remainder))
    elif remainder == 10:
      digits.append(ten)
    else:
      digits.append(eleven)
    value //= 12
  if not digits:
    digits.append('0')
  duodecimal_string = ''.join(reversed(digits))
  return duodecimal_string.rjust(length, '0')

extra_filters['duodecimal'] = int_to_duodecimal
extra_filters['doz'] = int_to_duodecimal



# ┌───────────────────────┐
# │ Hash and cryptography │
# └───────────────────────┘

# Serialize almost any data type
# Source : Adrian https://death.andgravity.com/stable-hashing
def json_default(x):
  try:
    return dataclasses.asdict(x)
  except TypeError:
    pass
  if isinstance(x, datetime.datetime):
    return x.isoformat(timespec='microseconds')
  raise TypeError(f"object of type {type(x).__name__} not serializable")

def json_dumps(x):
  return json.dumps(
    x,
    default      = json_default,
    ensure_ascii = False,
    sort_keys    = True,
    indent       = None,
    separators   = (',', ':'),
  )

# Hash
extra_filters['md5']      = lambda x : hashlib.md5      (json_dumps(x).encode('utf-8')).hexdigest()
extra_filters['sha1']     = lambda x : hashlib.sha1     (json_dumps(x).encode('utf-8')).hexdigest()
extra_filters['sha224']   = lambda x : hashlib.sha224   (json_dumps(x).encode('utf-8')).hexdigest()
extra_filters['sha256']   = lambda x : hashlib.sha256   (json_dumps(x).encode('utf-8')).hexdigest()
extra_filters['sha384']   = lambda x : hashlib.sha384   (json_dumps(x).encode('utf-8')).hexdigest()
extra_filters['sha512']   = lambda x : hashlib.sha512   (json_dumps(x).encode('utf-8')).hexdigest()
extra_filters['sha3_224'] = lambda x : hashlib.sha3_224 (json_dumps(x).encode('utf-8')).hexdigest()
extra_filters['sha3_256'] = lambda x : hashlib.sha3_256 (json_dumps(x).encode('utf-8')).hexdigest()
extra_filters['sha3_384'] = lambda x : hashlib.sha3_384 (json_dumps(x).encode('utf-8')).hexdigest()
extra_filters['sha3_512'] = lambda x : hashlib.sha3_512 (json_dumps(x).encode('utf-8')).hexdigest()
extra_filters['blake2b']  = lambda x : hashlib.blake2b  (json_dumps(x).encode('utf-8')).hexdigest()
extra_filters['blake2s']  = lambda x : hashlib.blake2s  (json_dumps(x).encode('utf-8')).hexdigest()
extra_filters['adler32']  = lambda x : zlib.adler32     (json_dumps(x).encode('utf-8'))
extra_filters['crc32']    = lambda x : zlib.crc32       (json_dumps(x).encode('utf-8'))



# ┌─────────────────────┐
# │ String manipulation │
# └─────────────────────┘

# Alignment and padding
extra_filters['ljust']  = lambda s,l,c=" " : str(s).ljust(l,c)
extra_filters['rjust']  = lambda s,l,c=" " : str(s).rjust(l,c)
extra_filters['center'] = lambda s,l,c=" " : str(s).center(l,c)

# Trimming
extra_filters['strip']  = lambda s,p=None : str(s).strip(p)
extra_filters['lstrip'] = lambda s,p=None : str(s).lstrip(p)
extra_filters['rstrip'] = lambda s,p=None : str(s).rstrip(p)

def until(x, terminator):
  if isinstance(x, str):
    if isinstance(terminator, str):
      return x.split(terminator)[0]
    else:
      throw_error(f"Invalid terminator of type '{type(terminator).__name__}' for filter 'until'.")
  else:
    try:
      return x[:x.index(terminator)]
    except Exception as exc:
      throw_error(f"Exception occurred in 'until' filter : \n  {type(exc).__name__}\n{intend_text(exc)}")
extra_filters['until'] = until

# Case
extra_filters['title']      = lambda s : str(s).title()
extra_filters['capitalize'] = lambda s : str(s).capitalize()
extra_filters['casefold']   = lambda s : str(s).casefold()
extra_filters['swapcase']   = lambda s : str(s).swapcase()

re_caps_boundary                    = re.compile(r'(?<!^)(?=[A-Z])')
re_caps_boundary_with_numbers       = re.compile(r'(?<!^)(?=[A-Z0-9])|(?<=[0-9])(?=[a-z])')
re_caps_boundary_group              = re.compile(r'(?<!^)(?<![A-Z])(?=[A-Z])')
re_caps_boundary_group_with_numbers = re.compile(r'(?<!^)(?<![A-Z0-9])(?=[A-Z0-9])|(?<=[0-9])(?=[a-z])')

def split_into_words(text, delimiters=" _-", preserve_caps=True, group_caps=True, consider_numbers=True):
  if group_caps:
    if consider_numbers:
      pattern = re_caps_boundary_group_with_numbers
    else:
      pattern = re_caps_boundary_group
  else:
    if consider_numbers:
      pattern = re_caps_boundary_with_numbers
    else:
      pattern = re_caps_boundary

  words = pattern.split(text)
  if delimiters:
    delimiter_pattern = re.compile(f'[{re.escape(delimiters)}]+')
    additional_words = []
    delimiter_info = []
    for word in words:
      if word:
        splits = delimiter_pattern.split(word)
        delims = delimiter_pattern.findall(word)
        for i, split in enumerate(splits):
          if split:
            additional_words.append(split)
          if i < len(delims):
            delimiter_info.append(delims[i])
    words = [word for word in additional_words if word]

  if not preserve_caps:
    words = [word.lower() for word in words]

  return words, delimiter_info

def camel(text, delimiters=" _-", preserve_caps=True, group_caps=True, consider_numbers=True):
  words, delimiter_info = split_into_words(text, delimiters, preserve_caps, group_caps, consider_numbers)
  if not words:
    return ""
  result = words[0].lower()
  for i, word in enumerate(words[1:], 1):
    if word:
      if i <= len(delimiter_info):
        delimiter = delimiter_info[i-1]
        if len(delimiter) > 1:
          result += delimiter[:-1]
      result += word.capitalize()
  return result

def pascal(text, delimiters=" _-", preserve_caps=True, group_caps=True, consider_numbers=True):
  words, delimiter_info = split_into_words(text, delimiters, preserve_caps, group_caps, consider_numbers)
  if not words:
    return ""
  result = words[0].capitalize()
  for i, word in enumerate(words[1:], 1):
    if word:
      if i <= len(delimiter_info):
        delimiter = delimiter_info[i-1]
        if len(delimiter) > 1:
          result += delimiter[:-1]
      result += word.capitalize()
  return result

def snake(text, delimiters=" _-", preserve_caps=True, group_caps=True, consider_numbers=True):
  words, delimiter_info = split_into_words(text, delimiters, preserve_caps, group_caps, consider_numbers)
  if not words:
    return ""
  result = words[0]
  for i, word in enumerate(words[1:], 1):
    if word:
      if i <= len(delimiter_info):
        delimiter = delimiter_info[i-1]
        result += '_' * len(delimiter)
      else:
        result += '_'
      result += word
  return result

def kebab(text, delimiters=" _-", preserve_caps=True, group_caps=True, consider_numbers=True):
  words, delimiter_info = split_into_words(text, delimiters, preserve_caps, group_caps, consider_numbers)
  if not words:
    return ""
  result = words[0]
  for i, word in enumerate(words[1:], 1):
    if word:
      if i <= len(delimiter_info):
        delimiter = delimiter_info[i-1]
        result += '-' * len(delimiter)
      else:
        result += '-'
      result += word
  return result

extra_filters['camel']  = camel
extra_filters['pascal'] = pascal
extra_filters['snake']  = snake
extra_filters['kebab']  = kebab

def change_case(text, case=None, delimiters=" _-", preserve_caps=True, group_caps=True, consider_numbers=True):
  match case:
    case "lower":      text = text.lower()
    case "upper":      text = text.upper()
    case "title":      text = text.title()
    case "capitalize": text = text.capitalize()
    case "casefold":   text = text.casefold()
    case "swapcase":   text = text.swapcase()
    case "camel":      text = camel  (text, delimiters, preserve_caps, group_caps, consider_numbers)
    case "pascal":     text = pascal (text, delimiters, preserve_caps, group_caps, consider_numbers)
    case "snake":      text = snake  (text, delimiters, preserve_caps, group_caps, consider_numbers)
    case "kebab":      text = kebab  (text, delimiters, preserve_caps, group_caps, consider_numbers)
  return text
extra_filters['change_case'] = change_case

def affix(text, prefix="", suffix="", case=None, delimiters=" _-", preserve_caps=True, group_caps=True, consider_numbers=True):
  return prefix + change_case(text, case, delimiters, preserve_caps, group_caps, consider_numbers) + suffix
extra_filters['affix'] = affix

extra_filters['change_case_all']  = lambda l,c,    d=" _-",pc=True,gc=True,cn=True : [change_case(s,c,d,pc,gc,cn) for s in l]
extra_filters['affix_all']        = lambda l,p,s,c,d=" _-",pc=True,gc=True,cn=True : [affix(s,p,s,c,d,pc,gc,cn)   for s in l]



# ┌──────────────────────┐
# │ Paragraph formatting │
# └──────────────────────┘

# Affix lines with prefix and suffix
def affix_lines(content, prefix="", suffix="", prefix_first=True, suffix_last=True, affix_blank=True, strip_left=False, strip_right=False):
  # Iterate line by line
  lines = content.split('\n')
  for index,line in enumerate(lines):
    # Strip the line if requested
    if strip_left:
      line = line.lstrip()
    if strip_right:
      line = line.rstrip()
    # If line is not blank or we affix blank lines
    if line != '' or affix_blank:
      # If line isn't the first line and we affix the first line
      if index != 0 or prefix_first:
        line = prefix + line
      # If line isn't the last line and we affix the last line
      if index != len(lines)-1 or suffix_last:
        line = line + suffix
    # Update the line
    lines[index] = line
  return '\n'.join(lines)
extra_filters['affix_lines'] = affix_lines

# Justify lines
def justify_lines(content, width=1, fillchar=' ', align='left'):
  # Width of the longest line
  max_width = max([len(line) for line in content.split('\n')])
  justify_width = max(max_width, width)
  # Iterate line by line
  lines = content.split('\n')
  for index,line in enumerate(lines):
    # Justify the line
    match align:
      case 'left':
        line = line.ljust(justify_width, fillchar)
      case 'right':
        line = line.rjust(justify_width, fillchar)
      case 'center':
        line = line.center(justify_width, fillchar)
    # Update the line
    lines[index] = line
  return '\n'.join(lines)
extra_filters['ljust_lines']  = lambda s,w=1,c=" " : justify_lines(s,w,c,'left')
extra_filters['rjust_lines']  = lambda s,w=1,c=" " : justify_lines(s,w,c,'right')
extra_filters['center_lines'] = lambda s,w=1,c=" " : justify_lines(s,w,c,'center')

# Controlling line jumps and blank lines
extra_filters['strip_line_jumps']   = lambda P : P.strip('\n')
extra_filters['remove_blank_lines'] = lambda P : re.sub(r"\n(\s*\n)+", "\n", P)

# Removes pre-existing indentation and sets new one
def reindent(content, depth=1, spaces=2, tabs=False, first=False, blank=False):
  indent = depth * ('\t' if tabs else ' '*spaces)

  # Iterate line by line
  lines = content.split('\n')
  for index,line in enumerate(lines):

    # First line skipped according to argument
    if index == 0 and not first:
      continue

    # Update the line with the correct indentation
    line = line.lstrip()
    if line != '' or blank:
      line = indent + line
    lines[index] = line

  # Return paragraph of lines
  return '\n'.join(lines)

extra_filters['reindent'] = reindent


# Removes pre-existing indentation and sets new indent based on rules
def autoindent(content, starts=['{'], ends=['}'], spaces=2, tabs=False, first=False, blank=False):
  depth      = 0
  next_depth = 0

  # Iterate line by line
  lines = content.split('\n')
  for index,line in enumerate(lines):
    depth = next_depth

    # First line
    if index == 0:

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
    if line != '' or blank:
      line = indent + line
    lines[index] = line

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
    column_index = 0
    # First split at the right align boundaries
    line_split_rjust = line.split('§§')
    for rjust_index, text_rjust in enumerate(line_split_rjust):
      # Then split at the left align boundaries
      text_rjust_split_ljust = text_rjust.split('§')
      for ljust_index, text in enumerate(text_rjust_split_ljust):
        # Preserve the indentation of the line
        if column_index == 0:
          text = text.rstrip()
        else:
          text = text.strip()
        # Build object with dict for each column
        if ljust_index == len(text_rjust_split_ljust)-1 and rjust_index != len(line_split_rjust)-1:
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
          if column_index == len(columns_widths):
            columns_widths.append(column_width)
          else:
            columns_widths[column_index] = max(columns_widths[column_index], column_width)
        column_index += 1
    lines_objs.append(line_obj)

  # No alignment markers detected
  if not columns_widths:
    return content

  # Then apply the alignment to all the lines
  lines = []
  for line_index,line_obj in enumerate(lines_objs):
    line = ""
    for column_index, column in enumerate(line_obj):
      column_width = columns_widths[column_index]
      column_text = column['text']
      column_just = column['just']
      if column_index == len(line_obj)-1:
        line += column_text
      elif column_just == 'left':
        line += column_text.ljust(column_width)
      else:
        line += column_text.rjust(column_width)
      if column_index != len(line_obj)-1:
        line += ' '*margin
    lines.append(line)

  # Return paragraph of lines
  return '\n'.join(lines)

extra_filters['align'] = align


re_restructure_nocapture = re.compile(r'{§\s*[\w\s]+?\s*§}')
re_restructure_capture   = re.compile(r'{§\s*([\w\s]+?)\s*§}')
re_s                     = re.compile(r'\s+')

def restructure(content):
  result = ""

  # Split the content between content sections and tags
  sections = re_restructure_nocapture.split(content)
  tags     = re_restructure_capture.findall(content)

  # Iterate over sections and tags
  for section, tag in zip(sections[:-1], tags):
    # Strip the line breaks and space around the content
    section = section.rstrip(' \t').strip('\n\r')
    # Split the tag into words
    tag_split = re_s.split(tag)
    # First word is the type of structure
    tag_operation = tag_split[0]
    # Other words are the operands
    tag_operands = tag_split[1:] if len(tag_split) > 1 else []
    # Spacing sections with line breaks
    if (tag_operation == 'spacing'):
      # Number of line breaks (by default 1)
      spacing = int(tag_operands[0])+1 if len(tag_operands) > 0 else 1
      # Add the section and its after-spacing
      result += section + '\n'*spacing
  # Add the last section
  result += sections[-1].rstrip(' \t').strip('\n\r')
  return result

extra_filters['restructure'] = restructure



# ┌─────────────────────┐
# │ Dictionary and list │
# └─────────────────────┘

# List of keys or values
extra_filters['keys']   = lambda D : list(D.keys())
extra_filters['values'] = lambda D : list(D.values())

# List of attributes of elements in nested dictionary or list of dictionaries
extra_filters['attributes'] = lambda X,attr : [x[attr] for x in (X.values() if isinstance(X,dict) else X) if attr in x]

# Filter nested dictionary or list of dictionaries
extra_filters['filter']  = lambda X,attribute,query : {key:value for key,value in X.keys() if isinstance(value,dict) and attribute in value and value[attribute]==query} if isinstance(X,dict) else [element for element in X if isinstance(element,dict) and attribute in element and element[attribute]==query]
extra_filters['excluse'] = lambda X,attribute,query : {key:value for key,value in X.keys() if isinstance(value,dict) and attribute in value and value[attribute]!=query} if isinstance(X,dict) else [element for element in X if isinstance(element,dict) and attribute in element and element[attribute]!=query]

# Filter dictionary based on keys
extra_filters['filter_by_list']   = lambda D,keys  : {key:D[key] for key       in keys      if key in D.keys()}
extra_filters['filter_by_regex']  = lambda D,regex : {key:value  for key,value in D.items() if re.fullmatch(regex,key)}
extra_filters['exclude_by_list']  = lambda D,keys  : {key:value  for key,value in D.items() if key not in keys}
extra_filters['exclude_by_regex'] = lambda D,regex : {key:value  for key,value in D.items() if not re.fullmatch(regex,key)}

# Element max and min based on sub attribute
extra_filters['el_of_max_attr'] = lambda L,attr : max(L, key = lambda el : el[attr])
extra_filters['el_of_min_attr'] = lambda L,attr : min(L, key = lambda el : el[attr])

# Key of max and min based on sub attribute
extra_filters['key_of_max_attr'] = lambda D,attr : max(D, key = lambda key : D[key][attr])
extra_filters['key_of_min_attr'] = lambda D,attr : min(D, key = lambda key : D[key][attr])

# Shortcut for the previous filters for both dictionary and list
extra_filters['with_max'] = lambda X,attr : extra_filters['el_of_max_attr'](X,attr) if isinstance(X,dict) else extra_filters['key_of_max_attr'](X,attr)
extra_filters['with_min'] = lambda X,attr : extra_filters['el_of_min_attr'](X,attr) if isinstance(X,dict) else extra_filters['key_of_min_attr'](X,attr)

# Accumulate elements of integer/float list
extra_filters['accumulate'] = lambda L : itertools.accumulate(L)

# Count occurences in list
extra_filters['count'] = lambda L,x : sum([l==x for l in L])

# Flatten to shallow list, keep only values for dictionaries
extra_filters['flatten'] = flatten



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
@render_time_only
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
@render_time_only
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
