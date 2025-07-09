# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     j2gpp - Jinja2-based General Purpose Preprocessor            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        cli.py                                                       ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Command Line Interface using the J2GPP engine.               ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



import argparse
import glob
import os
import sys
from platform import python_version

from jinja2 import __version__ as jinja2_version

from j2gpp.engine import J2GPP
from j2gpp.results import (
  RenderResult,
  FileRenderResult
)
from j2gpp.utils import (
  j2gpp_title,
  throw_h2,
  throw_error,
  throw_warning,
  get_j2gpp_version,
  print_license,
  error_warning_summary,
  perf_counter_start,
  perf_counter_stop,
  perf_counter_print,
  set_errors_output_stream,
  errors,
  warnings,
  load_module
)



def parse_arguments():
  """Parse command line arguments"""
  argparser = argparse.ArgumentParser()
  argparser.add_argument("source",                                                        help="Source template files or directories to render",                        nargs='*')
  argparser.add_argument("-O", "--outdir",                 dest="outdir",                 help="Output directory path"                                                           )
  argparser.add_argument("-o", "--output",                 dest="output",                 help="Output file path for single source template"                                     )
  argparser.add_argument("-I", "--incdir",                 dest="incdir",                 help="Include directories for include and import Jinja2 statements",          nargs='+')
  argparser.add_argument("-D", "--define",                 dest="define",                 help="Define global variables in the format name=value",                      action="append")
  argparser.add_argument("-V", "--varfile",                dest="varfile",                help="Global variables files",                                                nargs='+')
  argparser.add_argument(      "--envvar",                 dest="envvar",                 help="Loads environment variables as global variables",                       nargs='?',           default=None, const="")
  argparser.add_argument(      "--filters",                dest="filters",                help="Load extra Jinja2 filters from a Python file",                          nargs='+')
  argparser.add_argument(      "--tests",                  dest="tests",                  help="Load extra Jinja2 tests from a Python file",                            nargs='+')
  argparser.add_argument(      "--file-vars-adapter",      dest="file_vars_adapter",      help="Load a Python function to process variables after loading from a file", nargs=2  )
  argparser.add_argument(      "--global-vars-adapter",    dest="global_vars_adapter",    help="Load a Python function to process all variables before rendering",      nargs=2  )
  argparser.add_argument(      "--overwrite-outdir",       dest="overwrite_outdir",       help="Overwrite output directory",                                            action="store_true", default=False)
  argparser.add_argument(      "--warn-overwrite",         dest="warn_overwrite",         help="Warn when overwriting files",                                           action="store_true", default=False)
  argparser.add_argument(      "--no-overwrite",           dest="no_overwrite",           help="Prevent overwriting files",                                             action="store_true", default=False)
  argparser.add_argument(      "--no-strict-undefined",    dest="no_strict_undefined",    help="Disable error with undefined variable in template",                     action="store_true", default=False)
  argparser.add_argument(      "--no-check-identifier",    dest="no_check_identifier",    help="Disable warning when attributes are not valid identifiers",             action="store_true", default=False)
  argparser.add_argument(      "--fix-identifiers",        dest="fix_identifiers",        help="Replace invalid characters from identifiers with underscore",           action="store_true", default=False)
  argparser.add_argument(      "--chdir-src",              dest="chdir_src",              help="Change working directory to source before rendering",                   action="store_true", default=False)
  argparser.add_argument(      "--no-chdir",               dest="no_chdir",               help="Disable changing working directory before rendering",                   action="store_true", default=False)
  argparser.add_argument(      "--trim-whitespace",        dest="trim_whitespace",        help="Trim trailing whitespace in generated files",                           action="store_true", default=False)
  argparser.add_argument(      "--csv-delimiter",          dest="csv_delimiter",          help="CSV delimiter (default: ',')",                                                   )
  argparser.add_argument(      "--csv-escape-char",        dest="csv_escape_char",        help="CSV escape character (default: None)",                                           )
  argparser.add_argument(      "--csv-dont-strip",         dest="csv_dont_strip",         help="Disable stripping whitespace of CSV values",                            action="store_true", default=False)
  argparser.add_argument(      "--xml-convert-attributes", dest="xml_convert_attributes", help="Convert XML attributes to normal element without the '@' prefix",       action="store_true", default=False)
  argparser.add_argument(      "--xml-remove-namespaces",  dest="xml_remove_namespaces",  help="Remove XML namespace prefixes from tags",                               action="store_true", default=False)
  argparser.add_argument(      "--render-non-template",    dest="render_non_template",    help="Process also source files that are not recognized as templates",        nargs='?',           default=None, const="_j2gpp")
  argparser.add_argument(      "--copy-non-template",      dest="copy_non_template",      help="Copy source files that are not templates to output directory",          action="store_true", default=False)
  argparser.add_argument(      "--force-glob",             dest="force_glob",             help="Glob UNIX-like patterns in path even when quoted",                      action="store_true", default=False)
  argparser.add_argument(      "--debug-vars",             dest="debug_vars",             help="Display available variables at the top of rendered templates",          action="store_true", default=False)
  argparser.add_argument(      "--stdout-errors",          dest="stdout_errors",          help="Display errors on stdout instead of stderr",                            action="store_true", default=False)
  argparser.add_argument(      "--perf",                   dest="perf",                   help="Measure and display performance",                                       action="store_true", default=False)
  argparser.add_argument(      "--version",                dest="version",                help="Print J2GPP version and quits",                                         action="store_true", default=False)
  argparser.add_argument(      "--license",                dest="license",                help="Print J2GPP license and quits",                                         action="store_true", default=False)

  return argparser.parse_known_args()


