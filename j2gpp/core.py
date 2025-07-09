# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     j2gpp - Jinja2-based General Purpose Preprocessor            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        core.py                                                      ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Core J2GPP processing functions.                             ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



import os
import glob
import errno
import shutil
from typing import Dict, Any, List, Optional

from jinja2 import Environment, FileSystemLoader, StrictUndefined
import jinja2.exceptions as jinja2_exceptions

from j2gpp.results import (
  RenderResult,
  FileRenderResult
)
from j2gpp.utils import (
  throw_error,
  throw_warning,
  change_working_directory,
  load_module,
  jinja2_render_traceback
)
from j2gpp.filters import (
  extra_filters,
  write_source_toggle
)
from j2gpp.tests import extra_tests



class RelativeIncludeEnvironment(Environment):
  """Jinja2 environment with relative include support"""
  def join_path(self, template, parent):
    return os.path.join(os.path.dirname(parent), template)


def setup_jinja_environment(include_dirs: List[str]     = None,
                            filter_paths: List[str]     = None,
                            test_paths:   List[str]     = None,
                            options:      Dict[str,Any] = None,
                            ) -> Environment:
  """Set up Jinja2 environment with filters, tests, and options"""
  if include_dirs is None:
    include_dirs = []
  if filter_paths is None:
    filter_paths = []
  if test_paths is None:
    test_paths = []
  if options is None:
    options = {}

  # Create Jinja2 environment
  env = RelativeIncludeEnvironment(
    loader=FileSystemLoader(include_dirs)
  )
  env.add_extension('jinja2.ext.do')
  env.add_extension('jinja2.ext.debug')

  if not options.get('no_strict_undefined', False):
    env.undefined = StrictUndefined

  # Load built-in filters and tests
  env.filters.update(extra_filters)
  env.tests.update(extra_tests)

  # Load custom filters
  if filter_paths:
    filters = {}
    for filter_path in filter_paths:
      if os.path.isfile(filter_path):
        filter_module = load_module("", filter_path)
        for filter_name in dir(filter_module):
          if filter_name[0] != '_':
            filter_function = getattr(filter_module, filter_name)
            if callable(filter_function):
              filters[filter_name] = filter_function
    env.filters.update(filters)

  # Load custom tests
  if test_paths:
    tests = {}
    for test_path in test_paths:
      if os.path.isfile(test_path):
        test_module = load_module("", test_path)
        for test_name in dir(test_module):
          if test_name[0] != '_':
            test_function = getattr(test_module, test_name)
            if callable(test_function):
              tests[test_name] = test_function
    env.tests.update(tests)

  return env


