# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     j2gpp - Jinja2-based General Purpose Preprocessor            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        j2gpp.py                                                     ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Jinja2-based General Purpose Preprocessor. For information   ║
# ║              about the usage of this tool, please refer to the README or  ║
# ║              run "j2gp --help".                                           ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



import argparse
import glob
import imp
import os
import re
import errno
import shutil
from datetime import datetime
from platform import python_version
from jinja2 import Environment, FileSystemLoader
from jinja2 import __version__ as jinja2_version
from j2gpp.utils import *
from j2gpp.filters import extra_filters, write_source_toggle
from j2gpp.tests import extra_tests

def main():

  j2gpp_version = "2.0.2"

  # Source templates
  sources = []
  # Non-template files to copy
  to_copy= []
  # Global variables
  global_vars = {}
  # Special options
  options = {}
  # Flag to skip writing the original template
  global write_source_toggle



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
          throw_error(f"Exception occurred while loading '{var_path}' : \n  {type(exc).__name__}\n{intend_text(exc)}")
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
          throw_error(f"Exception occurred while loading '{var_path}' : \n  {type(exc).__name__}\n{intend_text(exc)}")
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
          throw_error(f"Exception occurred while loading '{var_path}' : \n  {type(exc).__name__}\n{intend_text(exc)}")
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
          throw_error(f"Exception occurred while loading '{var_path}' : \n  {type(exc).__name__}\n{intend_text(exc)}")
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
          for section in config.sections():
            if section == '_':
              for var,val in config.items(section):
                var_dict[var] = auto_cast_str(val)
            else:
              var_dict[section] = dict(config.items(section))
        except Exception as exc:
          throw_error(f"Exception occurred while loading '{var_path}' : \n  {type(exc).__name__}\n{intend_text(exc)}")
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

  def load_csv(var_path, delimiter=''):
    var_dict = {}
    if not delimiter: delimiter = options['csv_delimiter']
    try:
      import csv
      with open(var_path) as var_file:
        try:
          csv_reader = csv.DictReader(var_file, delimiter=delimiter, escapechar=options['csv_escapechar'])
          # First columns for keys
          main_key = csv_reader.fieldnames[0]
          for row in csv_reader:
            var = row.pop(main_key)
            # Strip whitespace around key and value
            if not options['csv_dontstrip']:
              row = {key.strip():val.strip() for key,val in row.items()}
            # Auto cast values
            row = {key:auto_cast_str(val) for key,val in row.items()}
            # Handle conflits inside the file
            if var in var_dict:
              throw_warning(f"Row '{var}' redefined from '{var_dict[var]}' to '{row}' in file '{var_path}'.")
            var_dict[var] = row
        except Exception as exc:
          throw_error(f"Exception occurred while loading '{var_path}' : \n  {type(exc).__name__}\n{intend_text(exc)}")
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
  argparser.add_argument("source",                                                  help="Source template files or directories to render",                 nargs='*')
  argparser.add_argument("-O", "--outdir",              dest="outdir",              help="Output directory path"                                                    )
  argparser.add_argument("-o", "--output",              dest="output",              help="Output file path for single source template"                              )
  argparser.add_argument("-I", "--incdir",              dest="incdir",              help="Include directories for include and import Jinja2 statements",   nargs='+')
  argparser.add_argument("-D", "--define",              dest="define",              help="Define global variables in the format name=value",               nargs='+')
  argparser.add_argument("-V", "--varfile",             dest="varfile",             help="Global variables files",                                         nargs='+')
  argparser.add_argument(      "--envvar",              dest="envvar",              help="Loads environment variables as global variables",                nargs='?',           default=None, const="")
  argparser.add_argument(      "--filters",             dest="filters",             help="Load extra Jinja2 filters from a Python file",                   nargs='+')
  argparser.add_argument(      "--tests",               dest="tests",               help="Load extra Jinja2 tests from a Python file",                     nargs='+')
  argparser.add_argument(      "--vars-post-processor", dest="vars_post_processor", help="Load a Python function to process variables after loading",      nargs=2  )
  argparser.add_argument(      "--overwrite-outdir",    dest="overwrite_outdir",    help="Overwrite output directory",                                     action="store_true", default=False)
  argparser.add_argument(      "--warn-overwrite",      dest="warn_overwrite",      help="Warn when overwriting files",                                    action="store_true", default=False)
  argparser.add_argument(      "--no-overwrite",        dest="no_overwrite",        help="Prevent overwriting files",                                      action="store_true", default=False)
  argparser.add_argument(      "--no-check-identifier", dest="no_check_identifier", help="Disable warning when attributes are not valid identifiers",      action="store_true", default=False)
  argparser.add_argument(      "--fix-identifiers",     dest="fix_identifiers",     help="Replace invalid characters from identifiers with underscore",    action="store_true", default=False)
  argparser.add_argument(      "--chdir-src",           dest="chdir_src",           help="Change working directory to source before rendering ",           action="store_true", default=False)
  argparser.add_argument(      "--no-chdir",            dest="no_chdir",            help="Disable changing working directory before rendering",            action="store_true", default=False)
  argparser.add_argument(      "--csv-delimiter",       dest="csv_delimiter",       help="CSV delimiter (default: ',')",                                            )
  argparser.add_argument(      "--csv-escapechar",      dest="csv_escapechar",      help="CSV escape character (default: None)",                                    )
  argparser.add_argument(      "--csv-dontstrip",       dest="csv_dontstrip",       help="Disable stripping whitespace of CSV values",                     action="store_true", default=False)
  argparser.add_argument(      "--render-non-template", dest="render_non_template", help="Process also source files that are not recognized as templates", nargs='?',           default=None, const="_j2gpp")
  argparser.add_argument(      "--copy-non-template",   dest="copy_non_template",   help="Copy source files that are not templates to output directory",   action="store_true", default=False)
  argparser.add_argument(      "--force-glob",          dest="force_glob",          help="Glob UNIX-like patterns in path even when quoted",               action="store_true", default=False)
  argparser.add_argument(      "--debug-vars",          dest="debug_vars",          help="Display available variables at the top of rendered templates",   action="store_true", default=False)
  argparser.add_argument(      "--perf",                dest="perf",                help="Measure and display performance",                                action="store_true", default=False)
  argparser.add_argument(      "--version",             dest="version",             help="Print J2GPP version and quits",                                  action="store_true", default=False)
  argparser.add_argument(      "--license",             dest="license",             help="Print J2GPP license and quits",                                  action="store_true", default=False)
  args, args_unknown = argparser.parse_known_args()

  if args.version:
    print(j2gpp_version)
    exit()

  if args.license:
    print_license()
    exit()

  # Title after license and version argument parsing
  j2gpp_title()
  print(f"Python version :",python_version())
  print(f"Jinja2 version :",jinja2_version)
  print(f"J2GPP  version :",j2gpp_version)

  # Backup command working directory
  pwd = os.getcwd()

  # Parsing command line arguments
  throw_h2("Parsing command line arguments")

  # Enable performance monitor
  if args.perf:
    perf_counter = perf_counter_start()

  # Report unknown command line arguments
  if args_unknown:
    throw_error(f"Incorrect arguments '{' '.join(args_unknown)}'.")

  # Source files and directories
  arg_source = args.source
  if not arg_source:
    throw_error("Must provide at least one source template.")
    exit()

  # Output directory
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

  # Output file if single source template
  one_out_path = ""
  if args.output:
    # Get full path
    one_out_path = os.path.expandvars(os.path.expanduser(os.path.abspath(args.output)))
    one_out_dir = os.path.dirname(one_out_path)
    # Create directories if needed
    if not os.path.isdir(one_out_dir):
      os.makedirs(one_out_dir)
    print("Output file :",out_dir)

  # Jinja2 include directories
  inc_dirs = []
  if args.incdir:
    print("Include directories :")
    for inc_dir in args.incdir:
      # Get full path
      inc_dir = os.path.expandvars(os.path.expanduser(os.path.abspath(inc_dir)))
      print(" ",inc_dir)
      inc_dirs.append(inc_dir)
  else: print("No include directory provided.")

  # Global variable defines
  defines = []
  if args.define:
    defines = args.define
    print("Global variables defined :")
    for define in defines:
      print(" ",define)
  else: print("No global variables defined.")

  # Global variable files
  global_var_paths = []
  if args.varfile:
    print("Global variables files :")
    for var_path in args.varfile:
      # Get full path
      var_path = os.path.expandvars(os.path.expanduser(os.path.abspath(var_path)))
      print(" ",var_path)
      global_var_paths.append(var_path)
  else: print("No global variables file provided.")

  # Loading environment variables as global variables
  envvar_raw = None
  envvar_obj = None
  if args.envvar is not None:
    print("Getting environment variables as global variables.")
    envvar_raw = os.environ
    envvar_obj = args.envvar

  # Custom Jinja2 filters
  filter_paths = []
  if args.filters:
    print("Extra Jinja2 filter files :")
    for filter_path in args.filters:
      # Get full path
      filter_path = os.path.expandvars(os.path.expanduser(os.path.abspath(filter_path)))
      print(" ", filter_path)
      filter_paths.append(filter_path)

  # Custom Jinja2 tests
  test_paths = []
  if args.tests:
    print("Extra Jinja2 test files :")
    for test_path in args.tests:
      # Get full path
      test_path = os.path.expandvars(os.path.expanduser(os.path.abspath(test_path)))
      print(" ", test_path)
      test_paths.append(test_path)

  # Variables files post processor
  vars_post_processor = None
  if args.vars_post_processor:
    vars_post_processor = args.vars_post_processor
    vars_post_processor[0] = os.path.expandvars(os.path.expanduser(os.path.abspath(vars_post_processor[0])))
    print(f"Variables files post processor :\n  {args.vars_post_processor[1]} from {args.vars_post_processor[0]}")

  # Debug mode
  debug_vars = args.debug_vars
  if debug_vars:
    print("Debug enabled : display available variables at the top of the rendered templates.")

  # Other options
  options['overwrite_outdir']    = args.overwrite_outdir
  options['warn_overwrite']      = args.warn_overwrite
  options['no_overwrite']        = args.no_overwrite
  options['no_check_identifier'] = args.no_check_identifier
  options['fix_identifiers']     = args.fix_identifiers
  options['chdir_src']           = args.chdir_src
  options['no_chdir']            = args.no_chdir
  options['csv_delimiter']       = args.csv_delimiter if args.csv_delimiter else ','
  options['csv_escapechar']      = args.csv_escapechar
  options['csv_dontstrip']       = args.csv_dontstrip
  options['render_non_template'] = args.render_non_template
  options['copy_non_template']   = args.copy_non_template
  options['force_glob']          = args.force_glob

  # Error checking command line options
  if options['overwrite_outdir'] and not out_dir:
    throw_warning("Overwrite output directory option enabled but no output directory provided. Option --overwrite-outdir is ignored.")
    options['overwrite_outdir'] = False

  if options['warn_overwrite'] and options['no_overwrite']:
    throw_warning("Incompatible --warn-overwrite and --no-overwrite options. Option --warn-overwrite is ignored.")
    options['warn_overwrite'] = False

  if options['overwrite_outdir'] and options['no_overwrite']:
    throw_warning("Incompatible --overwrite-outdir and --no-overwrite options. Option --no-overwrite is ignored.")
    options['no_overwrite'] = False

  if options['no_check_identifier'] and options['fix_identifiers']:
    throw_warning("Incompatible --no-check-identifier and --fix-identifiers options. Option --no-check-identifier is ignored.")
    options['no_check_identifier'] = False

  if options['chdir_src'] and options['no_chdir']:
    throw_warning("Incompatible --chdir-src and --no-chdir options. Option --no-chdir is ignored.")
    options['no_chdir'] = False

  if options['render_non_template'] and options['copy_non_template']:
    throw_warning("Incompatible --render-non-template and --copy-non-template options. Option --copy-non-template is ignored.")
    options['copy_non_template'] = False

  # Jinja2 environment
  env = Environment(
    loader=FileSystemLoader(inc_dirs)
  )
  env.add_extension('jinja2.ext.do')
  env.add_extension('jinja2.ext.debug')



  # ┌────────────────────────┐
  # │ Loading plugin scripts │
  # └────────────────────────┘

  throw_h2("Loading plugin scripts")

  print("Loading J2GPP built-in filters.")
  env.filters.update(extra_filters)

  print("Loading J2GPP built-in tests.")
  env.tests.update(extra_tests)

  # Extra Jinja2 filters
  if filter_paths:
    filters = {}
    for filter_path in filter_paths:
      filter_module = imp.load_source("", filter_path)
      for filter_name in dir(filter_module):
        if filter_name[0] != '_':
          print(f"Loading filter '{filter_name}' from '{filter_path}'.")
          filter_function = getattr(filter_module, filter_name)
          # Check if function, else could be module or variable
          if callable(filter_function):
            filters[filter_name] = filter_function
    env.filters.update(filters)

  # Extra Jinja2 tests
  if test_paths:
    tests = {}
    for test_path in test_paths:
      test_module = imp.load_source("", test_path)
      for test_name in dir(test_module):
        if test_name[0] != '_':
          test_function = getattr(test_module, test_name)
          # Check if function, else could be module or variable
          if callable(test_function):
            print(f"Loading test '{test_name}' from '{test_path}'.")
            tests[test_name] = test_function
    env.tests.update(tests)

  # Variables files post processor
  postproc_function = None
  if vars_post_processor:
    postproc_path = vars_post_processor[0]
    postproc_name = vars_post_processor[1]
    print(f"Loading variable postprocessor function '{postproc_name}' from '{postproc_path}'.")
    try:
      postproc_module = imp.load_source("", postproc_path)
      postproc_function = getattr(postproc_module, postproc_name)
      if not callable(postproc_function):
        throw_error(f"Object '{postproc_name}' from '{postproc_path}' is not a function.")
        postproc_function = None
    except FileNotFoundError as exc:
      throw_error(f"Script file '{postproc_path}' doesn't exist or cannot be read.")
      postproc_function = None
    except AttributeError as exc:
      throw_error(f"Function '{postproc_name}' cannot be found in script '{postproc_path}'.")
      postproc_function = None



  # ┌───────────────────────┐
  # │ Fetching source files │
  # └───────────────────────┘

  throw_h2("Fetching source files")

  # Fetch source template file
  def fetch_source_file(src_path, dir_path="", warn_non_template=False):
    # Templates end with .j2 extension
    is_template = src_path.endswith('.j2')

    # Output file name
    if is_template:
      print(f"Found template source {src_path}")
      # Strip .j2 extension for output path
      out_path = src_path[:-3]
    elif options['copy_non_template']:
      print(f"Found non-template file {src_path}")
      out_path = src_path
    elif options['render_non_template']:
      print(f"Found non-template source file {src_path}")
      # Add the option suffix before file extensions if present
      if '.' in src_path:
        out_path = src_path.replace('.', options['render_non_template']+'.', 1)
      else:
        out_path = src_path + options['render_non_template']
    else:
      if warn_non_template:
        throw_warning(f"Source file '{src_path}' is not a template.")
      return

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
    if not is_template and options['copy_non_template']:
      to_copy.append(src_dict)
    else:
      sources.append(src_dict)

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

  # Some checking
  if len(sources) == 0 and len(to_copy) == 0:
    throw_error(f"No source template found.")
  elif one_out_path and len(sources) > 1:
    throw_error(f"Multiple source templates provided alongside -o/--output argument.")



  # ┌───────────────────┐
  # │ Loading variables │
  # └───────────────────┘

  throw_h2("Loading variables")

  # Merge two dictionaries
  def var_dict_update(var_dict1, var_dict2, val_scope="", context=""):
    var_dict_res = var_dict1
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

  # Check that attributes names are valid Python identifier that can be accessed in Jinja2
  def rec_check_valid_identifier(var_dict, context_file=None, val_scope=""):
    for key, val in var_dict.copy().items():
      # Valid identifier contains only alphanumeric letters and underscores, and cannot start with a number
      if not key.isidentifier():
        if options['fix_identifiers']:
          key_valid = re.sub('\W|^(?=\d)','_', key)
          var_dict[key_valid] = val
          del var_dict[key]
          key = key_valid
        else:
          throw_warning(f"Variable '{val_scope}{key}' from '{context_file}' is not a valid Python identifier and may not be accessible in the templates.")
      if isinstance(val, dict):
        val_scope = f"{val_scope}{key}."
        # Traverse the dictionary recursively
        rec_check_valid_identifier(var_dict[key], context_file, val_scope)

  # Handle hierarchical includes of variables files
  load_var_file = None
  def rec_hierarchical_vars(var_dict, context_file=None):
    for key,val in var_dict.copy().items():
      if key == "__j2gpp_include__":
        # Remove include statement
        del var_dict[key]
        # If single include then make list
        if not isinstance(val,list):
          val = [val]
        for var_path in val:
          # Get full path relative to parent file
          var_path = os.path.join(os.path.dirname(context_file),var_path)
          print(f"Including variables file '{var_path}'\n                    from '{context_file}'.")
          # Recursively load the variable file (including its preprocessing)
          inc_var_dict = load_var_file(var_path)
          # Update the variables dictionary
          var_dict = var_dict_update(var_dict, inc_var_dict, context=f" when including '{var_path}' from '{context_file}'")
      elif isinstance(val, dict):
        # Traverse the dictionary recursively
        rec_hierarchical_vars(val, context_file)

  # Process the variables directory after loading
  def vars_postprocessor(var_dict, context_file=None):
    # Include variables files from others
    rec_hierarchical_vars(var_dict, context_file)
    # User postprocessor function
    if postproc_function:
      postproc_function(var_dict)
    # Check attributes are valid identifier
    if not options['no_check_identifier']:
      rec_check_valid_identifier(var_dict, context_file)

  # Load variables from a file and return the dictionary
  def load_var_file(var_path):
    var_dict = {}
    var_format = var_path.split('.')[-1]
    if var_format in loaders:
      loader = loaders[var_format]
      try:
        var_dict = loader(var_path)
        vars_postprocessor(var_dict, var_path)
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

  # Setting context global variables
  print(f"Setting context global variables.")
  context_dict = {
    '__python_version__'    : python_version(),
    '__jinja2_version__'    : jinja2_version,
    '__j2gpp_version__'     : j2gpp_version,
    '__user__'              : os.getlogin(),
    '__pid__'               : os.getpid(),
    '__ppid__'              : os.getppid(),
    '__working_directory__' : os.getcwd(),
    '__output_directory__'  : out_dir if out_dir else os.getcwd(),
    '__date__'              : datetime.now().strftime("%d-%m-%Y"),
    '__date_inv__'          : datetime.now().strftime("%Y-%m-%d"),
    '__time__'              : datetime.now().strftime("%H:%M:%S"),
    '__datetime__'          : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
  }
  global_vars = var_dict_update(global_vars, context_dict, context=f" when setting context variables")

  # Loading global variables from environment variables
  if envvar_raw:
    print(f"Loading global variables from environment variables.")
    envvar_dict = {}
    for var, val in envvar_raw.items():
      # Evaluate value to correct type
      envvar_dict[var] = auto_cast_str(val)
    # Store in root object if envvar argument provided
    if envvar_obj:
      envvar_dict = {envvar_obj: envvar_dict}
    # Merge with global variables dictionary
    global_vars = var_dict_update(global_vars, envvar_dict, context=f" when loading environment variables")

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

  # Option to overwrite the output directory
  if options['overwrite_outdir']:
    print(f"Overwriting output directory.")
    try:
      shutil.rmtree(out_dir)
    except Exception as exc:
      throw_error(f"Cannot remove output directory '{out_dir}'.")

  # Render all templates
  for src_dict in sources:
    src_path = src_dict['src_path']
    out_path = src_dict['out_path']
    print(f"Rendering {src_path} \n       to {out_path}")
    src_dirpath = os.path.dirname(src_path)
    out_dirpath = os.path.dirname(out_path)
    src_res = ""

    # Do render the source template, can be skipped by export filter option
    write_source_toggle[0] = True

    # Create directories for output path
    try:
      os.makedirs(out_dirpath, exist_ok=True)
    except OSError as exc:
        throw_error(f"Cannot create directory '{out_dirpath}'.")

    # Change working directory to output directory for filters and accessory functions
    if options['no_chdir']:
      pass
    elif options['chdir_src']:
      change_working_directory(src_dirpath)
    else:
      change_working_directory(out_dirpath)

    # Add context variables specific to this template
    src_vars = global_vars.copy()
    src_context_vars = {
      '__source_path__': src_path,
      '__output_path__': out_path,
    }
    src_vars = var_dict_update(src_vars, src_context_vars, context=f" when loading context variables for template {src_path}")

    # Output variables for debug purposes
    if debug_vars:
      src_res += str(src_vars) + 10*'\n'

    # Render template to string
    try:
      with open(src_path,'r') as src_file:
        # Jinja2 rendering from string
        src_res += env.from_string(src_file.read()).render(src_vars)
    except OSError as exc:
      # Catch file read exceptions
      if exc.errno == errno.ENOENT:
        throw_error(f"Cannot read '{src_path}' : file doesn't exist.")
      elif exc.errno == errno.EACCES:
        throw_error(f"Cannot read '{src_path}' : missing read permission.")
      else:
        throw_error(f"Cannot read '{src_path}'.")
    except Exception as exc:
      # Catch all other exceptions such as Jinja2 errors
      throw_error(f"Exception occurred while rendering '{src_path}' : \n  {type(exc).__name__}\n{intend_text(exc)}")

    if not write_source_toggle[0]:
      print(f"Not writting file '{out_path}' becaused skipped by exported block.")
      continue

    # If file already exists
    if os.path.exists(out_path):
      if options['warn_overwrite']:
        throw_warning(f"Output file '{out_path}' already exists and will be overwritten.")
      elif options['no_overwrite']:
        throw_warning(f"Output file '{out_path}' already exists and will not be overwritten.")
        continue

    # Write the rendered file
    try:
      with open(out_path,'w') as out_file:
        out_file.write(src_res)
    except OSError as exc:
      # Catch file write exceptions
      if exc.errno == errno.EISDIR:
        throw_error(f"Cannot write '{out_path}' : path is a directory.")
      elif exc.errno == errno.EACCES:
        throw_error(f"Cannot write '{out_path}' : missing write permission.")
      else:
        throw_error(f"Cannot write '{out_path}'.")

  # Restore command working directory
  change_working_directory(pwd)

  # If option is set, copy the non-template files
  if options['copy_non_template']:
    for cpy_dict in to_copy:
      cpy_path = cpy_dict['src_path']
      out_path = cpy_dict['out_path']
      print(f"Copying {cpy_path} \n     to {out_path}")

      # If file already exists
      if os.path.exists(out_path):
        print("File already exists")
        if options['warn_overwrite']:
          throw_warning(f"Output file '{out_path}' already exists and will be overwritten.")
        elif options['no_overwrite']:
          throw_warning(f"Output file '{out_path}' already exists and will not be overwritten.")
          continue

      # Copying the file
      try:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        shutil.copyfile(cpy_path, out_path)
      except shutil.SameFileError as exc:
        throw_error(f"Cannot write '{out_path}' : source and destination paths are identical.")
      except OSError as exc:
        # Catch file write exceptions
        if exc.errno == errno.EISDIR:
          throw_error(f"Cannot write '{out_path}' : path is a directory.")
        elif exc.errno == errno.EACCES:
          throw_error(f"Cannot write '{out_path}' : missing write permission.")
        else:
          throw_error(f"Cannot write '{out_path}'.")



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
