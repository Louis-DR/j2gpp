# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     j2gpp - Jinja2-based General Purpose Preprocessor            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        extensions.py                                                ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Extension discovery and loading system.                      ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from typing import (
  Dict,
  Any,
  List,
  Set,
  Optional,
)

from j2gpp.utils import throw_warning



# ┌─────────────────────┐
# │ Extension Interface │
# └─────────────────────┘

# Extensions are dictionaries with the following structure:
#   {
#     "name": "extension_name",        # Required: unique identifier
#     "version": "1.0.0",              # Optional: version string
#     "dependencies": ["other_ext"],   # Optional: dependency names
#     "filters": {"name": callable},   # Optional: Jinja2 filters
#     "tests": {"name": callable},     # Optional: Jinja2 tests
#     "globals": {"name": value},      # Optional: Jinja2 globals
#     "on_configure": callable,        # Optional: (config: Dict) -> None
#   }
#
# The on_configure callback receives extension-specific configuration from
# the user's configuration file (~/.config/j2gpp/j2gpp.json):
#   {
#     "extensions": {
#       "extension_name": {
#         "option1": "value1",
#         "option2": true
#       }
#     }
#   }

# Extensions register via entry points in pyproject.toml:
#   [project.entry-points."j2gpp.extensions"]
#   my_extension = "my_package:j2gpp_extension"

EXTENSION_ENTRY_POINT_GROUP = "j2gpp.extensions"



def discover_extensions() -> Dict[str,Dict[str,Any]]:
  """Discover all installed J2GPP extensions via entry points"""
  extensions = {}

  try:
    # Python 3.10+ has a different API
    from importlib.metadata import entry_points as importlib_entry_points
    entry_points = importlib_entry_points(group=EXTENSION_ENTRY_POINT_GROUP)
  except TypeError:
    # Python 3.9 and earlier
    from importlib.metadata import entry_points as importlib_entry_points
    all_entry_points = importlib_entry_points()
    entry_points = all_entry_points.get(EXTENSION_ENTRY_POINT_GROUP, [])

  for entry_point in entry_points:
    try:
      extension = _load_entry_point(entry_point)
      if extension:
        name = extension.get("name", entry_point.name)
        extensions[name] = extension
    except Exception as exception:
      throw_warning(f"Failed to load extension '{entry_point.name}': {exception}.")

  return extensions


def _load_entry_point(entry_point) -> Optional[Dict[str,Any]]:
  """Load an extension from an entry point"""
  try:
    extension = entry_point.load()

    # Handle callable (factory function)
    if callable(extension) and not isinstance(extension, dict):
      extension = extension()

    # Validate extension format
    if not isinstance(extension, dict):
      throw_warning(f"Extension '{entry_point.name}' must be a dict, got type '{type(extension).__name__}'.")
      return None

    # Ensure name is set
    if "name" not in extension:
      extension["name"] = entry_point.name

    return extension

  except Exception as exception:
    throw_warning(f"Error loading extension '{entry_point.name}': {exception}")
    return None


def load_extension_by_name(name:str) -> Optional[Dict[str,Any]]:
  """Load a specific extension by its entry point name"""
  try:
    from importlib.metadata import entry_points as importlib_entry_points
    try:
      # Python 3.10+
      entry_points = importlib_entry_points(group=EXTENSION_ENTRY_POINT_GROUP)
    except TypeError:
      # Python 3.9 and earlier
      all_entry_points = importlib_entry_points()
      entry_points = all_entry_points.get(EXTENSION_ENTRY_POINT_GROUP, [])

    for entry_point in entry_points:
      if entry_point.name == name:
        return _load_entry_point(entry_point)

    throw_warning(f"Extension '{name}' not found in installed packages.")
    return None

  except Exception as exception:
    throw_warning(f"Failed to load extension '{name}': {exception}")
    return None


def resolve_dependencies(extensions:Dict[str,Dict[str,Any]]) -> List[str]:
  """Resolve extension dependencies and return load order"""
  # Build dependency graph
  graph: Dict[str,Set[str]] = {}
  for name, extension in extensions.items():
    dependencies = extension.get("dependencies", [])
    graph[name] = set(dependencies) if dependencies else set()

  # Check for missing dependencies
  all_names = set(extensions.keys())
  for name, dependencies in graph.items():
    missing = dependencies - all_names
    if missing:
      throw_warning(
        f"Extension '{name}' depends on missing extension(s): {', '.join(missing)}"
      )
      # Remove missing dependencies to allow loading
      graph[name] = dependencies - missing

  # Topological sort (Kahn's algorithm)
  in_degree: Dict[str,int] = {name: 0 for name in graph}
  for name, dependencies in graph.items():
    for dependency in dependencies:
      if dependency in in_degree:
        in_degree[name] += 1

  queue = [name for name, degree in in_degree.items() if degree == 0]
  result = []

  while queue:
    # Sort for deterministic order
    queue.sort()
    node = queue.pop(0)
    result.append(node)

    for name, dependencies in graph.items():
      if node in dependencies:
        in_degree[name] -= 1
        if in_degree[name] == 0 and name not in result:
          queue.append(name)

  # Check for circular dependencies
  if len(result) != len(graph):
    remaining = set(graph.keys()) - set(result)
    throw_warning(f"Circular dependencies detected among: {', '.join(remaining)}")
    # Add remaining in alphabetical order anyway
    result.extend(sorted(remaining))

  return result


def get_extension_info(extension: Dict[str, Any]) -> Dict[str, Any]:
  """Extract metadata info from an extension"""
  return {
    "name":             extension.get("name",    "unknown"),
    "version":          extension.get("version", "unknown"),
    "dependencies":     extension.get("dependencies",   []),
    "filter_count": len(extension.get("filters", {})),
    "test_count":   len(extension.get("tests",   {})),
    "global_count": len(extension.get("globals", {})),
  }
