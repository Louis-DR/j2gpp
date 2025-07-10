# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     j2gpp - Jinja2-based General Purpose Preprocessor            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        engine.py                                                    ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Main J2GPP engine class for programmatic use.                ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



import os
from datetime import datetime
from platform import python_version
from typing import Dict, Any, List, Optional, Callable

from jinja2 import __version__ as jinja2_version
from jinja2 import Environment, TemplateSyntaxError, TemplateNotFound

from j2gpp.core import (
  setup_jinja_environment,
  process_single_file,
  process_directory,
  render_template_string
)
from j2gpp.results import (
  RenderResult,
  FileRenderResult,
  ValidationResult,
  DirectoryValidationResult
)
from j2gpp.loaders import (
  load_variables_from_file,
  load_variables_from_env_vars
)
from j2gpp.utils import (
  get_j2gpp_version,
  auto_cast_str,
  throw_warning,
  rec_check_valid_identifier,
  var_dict_update,
  load_module
)



class J2GPP:
  """Main J2GPP processing engine for programmatic use"""

  def __init__(self):
    # Global variables
    self.variables = {}

    # Rendering options
    self.options = {
      'no_strict_undefined':    False,
      'debug_vars':             False,
      'no_check_identifier':    False,
      'fix_identifiers':        False,
      'chdir_src':              False,
      'no_chdir':               False,
      'trim_whitespace':        False,
      'csv_delimiter':          ',',
      'csv_escape_char':        None,
      'csv_dont_strip':         False,
      'xml_convert_attributes': False,
      'xml_remove_namespaces':  False,
      'render_non_template':    None,
      'copy_non_template':      False,
      'warn_overwrite':         False,
      'no_overwrite':           False,
      'overwrite_outdir':       False,
    }

    # Output configuration
    self.output_directory = None

    # Jinja2 configuration
    self.include_dirs = []
    self.filters = {}
    self.tests   = {}

    # Adapter functions
    self.file_vars_adapter_function   = None
    self.global_vars_adapter_function = None

    # Cached Jinja2 environment
    self._jinja_env = None
    self._env_dirty = True



  # ┌─────────────────────┐
  # │ Variable Management │
  # └─────────────────────┘

  def define_variable(self, name: str, value: Any) -> 'J2GPP':
    """Define single variable with dot notation support (chainable)"""
    # Auto-cast string values
    if isinstance(value, str):
      value = auto_cast_str(value)

    # Handle dot notation (e.g., "config.debug" -> {"config": {"debug": value}})
    var_keys = name.split('.')[::-1]
    var_dict = {var_keys[0]: value}
    for var_key in var_keys[1:]:
      var_dict = {var_key: var_dict}

    self.variables = self._merge_variables(self.variables, var_dict)
    return self

  def define_variables(self, variables: Dict[str, Any]) -> 'J2GPP':
    """Add variables to global context (chainable)"""
    self.variables = self._merge_variables(self.variables, variables)
    return self

  def load_variables_from_file(self, file_path: str) -> 'J2GPP':
    """Load variables from YAML/JSON/TOML/etc file (chainable)"""
    var_dict = load_variables_from_file(file_path, self.options)
    if var_dict:
      # Apply post-processing
      var_dict = self._post_process_variables(var_dict, file_path)
      self.variables = self._merge_variables(self.variables, var_dict)
    return self

  def load_variables_from_env(self, prefix: Optional[str] = None) -> 'J2GPP':
    """Load environment variables (chainable)"""
    env_vars = load_variables_from_env_vars(os.environ, prefix)
    if env_vars:
      self.variables = self._merge_variables(self.variables, env_vars)
    return self



  # ┌───────────────┐
  # │ Configuration │
  # └───────────────┘

  def set_output_directory(self, output_dir: str) -> 'J2GPP':
    """Set the output directory for all file rendering (chainable)"""
    self.output_directory = os.path.abspath(output_dir)
    return self

  def set_include_directories(self, dirs: List[str]) -> 'J2GPP':
    """Set Jinja2 include directories (chainable)"""
    self.include_dirs = [os.path.abspath(d) for d in dirs]
    self._env_dirty = True
    return self

  def add_include_directory(self, dir_path: str) -> 'J2GPP':
    """Add single include directory (chainable)"""
    self.include_dirs.append(os.path.abspath(dir_path))
    self._env_dirty = True
    return self

  def set_option(self, option_name: str, value: Any) -> 'J2GPP':
    """Set rendering option (chainable)"""
    if option_name in self.options:
      self.options[option_name] = value
      self._env_dirty = True
    else:
      throw_warning(f"Unknown option '{option_name}' ignored.")
    return self

  def add_filter(self, name: str, function_callable: Callable) -> 'J2GPP':
    """Add a single filter function directly (chainable)"""
    if callable(function_callable):
      self.filters[name] = function_callable
      self._env_dirty = True
    else:
      throw_warning(f"Filter '{name}' must be callable.")
    return self

  def add_test(self, name: str, function_callable: Callable) -> 'J2GPP':
    """Add a single test function directly (chainable)"""
    if callable(function_callable):
      self.tests[name] = function_callable
      self._env_dirty = True
    else:
      throw_warning(f"Test '{name}' must be callable.")
    return self

  def add_filters(self, filters: Dict[str, Callable]) -> 'J2GPP':
    """Add multiple filter functions from dictionary (chainable)"""
    for name, function_callable in filters.items():
      self.add_filter(name, function_callable)
    return self

  def add_tests(self, tests: Dict[str, Callable]) -> 'J2GPP':
    """Add multiple test functions from dictionary (chainable)"""
    for name, function_callable in tests.items():
      self.add_test(name, function_callable)
    return self

  def load_filters_from_file(self, file_path: str) -> 'J2GPP':
    """Load custom Jinja2 filters from Python file (chainable)"""
    file_absolute_path = os.path.abspath(file_path)

    if os.path.isfile(file_absolute_path):
      try:
        filter_module = load_module("", file_absolute_path)
        for filter_name in dir(filter_module):
          if filter_name[0] != '_':
            filter_function = getattr(filter_module, filter_name)
            if callable(filter_function):
              self.add_filter(filter_name, filter_function)
      except Exception as exc:
        throw_warning(f"Could not load filters from '{file_absolute_path}': {exc}")
    else:
      throw_warning(f"Filter file '{file_absolute_path}' does not exist.")

    return self

  def load_tests_from_file(self, file_path: str) -> 'J2GPP':
    """Load custom Jinja2 tests from Python file (chainable)"""
    file_absolute_path = os.path.abspath(file_path)

    if os.path.isfile(file_absolute_path):
      try:
        test_module = load_module("", file_absolute_path)
        for test_name in dir(test_module):
          if test_name[0] != '_':
            test_function = getattr(test_module, test_name)
            if callable(test_function):
              self.add_test(test_name, test_function)
      except Exception as exc:
        throw_warning(f"Could not load tests from '{file_absolute_path}': {exc}")
    else:
      throw_warning(f"Test file '{file_absolute_path}' does not exist.")

    return self

  def set_file_vars_adapter(self, function_callable: Callable) -> 'J2GPP':
    """Set function to process variables after loading from files (chainable)"""
    if callable(function_callable):
      self.file_vars_adapter_function = function_callable
    else:
      throw_warning("File vars adapter must be callable.")
    return self

  def set_global_vars_adapter(self, function_callable: Callable) -> 'J2GPP':
    """Set function to process all variables before rendering (chainable)"""
    if callable(function_callable):
      self.global_vars_adapter_function = function_callable
    else:
      throw_warning("Global vars adapter must be callable.")
    return self



  # ┌──────────────────────────┐
  # │ Configuration Inspection │
  # └──────────────────────────┘

  def get_variables(self) -> Dict[str, Any]:
    """Get copy of current variables dictionary"""
    return self.variables.copy()

  def get_options(self) -> Dict[str, Any]:
    """Get copy of current options dictionary"""
    return self.options.copy()

  def get_filters(self) -> Dict[str, Callable]:
    """Get copy of current filters dictionary"""
    return self.filters.copy()

  def get_tests(self) -> Dict[str, Callable]:
    """Get copy of current tests dictionary"""
    return self.tests.copy()

  def get_include_directories(self) -> List[str]:
    """Get copy of current include directories list"""
    return self.include_dirs.copy()

  def get_output_directory(self) -> Optional[str]:
    """Get current output directory (None if not set)"""
    return self.output_directory

  def has_variable(self, name: str) -> bool:
    """Check if variable exists (supports dot notation for nested keys)"""
    var_keys = name.split('.')
    current = self.variables
    try:
      for key in var_keys:
        if not isinstance(current, dict) or key not in current:
          return False
        current = current[key]
      return True
    except (TypeError, KeyError):
      return False

  def has_filter(self, name: str) -> bool:
    """Check if filter is loaded"""
    return name in self.filters

  def has_test(self, name: str) -> bool:
    """Check if test is loaded"""
    return name in self.tests

  def has_include_directory(self, directory: str) -> bool:
    """Check if include directory is configured"""
    abs_dir = os.path.abspath(directory)
    return abs_dir in self.include_dirs



  # ┌─────────────────────┐
  # │ Template Validation │
  # └─────────────────────┘

  def validate_template_string(self, template_string: str) -> ValidationResult:
    """Validate template syntax without rendering"""
    try:
      # Create a minimal environment for parsing
      env = self._ensure_environment()
      # Parse the template to check for syntax errors
      env.parse(template_string)
      return ValidationResult(is_valid=True)
    except TemplateSyntaxError as exc:
      return ValidationResult(
        is_valid=False,
        error_message=str(exc),
        error_line=getattr(exc, 'lineno', None),
        error_column=getattr(exc, 'colno', None)
      )
    except TemplateNotFound as exc:
      return ValidationResult(
        is_valid=False,
        error_message=f"Template not found: {exc}"
      )
    except Exception as exc:
      return ValidationResult(
        is_valid=False,
        error_message=f"Unexpected error: {exc}"
      )

  def validate_template_file(self, file_path: str) -> ValidationResult:
    """Validate template file syntax without rendering"""
    abs_path = os.path.abspath(file_path)

    # Check if file exists
    if not os.path.isfile(abs_path):
      return ValidationResult(
        template_path=abs_path,
        is_valid=False,
        error_message=f"Template file does not exist: {abs_path}"
      )

    try:
      # Read template file
      with open(abs_path, 'r', encoding='utf-8') as file:
        template_content = file.read()

      # Validate the template content
      result = self.validate_template_string(template_content)
      result.template_path = abs_path
      return result

    except UnicodeDecodeError as exc:
      return ValidationResult(
        template_path=abs_path,
        is_valid=False,
        error_message=f"Cannot read template file (encoding error): {exc}"
      )
    except OSError as exc:
      return ValidationResult(
        template_path=abs_path,
        is_valid=False,
        error_message=f"Cannot read template file: {exc}"
      )

  def validate_directory(self, directory_path: str, recursive: bool = True) -> DirectoryValidationResult:
    """Validate all template files in a directory"""
    abs_dir = os.path.abspath(directory_path)
    result = DirectoryValidationResult(directory_path=abs_dir)

    if not os.path.isdir(abs_dir):
      # Add a single validation result indicating directory doesn't exist
      invalid_result = ValidationResult(
        template_path=abs_dir,
        is_valid=False,
        error_message=f"Directory does not exist: {abs_dir}"
      )
      result.add_template_result(invalid_result)
      return result

    try:
      # Find all .j2 template files
      if recursive:
        for root, dirs, files in os.walk(abs_dir):
          for file in files:
            if file.endswith('.j2'):
              file_path = os.path.join(root, file)
              template_result = self.validate_template_file(file_path)
              result.add_template_result(template_result)
      else:
        # Only check files in the immediate directory
        for file in os.listdir(abs_dir):
          file_path = os.path.join(abs_dir, file)
          if os.path.isfile(file_path) and file.endswith('.j2'):
            template_result = self.validate_template_file(file_path)
            result.add_template_result(template_result)

    except OSError as exc:
      # Add a single validation result indicating directory access error
      invalid_result = ValidationResult(
        template_path=abs_dir,
        is_valid=False,
        error_message=f"Cannot access directory: {exc}"
      )
      result.add_template_result(invalid_result)

    return result



  # ┌────────────────────────┐
  # │ Core Rendering Methods │
  # └────────────────────────┘

  def render_file(self,
                  source_path: str,
                  output_path: Optional[str]            = None,
                  output_dir:  Optional[str]            = None,
                  variables:   Optional[Dict[str, Any]] = None,
                  ) -> FileRenderResult:
    """Render single file with optional per-render parameters"""

    # Determine output path with hierarchy:
    # 1. Method parameter output_path (highest priority)
    # 2. Method parameter output_dir
    # 3. Class-level output_directory
    # 4. Source file directory (default)
    if output_path is None:
      if output_dir is None:
        if self.output_directory is not None:
          output_dir = self.output_directory
        else:
          output_dir = os.path.dirname(os.path.abspath(source_path))

      # Generate output filename
      filename = os.path.basename(source_path)
      if filename.endswith('.j2'):
        filename = filename[:-3]  # Strip .j2 extension
      elif self.options.get('render_non_template'):
        # Add suffix for non-templates
        suffix = self.options['render_non_template']
        if '.' in filename:
          filename = filename.replace('.', suffix + '.', 1)
        else:
          filename += suffix

      output_path = os.path.join(output_dir, filename)

    # Ensure output path is absolute
    output_path = os.path.abspath(output_path)

    # Merge variables
    merged_vars = self._get_merged_variables(variables)

    # Ensure Jinja2 environment is set up
    jinja_env = self._ensure_environment()

    # Process the file
    return process_single_file(
      source_path, output_path, jinja_env, merged_vars, self.options
    )

  def render_directory(self,
                       source_dir: str,
                       output_dir: Optional[str] = None,
                       variables:  Optional[Dict[str, Any]] = None,
                       ) -> RenderResult:
    """Render entire directory with optional per-render parameters"""

    # Determine output directory with hierarchy:
    # 1. Method parameter output_dir (highest priority)
    # 2. Class-level output_directory
    # 3. Source directory (default)
    if output_dir is None:
      if self.output_directory is not None:
        output_dir = self.output_directory
      else:
        output_dir = source_dir

    # Merge variables
    merged_vars = self._get_merged_variables(variables)

    # Ensure Jinja2 environment is set up
    jinja_env = self._ensure_environment()

    # Process the directory
    return process_directory(
      source_dir, output_dir, jinja_env, merged_vars, self.options
    )

  def render_string(self,
                   template_string: str,
                   variables: Optional[Dict[str, Any]] = None,
                   ) -> str:
    """Render template string directly"""

    # Merge variables
    merged_vars = self._get_merged_variables(variables)

    # Render using core function
    return render_template_string(
      template_string, merged_vars, self.include_dirs, self.filters, self.tests, self.options
    )



  # ┌──────────────────┐
  # │ Internal Methods │
  # └──────────────────┘

  def _ensure_environment(self):
    """Lazy initialization of Jinja2 environment"""
    if self._jinja_env is None or self._env_dirty:
      self._jinja_env = setup_jinja_environment(
        include_dirs = self.include_dirs,
        filters      = self.filters,
        tests        = self.tests,
        options      = self.options
      )
      self._env_dirty = False
    return self._jinja_env

  def _get_merged_variables(self, additional_vars: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get merged variables including context variables"""
    # Start with global variables
    merged_vars = self.variables.copy()

    # Add context variables
    context_vars = {}
    try:                     context_vars['__python_version__'] = python_version()
    except Exception as exc: throw_warning(f"Could not set the context global variable '__python_version__'.")
    try:                     context_vars['__jinja2_version__'] = jinja2_version
    except Exception as exc: throw_warning(f"Could not set the context global variable '__jinja2_version__'.")
    try:                     context_vars['__j2gpp_version__'] = get_j2gpp_version()
    except Exception as exc: throw_warning(f"Could not set the context global variable '__j2gpp_version__'.")
    try:                     context_vars['__user__'] = os.getlogin()
    except Exception as exc: throw_warning(f"Could not set the context global variable '__user__'.")
    try:                     context_vars['__pid__'] = os.getpid()
    except Exception as exc: throw_warning(f"Could not set the context global variable '__pid__'.")
    try:                     context_vars['__ppid__'] = os.getppid()
    except Exception as exc: throw_warning(f"Could not set the context global variable '__ppid__'.")
    try:                     context_vars['__working_directory__'] = os.getcwd()
    except Exception as exc: throw_warning(f"Could not set the context global variable '__working_directory__'.")
    try:                     context_vars['__output_directory__'] = self.options.get('out_dir', os.getcwd())
    except Exception as exc: throw_warning(f"Could not set the context global variable '__output_directory__'.")
    try:                     context_vars['__date__'] = datetime.now().strftime("%d-%m-%Y")
    except Exception as exc: throw_warning(f"Could not set the context global variable '__date__'.")
    try:                     context_vars['__date_inv__'] = datetime.now().strftime("%Y-%m-%d")
    except Exception as exc: throw_warning(f"Could not set the context global variable '__date_inv__'.")
    try:                     context_vars['__time__'] = datetime.now().strftime("%H:%M:%S")
    except Exception as exc: throw_warning(f"Could not set the context global variable '__time__'.")
    try:                     context_vars['__datetime__'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception as exc: throw_warning(f"Could not set the context global variable '__datetime__'.")
    merged_vars = self._merge_variables(merged_vars, context_vars)

    # Add per-render variables if provided
    if additional_vars:
      merged_vars = self._merge_variables(merged_vars, additional_vars)

    # Apply global vars adapter if set
    if self.global_vars_adapter_function:
      self.global_vars_adapter_function(merged_vars)

    return merged_vars

  def _merge_variables(self, var_dict1: Dict[str, Any], var_dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two variable dictionaries with conflict resolution"""
    return var_dict_update(var_dict1, var_dict2)

  def _post_process_variables(self, var_dict: Dict[str, Any], context_file: Optional[str] = None) -> Dict[str, Any]:
    """Post-process variables after loading from file"""
    # Apply file vars adapter if set
    if self.file_vars_adapter_function:
      self.file_vars_adapter_function(var_dict)

    # Check that variable names are valid Python identifiers
    if not self.options['no_check_identifier']:
      rec_check_valid_identifier(var_dict, context_file)

    return var_dict



# Utility function for quick template string rendering
def render_template(template_string: str,
                    variables: Optional[Dict[str, Any]] = None,
                    **options,
                    ) -> str:
  """Quick utility function to render a template string"""
  engine = J2GPP()

  # Set any options passed as keyword arguments
  for option_name, value in options.items():
    engine.set_option(option_name, value)

  return engine.render_string(template_string, variables)
