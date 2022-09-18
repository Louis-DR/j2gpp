# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     j2gpp - Jinja2-based General Purpose Preprocessor            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        j2gpp.py                                                     ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Jinja2-based General Purpose Preprocessor. For information   ║
# ║              about the usage of this tool, please refer to the README.    ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



import argparse
import glob
import os
import errno
from platform import python_version
from jinja2 import Environment, FileSystemLoader
from jinja2 import __version__ as jinja2_version
from utils import *

j2gpp_version = "1.2.0"

sources = []
global_var_paths = []
global_vars = {}
# CSV options
csv_delimiter = ","
csv_escapechar = None
csv_dontstrip = False



# ┌────────────────────────┐
# │ Variable files loaders │
# └────────────────────────┘

def load_yaml(var_path):
  var_dict = {}
  try:
    from ruamel.yaml import YAML
    yaml = YAML(typ="safe")
    with open(var_path) as var_file:
      try:
        var_dict = yaml.load(var_file)
      except Exception as exc:
        throw_error(f"Exception occured while loading '{var_path}' : \n  {type(exc).__name__}\n{intend_text(exc)}")
  except ImportError:
    throw_error("Could not import Python library 'ruamel.yaml' to parse YAML variables files.")
  return var_dict

def load_json(var_path):
  var_dict = {}
  try:
    import json
    with open(var_path) as var_file:
      try:
        var_dict = json.load(var_file)
      except Exception as exc:
        throw_error(f"Exception occured while loading '{var_path}' : \n  {type(exc).__name__}\n{intend_text(exc)}")
  except ImportError:
    throw_error("Could not import Python library 'json' to parse JSON variables files.")
  return var_dict

def load_xml(var_path):
  var_dict = {}
  try:
    import xmltodict
    # Postprocessor to auto cast the values
    def xml_postprocessor(path, key, value):
      if value == "true": value = "True"
      if value == "false": value = "False"
      return key, auto_cast_str(value)
    with open(var_path) as var_file:
      try:
        var_dict = xmltodict.parse(var_file.read(), postprocessor=xml_postprocessor)
        # If root element is '_', then remove this level
        if '_' in var_dict.keys():
          var_dict = var_dict['_']
      except Exception as exc:
        throw_error(f"Exception occured while loading '{var_path}' : \n  {type(exc).__name__}\n{intend_text(exc)}")
  except ImportError:
    throw_error("Could not import Python library 'xmltodict' to parse XML variables files.")
  return var_dict

def load_toml(var_path):
  var_dict = {}
  try:
    import toml
    with open(var_path) as var_file:
      try:
        var_dict = toml.load(var_file)
      except Exception as exc:
        throw_error(f"Exception occured while loading '{var_path}' : \n  {type(exc).__name__}\n{intend_text(exc)}")
  except ImportError:
    throw_error("Could not import Python library 'toml' to parse TOML variables files.")
  return var_dict

def load_ini(var_path):
  var_dict = {}
  try:
    import configparser
    with open(var_path) as var_file:
      try:
        config = configparser.ConfigParser()
        config.read_file(var_file)
        var_dict = {s:dict(config.items(s)) for s in config.sections()}
      except Exception as exc:
        throw_error(f"Exception occured while loading '{var_path}' : \n  {type(exc).__name__}\n{intend_text(exc)}")
  except ImportError:
    throw_error("Could not import Python library 'configparser' to parse INI/CFG variables files.")
  return var_dict

def load_env(var_path):
  var_dict = {}
  with open(var_path) as var_file:
    for line_nbr, line in enumerate(var_file):
      if line and line != "\n":
        # Comment line
        if line[0] == '#':
          continue
        # Syntax is var=value
        if '=' not in line:
          throw_error(f"Incorrect ENV file syntax '{line}' line {line_nbr} of file '{var_path}'.")
          continue
        var, val = line.split('=')
        var = var.strip()
        val = val.strip()
        val = auto_cast_str(val)
        # Handle conflits inside the file
        if var in var_dict:
          throw_warning(f"Variable '{var}' redefined from '{var_dict[var]}' to '{val}' in file '{var_path}'.")
        var_dict[var] = val
  return var_dict

def load_csv(var_path, delimiter=csv_delimiter):
  var_dict = {}
  try:
    import csv
    with open(var_path) as var_file:
      try:
        csv_reader = csv.DictReader(var_file, delimiter=delimiter, escapechar=csv_escapechar)
        # First columns for keys
        main_key = csv_reader.fieldnames[0]
        for row in csv_reader:
          var = row.pop(main_key)
          # Strip whitespace around key and value
          if not csv_dontstrip:
            row = {key.strip():val.strip() for key,val in row.items()}
          # Auto cast values
          row = {key:auto_cast_str(val) for key,val in row.items()}
          # Handle conflits inside the file
          if var in var_dict:
            throw_warning(f"Row '{var}' redefined from '{var_dict[var]}' to '{row}' in file '{var_path}'.")
          var_dict[var] = row
      except Exception as exc:
        throw_error(f"Exception occured while loading '{var_path}' : \n  {type(exc).__name__}\n{intend_text(exc)}")
  except ImportError:
    throw_error("Could not import Python library 'csv' to parse CSV/TSV variables files.")
  return var_dict