def configure_engine_from_args(engine: J2GPP, args) -> None:
  """Configure J2GPP engine from parsed CLI arguments"""

  # Set all options
  option_mapping = {
    'no_strict_undefined':    args.no_strict_undefined,
    'debug_vars':             args.debug_vars,
    'no_check_identifier':    args.no_check_identifier,
    'fix_identifiers':        args.fix_identifiers,
    'chdir_src':              args.chdir_src,
    'no_chdir':               args.no_chdir,
    'csv_delimiter':          args.csv_delimiter if args.csv_delimiter else ',',
    'csv_escape_char':        args.csv_escape_char,
    'csv_dont_strip':         args.csv_dont_strip,
    'xml_convert_attributes': args.xml_convert_attributes,
    'xml_remove_namespaces':  args.xml_remove_namespaces,
    'render_non_template':    args.render_non_template,
    'copy_non_template':      args.copy_non_template,
    'warn_overwrite':         args.warn_overwrite,
    'no_overwrite':           args.no_overwrite,
    'overwrite_outdir':       args.overwrite_outdir,
  }

  for option_name, value in option_mapping.items():
    engine.set_option(option_name, value)

  # Set include directories
  if args.incdir:
    engine.set_include_directories(args.incdir)

  # Load custom filters and tests
  if args.filters:
    for filter_path in args.filters:
      engine.load_filters_from_file(filter_path)

  if args.tests:
    for test_path in args.tests:
      engine.load_tests_from_file(test_path)

  # Set adapter functions
  if args.file_vars_adapter:
    file_vars_adapter_path = args.file_vars_adapter[0]
    file_vars_adapter_name = args.file_vars_adapter[1]
    try:
      file_vars_adapter_module = load_module("", file_vars_adapter_path)
      file_vars_adapter_function = getattr(file_vars_adapter_module, file_vars_adapter_name)
      engine.set_file_vars_adapter(file_vars_adapter_function)
    except Exception as exc:
      throw_error(f"Cannot load file vars adapter function '{file_vars_adapter_name}' from '{file_vars_adapter_path}': {exc}")

  if args.global_vars_adapter:
    global_vars_adapter_path = args.global_vars_adapter[0]
    global_vars_adapter_name = args.global_vars_adapter[1]
    try:
      global_vars_adapter_module = load_module("", global_vars_adapter_path)
      global_vars_adapter_function = getattr(global_vars_adapter_module, global_vars_adapter_name)
      engine.set_global_vars_adapter(global_vars_adapter_function)
    except Exception as exc:
      throw_error(f"Cannot load global vars adapter function '{global_vars_adapter_name}' from '{global_vars_adapter_path}': {exc}")


