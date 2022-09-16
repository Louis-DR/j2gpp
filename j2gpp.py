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

j2gpp_version = "1.1.0"
j2gpp_title()
print(f"Python version :",python_version())
print(f"Jinja2 version :",jinja2_version)
print(f"J2GPP  version :",j2gpp_version)

sources = []
global_var_paths = []
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
        throw_error(f"Exception occured while loading {var_path} : \n  {type(exc).__name__}\n{intend_text(exc)}")
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
        throw_error(f"Exception occured while loading {var_path} : \n  {type(exc).__name__}\n{intend_text(exc)}")
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
      except Exception as exc:
        throw_error(f"Exception occured while loading {var_path} : \n  {type(exc).__name__}\n{intend_text(exc)}")
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
argparser.add_argument("source",                          help="Path to library file",                                         nargs='*')
argparser.add_argument("-O", "--outdir",  dest="outdir",  help="Output directory path"                                                  )
argparser.add_argument("-o", "--output",  dest="output",  help="Output file path for single source template"                            )
argparser.add_argument("-I", "--incdir",  dest="incdir",  help="Include directories for include and import Jinja2 statements", nargs='+')
argparser.add_argument("-D", "--define",  dest="define",  help="Define global variables in the format name=value",             nargs='+')
argparser.add_argument("-V", "--varfile", dest="varfile", help="Global variables files",                                       nargs='+')
argparser.add_argument(      "--version", dest="version", help="Print J2GPP version and quits",                                action="store_true", default=False)
argparser.add_argument(      "--license", dest="license", help="Print J2GPP license and quits",                                action="store_true", default=False)
args, args_unknown = argparser.parse_known_args()

# Parsing arguments
throw_h2("Parsing command line arguments")

if args_unknown:
  throw_error(f"Incorrect arguments '{' '.join(args_unknown)}'.")

if args.version:
  print(j2gpp_version)
  exit()

if args.license:
  with open('LICENSE','r') as license_file:
    license_text = license_file.read()
    print("J2GPP is under",license_text)
  exit()

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

if args.define:
  print("Global variables defined :")
  for define in args.define:
    print(" ",define)
    # Defines in the format name=value
    var, val = define.split('=')
    # Cast int and floats
    if val.isdecimal():
      val = int(val)
    elif str_isfloat(val):
      val = float(val)
    global_vars[var] = val
else: print("No global variables defined.")

if args.varfile:
  print("Global variables files :")
  for var_path in args.varfile:
    # Get full path
    var_path = os.path.expandvars(os.path.expanduser(os.path.abspath(var_path)))
    print(" ",var_path)
    global_var_paths.append(var_path)
else: print("No global variables file provided.")

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

# Loading global variables from files
for var_path in global_var_paths:
  for extension, loader in loaders.items():
    if var_path.endswith(extension):
      print(f"Loading global variables file '{var_path}'")
      try:
        var_dict = loader(var_path)
      except OSError as exc:
        var_dict = {}
        if exc.errno == errno.ENOENT:
          throw_error(f"Cannot read '{var_path}' : file doesn't exist.")
        elif exc.errno == errno.EACCES:
          throw_error(f"Cannot read '{var_path}' : missing read permission.")
        else:
          throw_error(f"Cannot read '{var_path}'.")
      global_vars.update(var_dict)


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

throw_h2("Done")
