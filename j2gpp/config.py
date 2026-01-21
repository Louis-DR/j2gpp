# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     j2gpp - Jinja2-based General Purpose Preprocessor            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        config.py                                                    ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: User configuration file discovery and loading.               ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



import json
import os
from typing import (
  Dict,
  Any,
  Optional,
  List,
)

from j2gpp.utils import throw_warning



# ┌──────────────────────────────┐
# │ Configuration File Locations │
# └──────────────────────────────┘

# Configuration file search order
CONFIG_FILE_LOCATIONS = [
  os.path.join("~", ".config", "j2gpp", "j2gpp.json"),  # XDG standard
  os.path.join("~",                    ".j2gpp.json"),  # Simple dotfile
]



# ┌───────────────────────┐
# │ Default Configuration │
# └───────────────────────┘

def get_default_config() -> Dict[str,Any]:
  """Return the default configuration with all supported options"""
  return {
    "options": {
      "no_strict_undefined":    False,
      "debug_vars":             False,
      "no_check_identifier":    False,
      "fix_identifiers":        False,
      "chdir_src":              False,
      "no_chdir":               False,
      "trim_whitespace":        False,
      "csv_delimiter":          ",",
      "csv_escape_char":        None,
      "csv_dont_strip":         False,
      "xml_convert_attributes": False,
      "xml_remove_namespaces":  False,
      "render_non_template":    None,
      "copy_non_template":      False,
      "warn_overwrite":         False,
      "no_overwrite":           False,
      "overwrite_outdir":       False,
    },
    "include_dirs":       [],
    "no_auto_extensions": False,
    "disable_extensions": [],
    "extensions":         {},
  }



# ┌──────────────────────────────┐
# │ Configuration File Discovery │
# └──────────────────────────────┘

def find_config_file() -> Optional[str]:
  """Find the user configuration file"""
  for location in CONFIG_FILE_LOCATIONS:
    expanded_path = os.path.expanduser(location)
    if os.path.isfile(expanded_path):
      return expanded_path
  return None



# ┌────────────────────────────┐
# │ Configuration File Loading │
# └────────────────────────────┘

def load_config_file(path:Optional[str]=None) -> Dict[str,Any]:
  """Load configuration from a JSON file"""
  # Find config file if not explicitly provided
  if path is None:
    path = find_config_file()

  # No configuration file found
  if path is None:
    return {}

  # Expand path and check existence
  expanded_path = os.path.expanduser(path)
  if not os.path.isfile(expanded_path):
    throw_warning(f"Configuration file not found: '{expanded_path}'")
    return {}

  # Read configuration file
  try:
    with open(expanded_path, 'r', encoding='utf-8') as file:
      config = json.load(file)

    if not isinstance(config, dict):
      throw_warning(f"Configuration file must contain a JSON object: '{expanded_path}'")
      return {}

    return config

  except json.JSONDecodeError as exc:
    throw_warning(f"Invalid JSON in configuration file '{expanded_path}': {exc}")
    return {}
  except OSError as exc:
    throw_warning(f"Cannot read configuration file '{expanded_path}': {exc}")
    return {}



# ┌───────────────────────┐
# │ Configuration Merging │
# └───────────────────────┘

def _deep_merge(base:Dict[str,Any], override:Dict[str,Any]) -> Dict[str,Any]:
  """Deep merge two dictionaries. Override values take precedence"""
  result = base.copy()
  for key, value in override.items():
    if key in result and isinstance(result[key], dict) and isinstance(value, dict):
      result[key] = _deep_merge(result[key], value)
    else:
      result[key] = value
  return result


def merge_configs(defaults:      Dict[str,Any],
                  user_config:   Dict[str,Any],
                  cli_overrides: Dict[str,Any] = None
                  ) -> Dict[str,Any]:
  """Merge configuration from multiple sources"""
  # Start with defaults
  result = defaults.copy()

  # Merge user config (overrides defaults)
  result = _deep_merge(result, user_config)

  # Merge CLI overrides (highest priority)
  if cli_overrides:
    result = _deep_merge(result, cli_overrides)

  return result



# ┌────────────────────────────────────┐
# │ CLI Arguments to Config Conversion │
# └────────────────────────────────────┘

def cli_args_to_config(args) -> Dict[str,Any]:
  """Convert CLI arguments to configuration dictionary format"""
  config = {"options": {}}

  # Map CLI arguments to config options
  # Only include if the CLI argument was explicitly provided (not default)
  cli_option_mapping = {
    'no_strict_undefined':    'no_strict_undefined',
    'debug_vars':             'debug_vars',
    'no_check_identifier':    'no_check_identifier',
    'fix_identifiers':        'fix_identifiers',
    'chdir_src':              'chdir_src',
    'no_chdir':               'no_chdir',
    'trim_whitespace':        'trim_whitespace',
    'csv_delimiter':          'csv_delimiter',
    'csv_escape_char':        'csv_escape_char',
    'csv_dont_strip':         'csv_dont_strip',
    'xml_convert_attributes': 'xml_convert_attributes',
    'xml_remove_namespaces':  'xml_remove_namespaces',
    'render_non_template':    'render_non_template',
    'copy_non_template':      'copy_non_template',
    'warn_overwrite':         'warn_overwrite',
    'no_overwrite':           'no_overwrite',
    'overwrite_outdir':       'overwrite_outdir',
  }

  for cli_argument, config_key in cli_option_mapping.items():
    value = getattr(args, cli_argument, None)
    if value is not None:
      # For boolean flags that default to False, only include if True
      # For string options, only include if not None
      if isinstance(value, bool):
        if value:  # Only include True values for boolean flags
          config["options"][config_key] = value
      else:
        config["options"][config_key] = value

  # Handle include directories
  if hasattr(args, 'incdir') and args.incdir:
    config["include_dirs"] = args.incdir

  # Handle extension settings
  if hasattr(args, 'no_auto_extensions') and args.no_auto_extensions:
    config["no_auto_extensions"] = True

  if hasattr(args, 'disable_extensions') and args.disable_extensions:
    config["disable_extensions"] = args.disable_extensions

  return config



# ┌────────────────────────────────┐
# │ Extension Configuration Access │
# └────────────────────────────────┘

def get_extension_config(config:Dict[str,Any], extension_name:str) -> Dict[str,Any]:
  """Get configuration for a specific extension"""
  extensions_config = config.get("extensions", {})
  return extensions_config.get(extension_name, {})
