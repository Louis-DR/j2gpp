# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     j2gpp - Jinja2-based General Purpose Preprocessor            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        globals.py                                                   ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Additional useful global variables and functions.            ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



import os
from datetime import datetime
from platform import python_version
from itertools import cycle
from math import (
  pow,
  log,
  sqrt,
  cbrt,
  nan,
  inf,
  pi,
  tau,
  e,
)

from jinja2 import __version__ as jinja2_version

from j2gpp.utils import (
  get_j2gpp_version,
  throw_warning,
)



extra_globals = {}



# ┌───────────────────┐
# │ Context variables │
# └───────────────────┘

# Global context variables
try:                     extra_globals['__python_version__'] = python_version()
except Exception as exc: throw_warning(f"Could not set the context global variable '__python_version__'.")
try:                     extra_globals['__jinja2_version__'] = jinja2_version
except Exception as exc: throw_warning(f"Could not set the context global variable '__jinja2_version__'.")
try:                     extra_globals['__j2gpp_version__'] = get_j2gpp_version()
except Exception as exc: throw_warning(f"Could not set the context global variable '__j2gpp_version__'.")
try:                     extra_globals['__user__'] = os.getlogin()
except Exception as exc: throw_warning(f"Could not set the context global variable '__user__'.")
try:                     extra_globals['__pid__'] = os.getpid()
except Exception as exc: throw_warning(f"Could not set the context global variable '__pid__'.")
try:                     extra_globals['__ppid__'] = os.getppid()
except Exception as exc: throw_warning(f"Could not set the context global variable '__ppid__'.")
try:                     extra_globals['__working_directory__'] = os.getcwd()
except Exception as exc: throw_warning(f"Could not set the context global variable '__working_directory__'.")
try:                     extra_globals['__date__'] = datetime.now().strftime("%d-%m-%Y")
except Exception as exc: throw_warning(f"Could not set the context global variable '__date__'.")
try:                     extra_globals['__date_inv__'] = datetime.now().strftime("%Y-%m-%d")
except Exception as exc: throw_warning(f"Could not set the context global variable '__date_inv__'.")
try:                     extra_globals['__time__'] = datetime.now().strftime("%H:%M:%S")
except Exception as exc: throw_warning(f"Could not set the context global variable '__time__'.")
try:                     extra_globals['__datetime__'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
except Exception as exc: throw_warning(f"Could not set the context global variable '__datetime__'.")



# ┌────────────────────────┐
# │ Mathematical constants │
# └────────────────────────┘

extra_globals['nan']   = nan
extra_globals['inf']   = inf
extra_globals['pi']    = pi
extra_globals['tau']   = tau
extra_globals['e']     = e
extra_globals['phi']   = (1+sqrt(5))/2
extra_globals['sqrt2'] = sqrt(2)
extra_globals['sqrt3'] = sqrt(3)
extra_globals['cbrt2'] = cbrt(2)
extra_globals['cbrt3'] = cbrt(3)
extra_globals['ln2']   = log(2)



# ┌──────────────────┐
# │ Python libraries │
# └──────────────────┘

import math as math
extra_globals['math'] = math

import statistics as statistics
extra_globals['statistics'] = statistics

import itertools as itertools
extra_globals['itertools'] = itertools

import random as random
extra_globals['random'] = random

import secrets as secrets
extra_globals['secrets'] = secrets

import os.path as ospath
extra_globals['ospath'] = ospath

import datetime as datetime
extra_globals['datetime'] = datetime

import calendar as calendar
extra_globals['calendar'] = calendar

import pprint as pprint
extra_globals['pprint'] = pprint

import colorsys as colorsys
extra_globals['colorsys'] = colorsys

try:
  import colour as colour
  extra_globals['colour'] = colour
except ImportError:
  throw_warning(f"Could not load the global library 'colour'.")
  pass



# ┌──────────────┐
# │ Accumulators │
# └──────────────┘

class Accumulator:
  def __init__(self, initial=0):
    self.initial = initial
    self.value   = initial
  # Return the value after the operation
  def reset(self):
    self.value = self.initial
    return self.value
  def clear(self):
    self.value = 0
    return self.value
  def set(self, value):
    self.value = value
    return self.value
  def get(self):
    return self.value
  def increment(self):
    self.value += 1
    return self.value
  def decrement(self):
    self.value -= 1
    return self.value
  def add(self, value):
    self.value += value
    return self.value
  def subtract(self, value):
    self.value -= value
    return self.value
  def multiply(self, value):
    self.value *= value
    return self.value
  def divide(self, value):
    self.value /= value
    return self.value
  def modulo(self, value):
    self.value %= value
    return self.value
  def floor_divide(self, value):
    self.value //= value
    return self.value
  def square(self):
    self.value = pow(self.value,2)
    return self.value
  def cube(self):
    self.value = pow(self.value,3)
    return self.value
  def square_root(self):
    self.value = sqrt(self.value)
    return self.value
  def cube_root(self):
    self.value = cbrt(self.value)
    return self.value
  def exponentiate(self, value=2):
    self.value = pow(self.value, value)
    return self.value
  def logarithm(self, value=2):
    self.value = log(self.value, value)
    return self.value
  # Return the value before the operation
  def reset_after(self):
    before = self.value
    self.value = self.initial
    return before
  def clear_after(self):
    before = self.value
    self.value = 0
    return before
  def set_after(self, value):
    before = self.value
    self.value = value
    return before
  def increment_after(self):
    before = self.value
    self.value += 1
    return before
  def decrement_after(self):
    before = self.value
    self.value -= 1
    return before
  def add_after(self, value):
    before = self.value
    self.value += value
    return before
  def subtract_after(self, value):
    before = self.value
    self.value -= value
    return before
  def multiply_after(self, value):
    before = self.value
    self.value *= value
    return before
  def divide_after(self, value):
    before = self.value
    self.value /= value
    return before
  def modulo_after(self, value):
    before = self.value
    self.value %= value
    return before
  def floor_divide_after(self, value):
    before = self.value
    self.value //= value
    return before
  def square_after(self):
    before = self.value
    self.value = pow(self.value,2)
    return before
  def cube_after(self):
    before = self.value
    self.value = pow(self.value,3)
    return before
  def square_root_after(self):
    before = self.value
    self.value = sqrt(self.value)
    return before
  def cube_root_after(self):
    before = self.value
    self.value = cbrt(self.value)
    return before
  def exponentiate_after(self, value=2):
    before = self.value
    self.value = pow(self.value, value)
    return before
  def logarithm_after(self, value=2):
    before = self.value
    self.value = log(self.value, value)
    return before
extra_globals['Accumulator'] = Accumulator



# ┌────────┐
# │ Cycler │
# └────────┘

class Cycler:
  def __init__(self, *items):
    if not items:
      raise ValueError("Cycler requires at least one item.")
    self.items = items
    self.iterator = cycle(self.items)
  def next(self):
    return next(self.iterator)
  def reset(self):
    self.iterator = cycle(self.items)
extra_globals['Cycler'] = Cycler
