import argparse
import glob
import os
from jinja2 import Environment, BaseLoader

# Command line arguments
argparser = argparse.ArgumentParser()
argparser.add_argument("source",                        help="Path to library file",             nargs='+')
argparser.add_argument("-O", "--outdir", dest="outdir", help="Output directory path"                      )
args = argparser.parse_args()

# Parsing arguments
arg_source = args.source
out_dir = ""
if args.outdir:
  out_dir = os.path.expandvars(os.path.expanduser(os.path.abspath(args.outdir)))
  if not os.path.isdir(out_dir):
    os.makedirs(out_dir)

# Collecting source templates paths
sources = []
for raw_path in arg_source:
  # Glob to apply UNIX-style path patterns
  for glob_path in glob.glob(raw_path):
    abs_path = os.path.abspath(glob_path)
    # Only keep files ending with .j2 extension
    if os.path.isfile(abs_path) and abs_path.endswith('.j2'):
      # Strip .j2 extension for output path
      out_path = abs_path[:-3]
      if out_dir:
        out_path = os.path.join(out_dir, os.path.basename(out_path))
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
      print(f"Rendering {src_dict['src_path']} to {src_dict['out_path']}")
      out_file.write(env.from_string(src_file.read()).render())