def process_single_file(source_path: str,
                        output_path: str,
                        jinja_env:   Environment,
                        variables:   Dict[str,Any],
                        options:     Dict[str,Any] = None,
                        working_dir: Optional[str] = None,
                        ) -> FileRenderResult:
  """Process a single template file"""
  if options is None:
    options = {}

  # Backup current working directory
  original_wd = os.getcwd()

  try:
    # Change working directory if specified
    if working_dir:
      change_working_directory(working_dir)

    # Check if it's a template
    is_template = source_path.endswith('.j2')

    # Create output directory
    output_dir = os.path.dirname(output_path)
    try:
      os.makedirs(output_dir, exist_ok=True)
    except OSError as exc:
      error_msg = f"Cannot create directory '{output_dir}'."
      return FileRenderResult(source_path, output_path, False, error_msg, is_template)

    # Handle non-template files
    if not is_template:
      if options.get('copy_non_template', False):
        try:
          shutil.copyfile(source_path, output_path)
          return FileRenderResult(source_path, output_path, True, None, False, True)
        except Exception as exc:
          error_msg = f"Cannot copy '{source_path}' to '{output_path}': {exc}"
          return FileRenderResult(source_path, output_path, False, error_msg, False)
      else:
        # Skip non-templates
        return FileRenderResult(source_path, output_path, True, "Skipped non-template", False)

    # Process template file
    src_res = ""

    # Reset write source toggle
    write_source_toggle[0] = True

    # Add context variables specific to this template
    template_vars = variables.copy()
    template_vars.update({
      '__source_path__': source_path,
      '__output_path__': output_path,
    })

    # Output variables for debug purposes
    if options.get('debug_vars', False):
      src_res += str(template_vars) + 10*'\n'

    # Render template to string
    try:
      with open(source_path, 'r') as src_file:
        # Jinja2 rendering from string
        src_res += jinja_env.from_string(src_file.read()).render(template_vars)
    except jinja2_exceptions.UndefinedError as exc:
      # Undefined object encountered during rendering
      try:
        traceback = jinja2_render_traceback(source_path)
      except Exception as exc:
        throw_error(f"Exception occured while rendering the traceback of a previous Jinja2 exception for template '{source_path}':\n      {exc.message}")
      error_msg = f"Undefined object encountered while rendering '{source_path}' :\n{traceback}\n      {exc.message}"
      return FileRenderResult(source_path, output_path, False, error_msg, is_template)
    except jinja2_exceptions.TemplateSyntaxError as exc:
      # Syntax error encountered during rendering
      try:
        traceback = jinja2_render_traceback(source_path)
      except Exception as exc:
        throw_error(f"Exception occured while rendering the traceback of a previous Jinja2 exception for template '{source_path}':\n      {exc.message}")
      error_msg = f"Syntax error encountered while rendering '{source_path}' :\n{traceback}\n      {exc.message}"
      return FileRenderResult(source_path, output_path, False, error_msg, is_template)
    except jinja2_exceptions.TemplateNotFound as exc:
      # Template not found
      try:
        traceback = jinja2_render_traceback(source_path)
      except Exception as exc:
        throw_error(f"Exception occured while rendering the traceback of a previous Jinja2 exception for template '{source_path}':\n      {exc.message}")
      error_msg = f"Included template '{exc}' not found :\n{traceback}"
      return FileRenderResult(source_path, output_path, False, error_msg, is_template)
    except OSError as exc:
      # Catch file read exceptions
      if exc.errno == errno.ENOENT:
        error_msg = f"Cannot read '{source_path}' : file doesn't exist."
      elif exc.errno == errno.EACCES:
        error_msg = f"Cannot read '{source_path}' : missing read permission."
      else:
        error_msg = f"Cannot read '{source_path}'."
      return FileRenderResult(source_path, output_path, False, error_msg, is_template)
    except Exception as exc:
      # Catch all other Python exceptions
      try:
        traceback = jinja2_render_traceback(source_path, including_non_template=True)
      except Exception as exc:
        throw_error(f"Exception occured while rendering the traceback of a previous Jinja2 exception for template '{source_path}':\n      {exc.message}")
      error_msg = f"Exception occurred while rendering '{source_path}' :\n{traceback}\n      {type(exc).__name__} - {exc}"
      return FileRenderResult(source_path, output_path, False, error_msg, is_template)

    # Trim trailing whitespace
    if options.get('trim_whitespace', False):
      src_res = src_res.rstrip()

    # Check if write was skipped by export filter
    if not write_source_toggle[0]:
      return FileRenderResult(source_path, output_path, True, "Skipped by export filter", is_template)

    # Check if file already exists
    if os.path.exists(output_path):
      if options.get('warn_overwrite', False):
        throw_warning(f"Output file '{output_path}' already exists and will be overwritten.")
      elif options.get('no_overwrite', False):
        return FileRenderResult(source_path, output_path, True, "Skipped to avoid overwrite", is_template)

    # Write the rendered file
    try:
      with open(output_path, 'w') as out_file:
        out_file.write(src_res)
    except OSError as exc:
      # Catch file write exceptions
      if exc.errno == errno.EISDIR:
        error_msg = f"Cannot write '{output_path}' : path is a directory."
      elif exc.errno == errno.EACCES:
        error_msg = f"Cannot write '{output_path}' : missing write permission."
      else:
        error_msg = f"Cannot write '{output_path}'."
      return FileRenderResult(source_path, output_path, False, error_msg, is_template)

    return FileRenderResult(source_path, output_path, True, None, is_template)

  finally:
    # Restore original working directory
    change_working_directory(original_wd)


def process_directory(source_dir: str,
                      output_dir: str,
                      jinja_env:  Environment,
                      variables:  Dict[str,Any],
                      options:    Dict[str,Any] = None,
                      )-> RenderResult:
  """Process all templates in a directory"""
  if options is None:
    options = {}

  result = RenderResult()

  # Check directory permissions
  if not os.access(source_dir, os.R_OK | os.X_OK):
    result.add_error(f"Missing access permissions for source directory '{source_dir}'.")
    return result

  # Walk through directory
  for subdir, dirs, files in os.walk(source_dir):
    for filename in files:
      source_path = os.path.join(subdir, filename)

      # Calculate relative output path
      rel_path = os.path.relpath(source_path, source_dir)

      # Strip .j2 extension for templates
      if rel_path.endswith('.j2'):
        output_rel_path = rel_path[:-3]
      elif options.get('render_non_template'):
        # Add suffix for non-templates if option is set
        if '.' in rel_path:
          output_rel_path = rel_path.replace('.', options['render_non_template'] + '.', 1)
        else:
          output_rel_path = rel_path + options['render_non_template']
      else:
        output_rel_path = rel_path

      output_path = os.path.join(output_dir, output_rel_path)

      # Determine working directory
      working_dir = None
      if options.get('chdir_src', False):
        working_dir = os.path.dirname(source_path)
      elif not options.get('no_chdir', False):
        working_dir = os.path.dirname(output_path)

      # Process the file
      file_result = process_single_file(
        source_path, output_path, jinja_env, variables, options, working_dir
      )

      result.add_file_result(file_result)

      # Add error to result if file processing failed
      if not file_result.success and file_result.error_message:
        result.add_error(file_result.error_message)

  return result


def render_template_string(template_string: str,
                           variables:       Dict[str,Any] = None,
                           include_dirs:    List[str]     = None,
                           options:         Dict[str,Any] = None,
                           ) -> str:
  """Quick utility to render a template string"""
  if variables is None:
    variables = {}
  if options is None:
    options = {}

  env = setup_jinja_environment(include_dirs=include_dirs, options=options)
  return env.from_string(template_string).render(variables)