def load_tsv(var_path):
  return load_csv(var_path, delimiter='\t')

loaders = {
  'yaml': load_yaml,
  'yml':  load_yaml,
  'json': load_json,
  'xml':  load_xml,
  'toml': load_toml,
  'ini':  load_ini,
  'cfg':  load_ini,
  'env':  load_env,
  'csv':  load_csv,
  'tsv':  load_tsv,
}



# ┌────────────────────────┐
# │ Command line interface │
# └────────────────────────┘

# Creating arguments
argparser = argparse.ArgumentParser()
argparser.add_argument("source",                                            help="Path to library file",                                         nargs='*')
argparser.add_argument("-O", "--outdir",           dest="outdir",           help="Output directory path"                                                  )
argparser.add_argument("-o", "--output",           dest="output",           help="Output file path for single source template"                            )
argparser.add_argument("-I", "--incdir",           dest="incdir",           help="Include directories for include and import Jinja2 statements", nargs='+')
argparser.add_argument("-D", "--define",           dest="define",           help="Define global variables in the format name=value",             nargs='+')
argparser.add_argument("-V", "--varfile",          dest="varfile",          help="Global variables files",                                       nargs='+')
argparser.add_argument(      "--csv_delimiter",    dest="csv_delimiter",    help="CSV delimiter (default: ',')",                                          )
argparser.add_argument(      "--csv_escapechar",   dest="csv_escapechar",   help="CSV escape character (default: None)",                                  )
argparser.add_argument(      "--csv_dontstrip",    dest="csv_dontstrip",    help="Disable stripping whitespace of CSV values",                            )
argparser.add_argument(      "--perf",             dest="perf",             help="Measure and display performance",                              action="store_true", default=False)
argparser.add_argument(      "--version",          dest="version",          help="Print J2GPP version and quits",                                action="store_true", default=False)
argparser.add_argument(      "--license",          dest="license",          help="Print J2GPP license and quits",                                action="store_true", default=False)
args, args_unknown = argparser.parse_known_args()

if args.version:
  print(j2gpp_version)
  exit()

if args.license:
  with open('LICENSE','r') as license_file:
    license_text = license_file.read()
    print("J2GPP is under",license_text)
  exit()

# Title after license and version argument parsing
j2gpp_title()
print(f"Python version :",python_version())
print(f"Jinja2 version :",jinja2_version)
print(f"J2GPP  version :",j2gpp_version)

# Parsing arguments
throw_h2("Parsing command line arguments")

if args.perf:
  perf_counter = perf_counter_start()

if args_unknown:
  throw_error(f"Incorrect arguments '{' '.join(args_unknown)}'.")

arg_source = args.source
if not arg_source:
  throw_error("Must provide at least one source template.")
  exit()

out_dir = ""
if args.outdir:
  # Get full path
  out_dir = os.path.expandvars(os.path.expanduser(os.path.abspath(args.outdir)))
  # Create directories if needed
  if not os.path.isdir(out_dir):
    os.makedirs(out_dir)
  print("Output directory :\n ",out_dir)
else:
  print("Output directory :\n ",os.getcwd())

one_out_path = ""
if args.output:
  # Get full path
  one_out_path = os.path.expandvars(os.path.expanduser(os.path.abspath(args.output)))
  one_out_dir = os.path.dirname(one_out_path)
  # Create directories if needed
  if not os.path.isdir(one_out_dir):
    os.makedirs(one_out_dir)
  print("Output file :",out_dir)

inc_dirs = []
if args.incdir:
  print("Include directories :")
  for inc_dir in args.incdir:
    # Get full path
    inc_dir = os.path.expandvars(os.path.expanduser(os.path.abspath(inc_dir)))
    print(" ",inc_dir)
    inc_dirs.append(inc_dir)
else: print("No include directory provided.")

defines = []
if args.define:
  defines = args.define
  print("Global variables defined :")
  for define in defines:
    print(" ",define)
else: print("No global variables defined.")

if args.varfile:
  print("Global variables files :")
  for var_path in args.varfile:
    # Get full path
    var_path = os.path.expandvars(os.path.expanduser(os.path.abspath(var_path)))
    print(" ",var_path)
    global_var_paths.append(var_path)
else: print("No global variables file provided.")

if args.csv_delimiter:
  csv_delimiter = args.csv_delimiter
  print(f"CSV delimiter : {csv_delimiter}.")

if args.csv_escapechar:
  csv_escapechar = args.csv_escapechar
  print(f"CSV escape character : {csv_escapechar}.")

if args.csv_dontstrip:
  csv_dontstrip = args.csv_dontstrip
  print(f"CSV auto whitespace stripping is disabled.")

# Jinja2 environment
env = Environment(
  loader=FileSystemLoader(inc_dirs)
)



# ┌───────────────────────┐
# │ Fetching source files │
# └───────────────────────┘

