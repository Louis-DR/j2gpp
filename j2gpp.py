import argparse
import glob
import os
from jinja2 import Environment, BaseLoader

# Command line arguments
argparser = argparse.ArgumentParser()
argparser.add_argument("source", help="Path to library file", nargs='+')
args = argparser.parse_args()

# Collecting source templates paths
sources = []
for raw_path in args.source:
  # Glob to apply UNIX-style path patterns
  for glob_path in glob.glob(raw_path):
    abs_path = os.path.abspath(glob_path)
    # Only keep files ending with .j2 extension
    if os.path.isfile(abs_path) and abs_path.endswith('.j2'):
      # Strip .j2 extension for output path
      out_path = abs_path[:-3]
      src_dict = {
        'src_path': abs_path,
        'out_path': out_path
      }
      sources.append(src_dict)

# Jinja2 environment
env = Environment(
  loader=BaseLoader()
)

# Render all templates
for src_dict in sources:
  with open(src_dict['src_path'],'r') as src_file:
    with open(src_dict['out_path'],'w') as out_file:
      out_file.write(env.from_string(src_file.read()).render())
