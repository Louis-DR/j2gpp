# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     j2gpp - Jinja2-based General Purpose Preprocessor            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        results.py                                                   ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Result classes for J2GPP operations.                         ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from dataclasses import dataclass, field
from typing import List, Optional



@dataclass
class FileRenderResult:
  """Result of rendering a single file"""
  source_path:   str
  output_path:   str
  success:       bool
  error_message: Optional[str] = None
  is_template:   bool          = True
  was_copied:    bool          = False


@dataclass
class RenderResult:
  """Result of a rendering operation (single file or directory)"""
  files:    List[FileRenderResult] = field(default_factory=list)
  warnings: List[str]              = field(default_factory=list)
  errors:   List[str]              = field(default_factory=list)

  @property
  def total_files(self) -> int:
    """Total number of files processed"""
    return len(self.files)

  @property
  def successful_files(self) -> int:
    """Number of successfully processed files"""
    return sum(1 for f in self.files if f.success)

  @property
  def failed_files(self) -> int:
    """Number of files that failed to process"""
    return sum(1 for f in self.files if not f.success)

  @property
  def success(self) -> bool:
    """True if no errors occurred"""
    return len(self.errors) == 0

  def add_file_result(self, result: FileRenderResult):
    """Add a file result to this render result"""
    self.files.append(result)

  def add_warning(self, warning: str):
    """Add a warning message"""
    self.warnings.append(warning)

  def add_error(self, error: str):
    """Add an error message"""
    self.errors.append(error)

  def merge(self, other: 'RenderResult'):
    """Merge another RenderResult into this one"""
    self.files.extend(other.files)
    self.warnings.extend(other.warnings)
    self.errors.extend(other.errors)
