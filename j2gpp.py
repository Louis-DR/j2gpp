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
import ast
import os
import errno
from platform import python_version
from jinja2 import Environment, FileSystemLoader
from jinja2 import __version__ as jinja2_version
from utils import *

j2gpp_version = "1.2.0"

# Source templates
sources = []
# Global variables
global_vars = {}



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
        throw_error(f"Exception occurred while loading {var_path} : \n  {type(exc).__name__}\n{intend_text(exc)}")
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
        throw_error(f"Exception occurred while loading {var_path} : \n  {type(exc).__name__}\n{intend_text(exc)}")
  except ImportError:
    throw_error("Could not import Python library 'json' to parse JSON variables files.")
  return var_dict

def load_xml(var_path):
  var_dict = {}
  try:
    import xmltodict
    with open(var_path) as var_file:
      try:
        var_dict = xmltodict.parse(var_file.read())
        if '_' in var_dict.keys():
          var_dict = var_dict['_']
      except Exception as exc:
        throw_error(f"Exception occurred while loading {var_path} : \n  {type(exc).__name__}\n{intend_text(exc)}")
  except ImportError:
    throw_error("Could not import Python library 'xmltodict' to parse XML variables files.")
  return var_dict

loaders = {
  'yaml': load_yaml,
  'yml':  load_yaml,
  'json': load_json,
  'xml':  load_xml
}



# ┌────────────────────────┐
# │ Command line interface │
# └────────────────────────┘

# Creating arguments
argparser = argparse.ArgumentParser()
argparser.add_argument("source",                                                  help="Source template files or directories to render",                 nargs='*')
argparser.add_argument("-O", "--outdir",              dest="outdir",              help="Output directory path"                                                    )
argparser.add_argument("-o", "--output",              dest="output",              help="Output file path for single source template"                              )
argparser.add_argument("-I", "--incdir",              dest="incdir",              help="Include directories for include and import Jinja2 statements",   nargs='+')
argparser.add_argument("-D", "--define",              dest="define",              help="Define global variables in the format name=value",               nargs='+')
argparser.add_argument("-V", "--varfile",             dest="varfile",             help="Global variables files",                                         nargs='+')
argparser.add_argument(      "--render-non-template", dest="render_non_template", help="Process also source files that are not recognized as templates", nargs='?',           default=None, const="_j2gpp")
argparser.add_argument(      "--force-glob",          dest="force_glob",          help="Glob UNIX-like patterns in path even when quoted",               action="store_true", default=False)
argparser.add_argument(      "--perf",                dest="perf",                help="Measure and display performance",                                action="store_true", default=False)
argparser.add_argument(      "--version",             dest="version",             help="Print J2GPP version and quits",                                  action="store_true", default=False)
argparser.add_argument(      "--license",             dest="license",             help="Print J2GPP license and quits",                                  action="store_true", default=False)
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

global_var_paths = []
if args.varfile:
  print("Global variables files :")
  for var_path in args.varfile:
    # Get full path
    var_path = os.path.expandvars(os.path.expanduser(os.path.abspath(var_path)))
    print(" ",var_path)
    global_var_paths.append(var_path)
else: print("No global variables file provided.")

options = {}
options['force_glob']          = args.force_glob
options['render_non_template'] = args.render_non_template

# Jinja2 environment
env = Environment(
  loader=FileSystemLoader(inc_dirs)
)



# ┌───────────────────────┐
# │ Fetching source files │
# └───────────────────────┘

throw_h2("Fetching source files")

# Fetch source template file
def fetch_source_file(src_path, dir_path="", warn_non_template=False):
  # Only keep files ending with .j2 extension
  if src_path.endswith('.j2') or options['render_non_template']:
    print(f"Found template source {src_path}")

    # Output file name if we render non-templates sources
    if options['render_non_template'] and not src_path.endswith('.j2'):
      # Add the option suffix before file extensions if present
      if '.' in src_path:
        out_path = src_path.replace('.', options['render_non_template']+'.', 1)
      else:
        out_path = src_path + options['render_non_template']
    else:
      # Strip .j2 extension for output path
      out_path = src_path[:-3]

    # Providing output directory
    if out_dir:
      if dir_path:
        out_path = os.path.join(out_dir, os.path.relpath(out_path, dir_path))
      else:
        out_path = os.path.join(out_dir, os.path.basename(out_path))

    # Providing output file name
    if one_out_path:
      out_path = one_out_path

    # Dict structure for each source template
    src_dict = {
      'src_path': src_path,
      'out_path': out_path
    }
    sources.append(src_dict)
  elif warn_non_template:
    throw_warning(f"Source file '{src_path}' is not a template.")

# Fetch directory of source files
def fetch_source_directory(dir_path):
  # Read and execute permission required
  if not os.access(dir_path, os.R_OK | os.X_OK):
    throw_error(f"Missing access permissions for source directory '{dir_path}'.")
  else:
    print(f"Found source directory {dir_path}")
    for subdir, dirs, files in os.walk(dir_path):
      for src_path in files:
        abs_path = os.path.join(subdir, src_path)
        fetch_source_file(abs_path, dir_path)

# Fetch source file or directory
def fetch_source(src_path, warn_non_template=False):
  if os.path.isdir(src_path):
    fetch_source_directory(src_path)
  elif os.path.isfile(src_path):
    fetch_source_file(src_path, warn_non_template=warn_non_template)
  else:
    throw_error(f"Unresolved source '{src_path}'.")

# Collecting source templates paths
for raw_path in arg_source:
  if options['force_glob']:
    # Glob to apply UNIX-style path patterns
    for glob_path in glob.glob(raw_path):
      abs_path = os.path.abspath(glob_path)
      fetch_source(abs_path)
  else:
    abs_path = os.path.abspath(raw_path)
    fetch_source(abs_path, warn_non_template=True)



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
    try:
      val = ast.literal_eval(val)
    except:
      pass
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
    throw_error(f"Exception occurred while rendering '{src_path}' : \n  {type(exc).__name__}\n{intend_text(exc)}")
  try:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
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