def load_variables_from_args(engine: J2GPP, args) -> None:
  """Load variables from CLI arguments into engine"""

  # Load variables from files
  if args.varfile:
    print("Global variables files :")
    for var_path in args.varfile:
      var_path = os.path.expandvars(os.path.expanduser(os.path.abspath(var_path)))
      print(" ", var_path)
      engine.load_variables_from_file(var_path)
  else:
    print("No global variables file provided.")

  # Load environment variables
  if args.envvar is not None:
    print("Getting environment variables as global variables.")
    engine.load_variables_from_env(args.envvar if args.envvar else None)

  # Load variables from defines
  if args.define:
    print("Global variables defined :")
    for define in args.define:
      print(" ", define)
      if '=' not in define:
        throw_error(f"Incorrect define argument format for '{define}'.")
        continue
      var, val = define.split('=', 1)
      engine.define_variable(var, val)
  else:
    print("No global variables defined.")


def collect_source_paths(args) -> list:
  """Collect and validate source paths from arguments"""
  source_paths = []

  for raw_path in args.source:
    if args.force_glob:
      # Glob to apply UNIX-style path patterns
      for glob_path in glob.glob(raw_path):
        abs_path = os.path.abspath(glob_path)
        source_paths.append(abs_path)
    else:
      abs_path = os.path.abspath(raw_path)
      source_paths.append(abs_path)

  return source_paths


def validate_arguments(args) -> None:
  """Validate argument combinations and report conflicts"""

  # Error checking command line options
  if args.overwrite_outdir and not args.outdir:
    throw_warning("Overwrite output directory option enabled but no output directory provided. Option --overwrite-outdir is ignored.")

  if args.warn_overwrite and args.no_overwrite:
    throw_warning("Incompatible --warn-overwrite and --no-overwrite options. Option --warn-overwrite is ignored.")

  if args.overwrite_outdir and args.no_overwrite:
    throw_warning("Incompatible --overwrite-outdir and --no-overwrite options. Option --no-overwrite is ignored.")

  if args.no_check_identifier and args.fix_identifiers:
    throw_warning("Incompatible --no-check-identifier and --fix-identifiers options. Option --no-check-identifier is ignored.")

  if args.chdir_src and args.no_chdir:
    throw_warning("Incompatible --chdir-src and --no-chdir options. Option --no-chdir is ignored.")

  if args.render_non_template and args.copy_non_template:
    throw_warning("Incompatible --render-non-template and --copy-non-template options. Option --copy-non-template is ignored.")


def process_sources_with_engine(engine: J2GPP, source_paths: list, args) -> list:
  """Process all source paths using the engine and return results"""
  results = []

  # Handle overwrite output directory option
  if args.overwrite_outdir and args.outdir:
    print(f"Overwriting output directory.")
    import shutil
    try:
      shutil.rmtree(args.outdir)
    except Exception as exc:
      throw_error(f"Cannot remove output directory '{args.outdir}'.")

  for source_path in source_paths:
    if os.path.isdir(source_path):
      # Process directory
      if not args.outdir:
        throw_error("Output directory required when processing directories.")
        continue

      print(f"Found source directory {source_path}")
      result = engine.render_directory(source_path, args.outdir)
      results.append(result)

    elif os.path.isfile(source_path):
      # Process single file
      print(f"Found template source {source_path}")

      if args.output:
        # Single output file specified
        result = engine.render_file(source_path, output_path=args.output)
        # Create single file result
        single_result = RenderResult()
        single_result.add_file_result(result)
        results.append(single_result)
      else:
        # Use output directory or current directory
        output_dir = args.outdir if args.outdir else os.getcwd()
        result = engine.render_file(source_path, output_dir=output_dir)
        # Create single file result
        single_result = RenderResult()
        single_result.add_file_result(result)
        results.append(single_result)
    else:
      throw_error(f"Unresolved source '{source_path}'.")

  return results


def handle_results(results: list) -> bool:
  """Handle and display results, return True if successful"""
  total_files = 0
  successful_files = 0
  has_errors = False

  for result in results:
    total_files += result.total_files
    successful_files += result.successful_files
    if not result.success:
      has_errors = True

    # Report individual file results
    for file_result in result.files:
      if file_result.success:
        if file_result.was_copied:
          print(f"Copying {file_result.source_path} \n     to {file_result.output_path}")
        elif file_result.is_template:
          print(f"Rendering {file_result.source_path} \n       to {file_result.output_path}")

        if file_result.error_message and "Skipped" in file_result.error_message:
          print(f"Not writing file '{file_result.output_path}' because {file_result.error_message.lower()}")
      else:
        if file_result.error_message:
          throw_error(file_result.error_message)

  # Check if any files were processed
  if total_files == 0:
    throw_error("No source template found.")
    return False

  return not has_errors


