# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ Project:     j2gpp - Jinja2-based General Purpose Preprocessor            ║
# ║ Author:      Louis Duret-Robert - louisduret@gmail.com                    ║
# ║ Website:     louis-dr.github.io                                           ║
# ║ License:     MIT License                                                  ║
# ║ File:        setup.py                                                     ║
# ╟───────────────────────────────────────────────────────────────────────────╢
# ║ Description: Setuptools configuration to build the command line program.  ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝



from setuptools import setup, find_packages

setup(name         = 'j2gpp',
      version      = '2.0.2',
      description  = 'A Jinja2-based General Purpose Preprocessor',
      keywords     = ['j2gpp', 'jinja2', 'preprocessor'],
      url          = 'https://github.com/Louis-DR/j2gpp',
      author       = 'Louis Duret-Robert',
      author_email = 'louisduret@gmail.com',
      license      = 'MIT',
      license_file = 'LICENSE',

      long_description              = open('README.md').read(),
      long_description_content_type = 'text/markdown',

      packages     = find_packages(),
      entry_points = {
        'console_scripts': ['j2gpp = j2gpp:main']
      },
      install_requires = [
        'jinja2',
        'ruamel.yaml',
        'xmltodict',
        'toml',
        'configparser'
      ],
)
