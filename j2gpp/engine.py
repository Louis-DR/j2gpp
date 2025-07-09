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
from typing import Dict, Any, List, Optional

from jinja2 import __version__ as jinja2_version

from j2gpp.core import (
  setup_jinja_environment,
  process_single_file,
  process_directory,
  render_template_string
)
from j2gpp.results import RenderResult, FileRenderResult
from j2gpp.loaders import (
  load_variables_from_file,
  load_variables_from_env_vars
)
from j2gpp.utils import (
  get_j2gpp_version,
  auto_cast_str,
  throw_warning,
  rec_check_valid_identifier,
  var_dict_update
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

    # Jinja2 configuration
    self.include_dirs = []
    self.filter_paths = []
    self.test_paths   = []

    # Adapter functions
    self.file_vars_adapter_function   = None
    self.global_vars_adapter_function = None

    # Cached Jinja2 environment
    self._jinja_env = None
    self._env_dirty = True


  # ┌──────────────────────┐
  # │ Variable Management  │
  # └──────────────────────┘

  def add_variables(self, variables: Dict[str, Any]) -> 'J2GPP':
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


  # ┌───────────────┐
  # │ Configuration │
  # └───────────────┘

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

  def load_filters_from_file(self, file_path: str) -> 'J2GPP':
    """Load custom Jinja2 filters (chainable)"""
    abs_path = os.path.abspath(file_path)
    if abs_path not in self.filter_paths:
      self.filter_paths.append(abs_path)
      self._env_dirty = True
    return self

  def load_tests_from_file(self, file_path: str) -> 'J2GPP':
    """Load custom Jinja2 tests (chainable)"""
    abs_path = os.path.abspath(file_path)
    if abs_path not in self.test_paths:
      self.test_paths.append(abs_path)
      self._env_dirty = True
    return self

  def set_file_vars_adapter(self, function_callable) -> 'J2GPP':
    """Set function to process variables after loading from files (chainable)"""
    if callable(function_callable):
      self.file_vars_adapter_function = function_callable
    else:
      throw_warning("File vars adapter must be callable.")
    return self

  def set_global_vars_adapter(self, function_callable) -> 'J2GPP':
    """Set function to process all variables before rendering (chainable)"""
    if callable(function_callable):
      self.global_vars_adapter_function = function_callable
    else:
      throw_warning("Global vars adapter must be callable.")
    return self


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

    # Determine output path
    if output_path is None:
      if output_dir is None:
        output_dir = os.getcwd()

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
                       output_dir: str,
                       variables:  Optional[Dict[str, Any]] = None,
                       ) -> RenderResult:
    """Render entire directory with optional per-render parameters"""

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
      template_string, merged_vars, self.include_dirs, self.options
    )


  # ┌──────────────────┐
  # │ Internal Methods │
  # └──────────────────┘

  def _ensure_environment(self):
    """Lazy initialization of Jinja2 environment"""
    if self._jinja_env is None or self._env_dirty:
      self._jinja_env = setup_jinja_environment(
        include_dirs = self.include_dirs,
        filter_paths = self.filter_paths,
        test_paths   = self.test_paths,
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
