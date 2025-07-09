# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     j2gpp - Jinja2-based General Purpose Preprocessor            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        loaders.py                                                   ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Variable loading functions for different file formats.       ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



import errno
from typing import Dict, Any, Optional

from j2gpp.utils import (
  throw_error,
  intend_text,
  auto_cast_str,
  throw_warning
)



def load_yaml_variables(var_path: str) -> Dict[str,Any]:
  """Load variables from YAML file"""
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
  return var_dict or {}


def load_json_variables(var_path: str) -> Dict[str,Any]:
  """Load variables from JSON file"""
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
  return var_dict or {}


def load_hjson_variables(var_path: str) -> Dict[str,Any]:
  """Load variables from HJSON file"""
  var_dict = {}
  try:
    import hjson
    with open(var_path) as var_file:
      try:
        var_dict = dict(hjson.loads(var_file.read()))
      except Exception as exc:
        throw_error(f"Exception occurred while loading '{var_path}' : \n  {type(exc).__name__}\n{intend_text(exc)}")
  except ImportError:
    throw_error("Could not import Python library 'hjson' to parse HJSON variables files.")
  return var_dict or {}


def load_xml_variables(var_path: str,
                       options:  Dict[str,Any] = None,
                       ) -> Dict[str,Any]:
  """Load variables from XML file"""
  if options is None:
    options = {'xml_convert_attributes': False, 'xml_remove_namespaces': False}

  var_dict = {}
  try:
    import xmltodict
    # Postprocessor to auto cast the values
    def xml_postprocessor(path, key, value):
      # Convert attribute to child
      if options['xml_convert_attributes']:
        key = key.lstrip("@")
      # Remove namespace
      if options['xml_remove_namespaces']:
        key = key.split(":")[-1]
      # Prepare bool for auto-cast
      if value == "true":  value = "True"
      if value == "false": value = "False"
      # Auto-cast value
      value = auto_cast_str(value)
      return key, value

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
  return var_dict or {}


def load_toml_variables(var_path: str) -> Dict[str,Any]:
  """Load variables from TOML file"""
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
  return var_dict or {}


def load_ini_variables(var_path: str) -> Dict[str,Any]:
  """Load variables from INI/CFG file"""
  var_dict = {}
  try:
    import configparser
    with open(var_path) as var_file:
      try:
        config = configparser.ConfigParser()
        config.read_file(var_file)
        for section in config.sections():
          if section == '_':
            for var, val in config.items(section):
              var_dict[var] = auto_cast_str(val)
          else:
            var_dict[section] = dict(config.items(section))
      except Exception as exc:
        throw_error(f"Exception occurred while loading '{var_path}' : \n  {type(exc).__name__}\n{intend_text(exc)}")
  except ImportError:
    throw_error("Could not import Python library 'configparser' to parse INI/CFG variables files.")
  return var_dict or {}


def load_env_variables(var_path: str) -> Dict[str,Any]:
  """Load variables from ENV file"""
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
        # Handle conflicts inside the file
        if var in var_dict:
          throw_warning(f"Variable '{var}' redefined from '{var_dict[var]}' to '{val}' in file '{var_path}'.")
        var_dict[var] = val
  return var_dict


def load_csv_variables(var_path:    str,
                       delimiter:   str           = ',',
                       escape_char: Optional[str] = None,
                       dont_strip:  bool          = False,
                       ) -> Dict[str,Any]:
  """Load variables from CSV file"""
  var_dict = {}
  try:
    import csv
    with open(var_path) as var_file:
      try:
        csv_reader = csv.DictReader(var_file, delimiter=delimiter, escapechar=escape_char)
        # First columns for keys
        main_key = csv_reader.fieldnames[0]
        for row in csv_reader:
          var = row.pop(main_key)
          # Strip whitespace around key and value
          if not dont_strip:
            row = {key.strip(): val.strip() for key, val in row.items()}
          # Auto cast values
          row = {key: auto_cast_str(val) for key, val in row.items()}
          # Handle conflicts inside the file
          if var in var_dict:
            throw_warning(f"Row '{var}' redefined from '{var_dict[var]}' to '{row}' in file '{var_path}'.")
          var_dict[var] = row
      except Exception as exc:
        throw_error(f"Exception occurred while loading '{var_path}' : \n  {type(exc).__name__}\n{intend_text(exc)}")
  except ImportError:
    throw_error("Could not import Python library 'csv' to parse CSV/TSV variables files.")
  return var_dict


def load_tsv_variables(var_path:    str,
                       escape_char: Optional[str] = None,
                       dont_strip:  bool          = False,
                       ) -> Dict[str,Any]:
  """Load variables from TSV file"""
  return load_csv_variables(var_path, delimiter='\t', escape_char=escape_char, dont_strip=dont_strip)


# Registry of loaders by file extension
LOADERS = {
  'yaml':  load_yaml_variables,
  'yml':   load_yaml_variables,
  'json':  load_json_variables,
  'hjson': load_hjson_variables,
  'xml':   load_xml_variables,
  'toml':  load_toml_variables,
  'ini':   load_ini_variables,
  'cfg':   load_ini_variables,
  'env':   load_env_variables,
  'csv':   load_csv_variables,
  'tsv':   load_tsv_variables,
}


def load_variables_from_file(file_path: str,
                             options:   Dict[str,Any] = None,
                             ) -> Dict[str,Any]:
  """Load variables from any supported file format"""
  if options is None:
    options = {}

  var_format = file_path.split('.')[-1].lower()

  if var_format not in LOADERS:
    throw_error(f"Cannot read '{file_path}' : unsupported format '{var_format}'.")
    return {}

  try:
    loader = LOADERS[var_format]

    # Handle loaders that need extra options
    if var_format == 'xml':
      return loader(file_path, options)
    elif var_format in ('csv', 'tsv'):
      return loader(
        file_path,
        delimiter=options.get('csv_delimiter', ',' if var_format == 'csv' else '\t'),
        escape_char=options.get('csv_escape_char'),
        dont_strip=options.get('csv_dont_strip', False)
      )
    else:
      return loader(file_path)

  except OSError as exc:
    if exc.errno == errno.ENOENT:
      throw_error(f"Cannot read '{file_path}' : file doesn't exist.")
    elif exc.errno == errno.EACCES:
      throw_error(f"Cannot read '{file_path}' : missing read permission.")
    else:
      throw_error(f"Cannot read '{file_path}'.")
    return {}


def load_variables_from_env_vars(env_vars: Dict[str,str],
                                 prefix:   Optional[str] = None,
                                 ) -> Dict[str,Any]:
  """Load variables from environment variables"""
  var_dict = {}
  for var, val in env_vars.items():
    # Filter by prefix if provided
    if prefix and not var.startswith(prefix):
      continue
    # Remove prefix if provided
    if prefix:
      var = var[len(prefix):]
    # Evaluate value to correct type
    var_dict[var] = auto_cast_str(val)
  return var_dict