def main():
  """CLI entry point - refactored to use J2GPP engine"""

  # Get version info
  j2gpp_version = get_j2gpp_version()

  # Parse arguments
  args, args_unknown = parse_arguments()

  # Handle version and license early
  if args.version:
    print(j2gpp_version)
    sys.exit(0)

  if args.license:
    print_license()
    sys.exit(0)

  # Title after version and license argument parsing
  j2gpp_title()
  print(f"Python version :",python_version())
  print(f"Jinja2 version :",jinja2_version)
  print(f"J2GPP  version :",j2gpp_version)

  # Start parsing command line arguments
  throw_h2("Parsing command line arguments")

  # Set global error output stream setting
  if args.stdout_errors:
    print("Displaying errors on stdout instead of stderr.")
    set_errors_output_stream(sys.stdout)

  # Enable performance monitor
  perf_counter = None
  if args.perf:
    perf_counter = perf_counter_start()

  # Report unknown command line arguments
  if args_unknown:
    throw_error(f"Incorrect arguments '{' '.join(args_unknown)}'.")

  # Validate source arguments
  if not args.source:
    throw_error("Must provide at least one source template.")
    sys.exit(1)

  # Validate single output with multiple sources
  if args.output and len(args.source) > 1:
    throw_error("Multiple source templates provided alongside -o/--output argument.")

  # Output directory setup
  if args.outdir:
    out_dir = os.path.expandvars(os.path.expanduser(os.path.abspath(args.outdir)))
    if not os.path.isdir(out_dir):
      os.makedirs(out_dir)
    print("Output directory :\n ", out_dir)
  else:
    print("Output directory :\n ", os.getcwd())

  # Output file if single source template
  if args.output:
    one_out_path = os.path.expandvars(os.path.expanduser(os.path.abspath(args.output)))
    one_out_dir = os.path.dirname(one_out_path)
    if not os.path.isdir(one_out_dir):
      os.makedirs(one_out_dir)
    print("Output file :", args.output)

  # Display include directories
  if args.incdir:
    print("Include directories :")
    for inc_dir in args.incdir:
      inc_dir = os.path.expandvars(os.path.expanduser(os.path.abspath(inc_dir)))
      print(" ", inc_dir)
  else:
    print("No include directory provided.")

  # Display custom filters and tests
  if args.filters:
    print("Extra Jinja2 filter files :")
    for filter_path in args.filters:
      filter_path = os.path.expandvars(os.path.expanduser(os.path.abspath(filter_path)))
      print(" ", filter_path)

  if args.tests:
    print("Extra Jinja2 test files :")
    for test_path in args.tests:
      test_path = os.path.expandvars(os.path.expanduser(os.path.abspath(test_path)))
      print(" ", test_path)

  # Display adapter functions
  if args.file_vars_adapter:
    print(f"Variables files adapter function :\n  {args.file_vars_adapter[1]} from {args.file_vars_adapter[0]}")

  if args.global_vars_adapter:
    print(f"Global variables adapter function :\n  {args.global_vars_adapter[1]} from {args.global_vars_adapter[0]}")

  # Debug mode
  if args.debug_vars:
    print("Debug enabled : display available variables at the top of the rendered templates.")

  # Validate argument combinations
  validate_arguments(args)

  # Create and configure engine
  throw_h2("Loading plugin scripts")
  print("Loading J2GPP built-in filters.")
  print("Loading J2GPP built-in tests.")

  engine = J2GPP()
  configure_engine_from_args(engine, args)

  # Collect source paths
  throw_h2("Fetching source files")
  source_paths = collect_source_paths(args)

  # Load variables
  throw_h2("Loading variables")
  print("Setting context global variables.")
  load_variables_from_args(engine, args)

  # Render templates
  throw_h2("Rendering templates")
  results = process_sources_with_engine(engine, source_paths, args)

  # Handle results
  success = handle_results(results)

  # Print all errors and warnings at the end
  if errors or warnings:
    throw_h2("Error/warning summary")
    error_warning_summary()

  # Print the performance timer
  if args.perf:
    throw_h2("Performance")
    perf_counter_print(perf_counter_stop(perf_counter))

  throw_h2("Done")

  if errors:
    sys.exit(1)
  else:
    sys.exit(0)