throw_h2("Fetching source files")

# Collecting source templates paths
for raw_path in arg_source:
  # Glob to apply UNIX-style path patterns
  for glob_path in glob.glob(raw_path):
    abs_path = os.path.abspath(glob_path)
    # Only keep files ending with .j2 extension
    if os.path.isfile(abs_path) and abs_path.endswith('.j2'):
      print(f"Found template source {abs_path}")
      # Strip .j2 extension for output path
      out_path = abs_path[:-3]
      # Providing output directory
      if out_dir:
        out_path = os.path.join(out_dir, os.path.basename(out_path))
      # Providing output file name
      if one_out_path:
        out_path = one_out_path
      # Dict structure for each source template
      src_dict = {
        'src_path': abs_path,
        'out_path': out_path
      }
      sources.append(src_dict)



# ┌───────────────────┐
# │ Loading variables │
# └───────────────────┘

throw_h2("Loading variables")

# Merge two dictionaries
def var_dict_update(var_dict1, var_dict2, val_scope="", context=""):
  var_dict_res = var_dict1.copy()
  for key,val in var_dict2.items():
    # Conflict
    if key in var_dict1.keys() and var_dict1[key] != val:
      val_ori = var_dict1[key]
      # Recursively merge dictionary
      if isinstance(val_ori, dict) and isinstance(val, dict):
        val_scope = f"{val_scope}{key}."
        var_dict_res[key] = var_dict_update(val_ori, val, val_scope, context)
      else:
        var_dict_res[key] = val
        throw_warning(f"Variable '{val_scope}{key}' got overwritten from '{val_ori}' to '{val}'{context}.")
    else:
      var_dict_res[key] = val
  return var_dict_res

# Load variables from a file and return the dictionary
def load_var_file(var_path):
  var_dict = {}
  var_format = var_path.split('.')[-1]
  if var_format in loaders:
    loader = loaders[var_format]
    try:
      var_dict = loader(var_path)
    except OSError as exc:
      if exc.errno == errno.ENOENT:
        throw_error(f"Cannot read '{var_path}' : file doesn't exist.")
      elif exc.errno == errno.EACCES:
        throw_error(f"Cannot read '{var_path}' : missing read permission.")
      else:
        throw_error(f"Cannot read '{var_path}'.")
  else:
    throw_error(f"Cannot read '{var_path}' : unsupported format.")
  return var_dict

# Loading global variables from files
for var_path in global_var_paths:
  print(f"Loading global variables file '{var_path}'")
  var_dict = load_var_file(var_path)
  global_vars = var_dict_update(global_vars, var_dict, context=f" when loading global variables file '{var_path}'")

# Loading global variables from define
if defines:
  print(f"Loading global variables from command line defines.")
  for define in defines:
    # Defines in the format name=value
    if '=' not in define:
      throw_error(f"Incorrect define argument format for '{define}'.")
      continue
    var, val = define.split('=')
    var_dict = {}
    # Evaluate value to correct type
    val = auto_cast_str(val)
    # Interpret dot as dictionary depth
    var_keys = var.split('.')[::-1]
    var_dict = {var_keys[0]:val}
    for var_key in var_keys[1:]:
      var_dict = {var_key:var_dict}
    # Merge with global variables dictionary
    global_vars = var_dict_update(global_vars, var_dict, context=f" when loading global command line defines")



# ┌─────────────────────┐
# │ Rendering templates │
# └─────────────────────┘

throw_h2("Rendering templates")

# Render all templates
for src_dict in sources:
  print(f"Rendering {src_dict['src_path']} \n       to {src_dict['out_path']}")
  src_path = src_dict['src_path']
  out_path = src_dict['out_path']
  src_res = ""
  try:
    with open(src_path,'r') as src_file:
      src_res = env.from_string(src_file.read()).render(global_vars)
  except OSError as exc:
    if exc.errno == errno.ENOENT:
      throw_error(f"Cannot read '{var_path}' : file doesn't exist.")
    elif exc.errno == errno.EACCES:
      throw_error(f"Cannot read '{var_path}' : missing read permission.")
    else:
      throw_error(f"Cannot read '{var_path}'.")
  except Exception as exc:
    throw_error(f"Exception occured while rendering '{src_path}' : \n  {type(exc).__name__}\n{intend_text(exc)}")
  try:
    with open(out_path,'w') as out_file:
      out_file.write(src_res)
  except OSError as exc:
    if exc.errno == errno.EISDIR:
      throw_error(f"Cannot write '{var_path}' : path is a directory.")
    elif exc.errno == errno.EACCES:
      throw_error(f"Cannot write '{var_path}' : missing write permission.")
    else:
      throw_error(f"Cannot write '{var_path}'.")



# ┌─────┐
# │ End │
# └─────┘

# Print all errors and warnings at the end
if errors or warnings:
  throw_h2("Error/warning summary")
  error_warning_summary()

# Print the performance timer
if args.perf:
  throw_h2("Performance")
  perf_counter_print(perf_counter_stop(perf_counter))

throw_h2("Done")
