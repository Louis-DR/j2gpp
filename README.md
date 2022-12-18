# J2GPP - Jinja2-based General Purpose Preprocessor

`j2gpp` is a command-line tool for rendering templates using the Jinja2 syntax. It's intended purpose is to serve as a preprocessor for any programming or markup language with a unified syntax and flow across languages.

- [J2GPP - Jinja2-based General Purpose Preprocessor](#j2gpp---jinja2-based-general-purpose-preprocessor)
  - [Installation](#installation)
  - [Basic usage](#basic-usage)
  - [Command line arguments](#command-line-arguments)
    - [Specify output directory](#specify-output-directory)
    - [Specifying output file](#specifying-output-file)
    - [Include search directory](#include-search-directory)
    - [Passing global variables in command line](#passing-global-variables-in-command-line)
    - [Loading global variables from files](#loading-global-variables-from-files)
    - [Loading global variables from environment](#loading-global-variables-from-environment)
    - [Loading custom Jinja2 filters](#loading-custom-jinja2-filters)
    - [Loading custom Jinja2 tests](#loading-custom-jinja2-tests)
    - [Post-processing variables files](#post-processing-variables-files)
    - [Option flags](#option-flags)
    - [Context variables](#context-variables)
    - [Built-in filters](#built-in-filters)
  - [Process directories](#process-directories)
  - [Supported formats for variables](#supported-formats-for-variables)
    - [Command line define](#command-line-define)
    - [YAML](#yaml)
    - [JSON](#json)
    - [XML](#xml)
    - [TOML](#toml)
    - [INI/CFG](#inicfg)
    - [ENV](#env)
    - [CSV/TSV](#csvtsv)
  - [Scripting in J2GPP templates](#scripting-in-j2gpp-templates)
    - [Conditional and do extension](#conditional-and-do-extension)
    - [Conditional and filters](#conditional-and-filters)
    - [Writing files](#writing-files)
      - [Write example](#write-example)
      - [Append example](#append-example)
      - [Path argument](#path-argument)
      - [Writing to both files](#writing-to-both-files)
      - [Skipping the parent file](#skipping-the-parent-file)


## Installation

With `Python >= 3.7`, Install from Pypi :

``` shell
pip install j2gpp
```

## Basic usage

`j2gpp` requires at least one source be provided. The source paths can be files or directories, relative or absolute, and can use UNIX-style patterns such as wildcards. Template file names must end with the `.j2` extension which will be stripped at render.

For more information about the Jinja2 syntax, see the documentation at [jinja.palletsprojects.com](https://jinja.palletsprojects.com/).

For instance, suppose we have a templatized source file `foo.c.j2` :

``` c
#include <stdio.h>

{% set message = "Hello, world!" %}

int main() {
  printf("{{message}}");
  return 0;
}
```

We can render the template using `j2gpp` :

``` shell
j2gpp ./foo.c.j2
```

The output is written to `foo.c` next to the source template :

``` c
#include <stdio.h>

int main() {
  printf("Hello, world!");
  return 0;
}
```

The following arguments can be added to the command for additional features. The details of each command is explained in the sections below.

| Argument                | Description                                                    |
| ----------------------- | -------------------------------------------------------------- |
| `-O/--outdir`           | Output directory for all rendered templates                    |
| `-o/--output`           | Output file for single template                                |
| `-I/--incdir`           | Include search directory for include and import statements     |
| `-D/--define`           | Inline global variables for all templates                      |
| `-V/--varfile`          | Global variables files for all templates                       |
| `--envvar`              | Loads environment variables as global variables                |
| `--filters`             | Load extra Jinja2 filters from a Python file                   |
| `--tests`               | Load extra Jinja2 tests from a Python file                     |
| `--vars-post-processor` | Load a Python function to process variables after loading      |
| `--overwrite-outdir`    | Overwrite output directory                                     |
| `--warn-overwrite`      | Warn when overwriting files                                    |
| `--no-overwrite`        | Prevent overwriting files                                      |
| `--no-check-identifier` | Disable warning when attributes are not valid identifiers      |
| `--fix-identifiers`     | Replace invalid characters from identifiers with underscore    |
| `--csv-delimiter`       | CSV delimiter (default: '`,`')                                 |
| `--csv-escapechar`      | CSV escape character (default: None)                           |
| `--csv-dontstrip`       | Disable stripping whitespace of CSV values                     |
| `--render-non-template` | Process also source files that are not recognized as templates |
| `--copy-non-template`   | Copy source files that are not templates to output directory   |
| `--force-glob`          | Glob UNIX-like patterns in path even when quoted               |
| `--perf`                | Measure the execution time for performance testing             |
| `--version`             | Print J2GPP version and quits                                  |
| `--license`             | Print J2GPP license and quits                                  |

## Command line arguments

### Specify output directory

By default the rendered files are saved next to the source templates. You can provide an output directory with the `-O/--outdir` argument. The output directory path can be relative or absolute. If the directory doesn't exist, it will be created.

For instance the following command will write the rendered file to `./bar/foo.c`.

``` shell
j2gpp ./foo.c.j2 --outdir ./bar/
```

### Specifying output file

By default the rendered files are saved next to the source templates. If a single source template is provided, you can specify the output file directory and name with the `-o/--output` argument. The output file path can be relative or absolute. If the directory doesn't exist, it will be created.

For instance the following command will write the rendered file to `./bar.c`.

``` shell
j2gpp ./foo.c.j2 --output ./bar.c
```

### Include search directory

The `include` and `import` Jinja2 statements require specifying the directory in which the renderer will search. That is provided using the `-I/--incidr` argument.

For instance, with the following command, the files in the directory `./includes/` will be available to `include` and `import` statements when rendering the template `foo.c.j2`.

``` shell
j2gpp ./foo.c.j2 --incdir ./includes/
```

### Passing global variables in command line

You can pass global variables to all templates rendered using the `-D/--define` argument with a list of variables in the format `name=value`. Values are parsed to cast to the correct Python type as explained [later](#command-line-define). Dictionary attributes to any depth can be assigned using dots "`.`" to separate the keys. Global variables defined in the command line overwrite the global variables set by loading files.

For instance, with the following command, the variable `bar` will have the value `42` when rendering the template `foo.c.j2`.

``` shell
j2gpp ./foo.c.j2 --define bar=42
```

### Loading global variables from files

You can load global variables from files using the `-V/--varfile` argument with a list of files. The file paths can be relative or absolute, and can use UNIX-style patterns such as wildcards. Variables file types supported right now are YAML, JSON, XML, TOML, INI/CFG, ENV, CSV and TSV. Global variables loaded from files are overwritten by variables defined in the command line.

For instance, with the following command, the variable `bar` will have the value `42` when rendering the template `foo.c.j2`.

``` shell
j2gpp ./foo.c.j2 --varfile ./qux.yml
```

With the variables file `qux.yml` :

``` yml
bar: 42
```

### Loading global variables from environment

You can import the environment variables of the shell as global variables using the `--envvar` argument. The name of the variables will be that of the environment variable and the value will be cast automatically to the proper Python/Jinja2 type.

For instance, with the following command, the variable `BAR` will have the value `42` when rendering the template `foo.c.j2`.

``` shell
export BAR=42
j2gpp ./foo.c.j2 --envvar
```

If a string is provided after the `--envvar` argument, the environment variables will be stored in an object of the name provided instead of at the root.

For instance, with the following command, the variable `ENV.BAR` will have the value `42` when rendering the template `foo.c.j2`.

``` shell
export BAR=42
j2gpp ./foo.c.j2 --envvar ENV
```

### Loading custom Jinja2 filters

You can import custom Jinja2 filters by providing Python files with the `--filters` argument. All functions defined in the python files will be available as Jinja2 filters in the templates.

For instance, with the following command and python file, the filter `right_ajust` will be available when rendering the template `foo.c.j2`.

``` shell
j2gpp ./foo.c.j2 --filters ./bar.py
```

``` python
# bar.py
def right_ajust(s, length=0):
  return s.rjust(length)
```

### Loading custom Jinja2 tests

You can import custom Jinja2 tests by providing Python files with the `--tests` argument. All functions defined in the python files will be available as Jinja2 tests in the templates.

For instance, with the following command and python file, the test `prime` will be available when rendering the template `foo.c.j2`.

``` shell
j2gpp ./foo.c.j2 --tests ./bar.py
```

``` python
# bar.py
import math
def prime(x):
  if x<=1: return False
  for i in range(2,int(math.sqrt(x))+1):
    if (x%i) == 0:
      return False
  return True
```

### Post-processing variables files

You can perform transformations on the dictionary returned after processing a variables files by providing a Python function with the argument `--vars-post-processor`. It takes two arguments, the first is the path to the Python script, and the second is the name of the function to use. The function must take in a single argument, the variables dictionary, and modify it as a reference (not return the modified dictionary).

For instance, with the following command and python file, the variable dictionary loaded from the file `qux.yml` will be processed by the function `shout_values()` before rendering the template `foo.c.j2`.

``` shell
j2gpp ./foo.c.j2 --varfile ./qux.yml --vars-post-processor ./bar.py shout_values
```

``` python
# bar.py
def shout_values(var_dict):
  for key,val in var_dict.items():
    if isinstance(val, str):
      var_dict[key] = val.upper()
```

### Option flags

Some arguments are flags to enable or disable special features. This is more advanced but can be useful in niche situations.

`--overwrite-outdir` cleans the output directory before rendering the templates and copying any other files.

`--warn-overwrite` enables warnings triggered whenever a file is overwritten.

`--no-overwrite` prevents any file from being overwritten, and triggers a warning when that happens.

`--no-check-identifier` disables the ckecking that the variables names and attributes are valid Python identifiers. Root variables with a name not passing this check will not be accessible in Jinja2 templates.

`--fix-identifiers` fixes variables and attributes names that are not valid Python identifiers by replacing incorrect characters by underscores, and if the first character is a number, an underscore is added before.

`--csv-delimiter` followed by a string will change the delimiter used to parse CSV variables files. The default is "`,`".

`--csv-escapechar` followed by a character sets the escape character used to parse CSV variables files. There is no escape character by default.

`--csv-dontstrip` disables the stripping of whitespace from CSV keys and values.

`--render-non-template` forces every source file found to be rendered, even if they are not recognized as a template (by ending with a template extension). The resulting file will be saved in the location following the rules of regular templates, but instead of removing the template extension, they will have a suffix added before the file extensions. By default, this suffix is `_j2gpp`, but this can be replaced by whatever is specified after the flag argument.

`--copy-non-template` enables the copying of the source files that are not recognized as templates or the files in the source directories to the output directory when one is provided with the `--outdir` argument.

`--force-glob` enables globbing UNIX-like patterns in the source files paths even if they are surrounded by quotes. This is disabled by default to allow processing files with `*` and `[...]` in their path. Paths provided without quotes are preprocessed by the shell and any wildcard or other patterns cannot be prevented.

### Context variables

Useful context variables are added before any other variable is loaded. Some are global for all templates rendered, and some are template-specific.

| Variable                | Scope    | Description                                   |
| ----------------------- | -------- | --------------------------------------------- |
| `__python_version__`    | Global   | Python version                                |
| `__jinja2_version__`    | Global   | Jinja2 version                                |
| `__j2gpp_version__`     | Global   | J2GPP version                                 |
| `__user__`              | Global   | Name of the current user                      |
| `__pid__`               | Global   | Process ID of the current process             |
| `__ppid__`              | Global   | Process ID of the parent process              |
| `__working_directory__` | Global   | Working directory                             |
| `__output_directory__`  | Global   | Output directory                              |
| `__date__`              | Global   | Date in the format `DD-MM-YYYY`               |
| `__date_inv__`          | Global   | Date in the format `YYYY-MM-DD`               |
| `__time__`              | Global   | Time in the format `hh:mm:ss`                 |
| `__datetime__`          | Global   | Timestamp in the format `YYYY-MM-DD hh:mm:ss` |
| `__source_path__`       | Template | Path of the source template file              |
| `__output_path__`       | Template | Path where the template is rendered           |

### Built-in filters

In addition to the [Jinja2 built-in filters](https://jinja.palletsprojects.com/en/latest/templates/#builtin-filters), J2GPP also defines many useful filter functions.

All functions from the Python libraries `math` and `statistics` are made available as filters. This includes useful functions such as `sqrt`, `pow`, `log`, `sin`, `cos`, `floor`, `ceil`, `mean`, `median`, `variance`, `stdev`, ...

An operation can be applied to all elements of a list with the filters `list_add`, `list_sub`, `list_mult`, `list_div`, `list_mod`, `list_rem` and `list_exp` respectively for the Python operators `+`, `-`, `*`, `/`, `%`, `//` and `**`.

Text alignment can be controlled with the Python functions `ljust`, `rjust` and `center`.

Case and formatting can be controlled with the Python functions `title` and `swapcase`, or the added functions `camel`, `pascal`, `snake` and `kebab`. `camel` and `pascal` will remove the underscores and hyphens by default but leave the dots ; that behaviour can be changed by providing the filter arguments `remove_underscore`, `remove_hyphen` and `remove_dot` as `True` or `False`. `snake` and `kebab` will group capitalized letters and preserve capitalization by default ; that behaviour can be changed by providing the filter arguments `preserve_caps` and `group_caps` as `True` or `False`.

Paragraph formatting is facilitated by multiple filters that should be used on a `filter` block. `reindent` removes pre-existing indentation and sets new one. `autoindent` removes pre-existing indentation and sets new indent by incrementing and decrementing the depth based on start and end delimiters of blocks provided by the `starts` and `ends` lists of strings provided by argument (culry braces by default). `align` aligns every line of the paragraph by columns, left before `§`, right before `§§`.

When using a list of dictionaries with a key in common, you can get the list element with the minimum or maximum value of that attribute using the filters `el_of_max_attr` or `el_of_min_attr`.

When using two-level dictionaries, the key corresponding to the minimum or maximum with regards to a specified attribute using the filters `key_of_max_attr` or `key_of_min_attr`.

You can count the number of occurrences of a value in a list using the `count` filter.

The `write` and `append` filters can be used to export the content of a filter to another file whose path is provided as argument to the filter. The path can be absolute or relative to the output rendered base template. By default, the content of the filter is not written to the base rendered template ; this behaviour can be changed by providing the filter argument `preserve` as `True`. The source template can also be prevented from resulting in a generated file by providing the filter argument `write_source` as `False`, and only the content of `write` and `append` blocks will generate files.

## Process directories

When the source path provided corresponds to a directory, J2GPP will look for any template files in the source directory tree. If no output directory argument is provided, the rendered files will be written next to the source templates. If an output directory is provided, the source directory tree structure will be copied to the output directory with only the rendered files.

For instance, suppose we have the following directory structure :

``` txt
.
└── test_dir
    ├── sub_dir_1
    │   ├── deep_dir
    │   │   └── template_1.txt.j2
    │   └── non_template_1.txt
    ├── sub_dir_2
    │   └── non_template_2.txt
    └── template_2.txt.j2
```

When we execute the command `j2gpp ./test_dir/`, we will get :

``` txt
.
└── test_dir
    ├── sub_dir_1
    │   ├── deep_dir
    │   │   ├── template_1.txt
    │   │   └── template_1.txt.j2
    │   └── non_template_1.txt
    ├── sub_dir_2
    │   └── non_template_2.txt
    ├── template_2.txt
    └── template_2.txt.j2
```

But if we provide an output directory with the command `j2gpp ./test_dir/ --outdir ./out_dir/`, we will get :

``` txt
.
├── test_dir
│   ├── sub_dir_1
│   │   ├── deep_dir
│   │   │   └── template_1.txt.j2
│   │   └── non_template_1.txt
│   ├── sub_dir_2
│   │   └── non_template_2.txt
│   └── template_2.txt.j2
└── out_dir
    ├── sub_dir_1
    │   └── deep_dir
    │       └── template_1.txt
    └── template_2.txt
```

We can also tell J2GPP to copy the non-template files with the command `j2gpp ./test_dir/ --outdir ./out_dir/ --copy-non-template`, then we will get :

``` txt
.
├── test_dir
│   ├── sub_dir_1
│   │   ├── deep_dir
│   │   │   └── template_1.txt.j2
│   │   └── non_template_1.txt
│   ├── sub_dir_2
│   │   └── non_template_2.txt
│   └── template_2.txt.j2
└── out_dir
    ├── sub_dir_1
    │   ├── deep_dir
    │   │   └── template_1.txt
    │   └── non_template_1.txt
    ├── sub_dir_2
    │   └── non_template_2.txt
    └── template_2.txt
```

Or even to process non-templates files as templates anyway with the command `j2gpp ./test_dir/ --outdir ./out_dir/ --render-non-template`, then we will get :

``` txt
.
├── test_dir
│   ├── sub_dir_1
│   │   ├── deep_dir
│   │   │   └── template_1.txt.j2
│   │   └── non_template_1.txt
│   ├── sub_dir_2
│   │   └── non_template_2.txt
│   └── template_2.txt.j2
└── out_dir
    ├── sub_dir_1
    │   ├── deep_dir
    │   │   └── template_1.txt
    │   └── non_template_1_j2gpp.txt
    ├── sub_dir_2
    │   └── non_template_2_j2gpp.txt
    └── template_2.txt
```

## Supported formats for variables

Jinja2 supports variables types from python. The main types are None, Boolean, Integer, Float, String, Tuple, List and Dictionary. J2GPP provides many ways to set variables and not all types are supported by each format.

### Command line define

Defines passed by the command line are interpreted by the Python [ast.literal_eval()](https://docs.python.org/3/library/ast.html#ast.literal_eval) function which supports Python syntax and some additional types such as `set()`.

``` shell
j2gpp ./foo.c.j2 --define test_none=None             \
                          test_bool=True             \
                          test_int=42                \
                          test_float=3.141592        \
                          test_string1=lorem         \
                          test_string2="lorem ipsum" \
                          test_tuple="(1,2,3)"       \
                          test_list="[1,2,3]"        \
                          test_dict="{'key1': value1, 'key2': value2}" \
                          test_dict.key3=value3
```

### YAML

``` yml
test_none1:
test_none2: null

test_bool1: true
test_bool2: false

test_int: 42
test_float: 3.141592

test_string1: lorem ipsum
test_string2:
  single
  line
  text
test_string3: |
  multi
  line
  text

test_list1: [1,2,3]
test_list2:
  - 1
  - 2
  - 3

test_dict:
  key1: value1
  key2: value2
  key3: value3
```

### JSON

``` json
{
  "test_none": null,

  "test_bool1": true,
  "test_bool2": false,

  "test_int": 42,
  "test_float": 3.141592,

  "test_string": "lorem ipsum",

  "test_list": [1,2,3],

  "test_dict": {
    "key1": "value1",
    "key2": "value2",
    "key3": "value3"
  }
}
```

### XML

Note that XML expects a single root element. To avoid having to specify the root element when using the variables in a template, J2GPP automatically removes the root element level if it is named "`_`".

``` xml
<_>
  <test_none></test_none>

  <test_bool1>true</test_bool1>
  <test_bool2>false</test_bool2>

  <test_int>42</test_int>
  <test_float>3.141592</test_float>

  <test_string>lorem ipsum</test_string>

  <test_list>1</test_list>
  <test_list>2</test_list>
  <test_list>3</test_list>

  <test_dict>
    <key1>value1</key1>
    <key2>value2</key2>
    <key3>value3</key3>
  </test_dict>
</_>
```

### TOML

``` toml
test_bool1 = true
test_bool2 = false

test_int = 42
test_float = 3.141592

test_string1 = "lorem ipsum"
test_string2 = """
multi
line
text"""

test_list = [1,2,3]

[test_dict]
key1 = "value1"
key2 = "value2"
key3 = "value3"
```

### INI/CFG

Note that INI file expects data to be divided in sections with a header in square brackets. To avoid having to specify the root element when using the variables in a template, J2GPP automatically flattens the section whose header is "`_`".

``` ini
[_]
test_bool1 = True
test_bool2 = False

test_int = 42
test_float = 3.141592

test_string = "lorem ipsum"

test_list = [1,2,3]

[test_dict]
key1 = value1
key2 = value2
key3 = value3
```

### ENV

``` env
test_bool1 = True
test_bool2 = False

test_int = 42
test_float = 3.141592

test_string = lorem ipsum

test_list = [1,2,3]

test_dict = {'key1':'value1','key2':'value2','key3':'value3'}
```

### CSV/TSV

CSV and TSV are interpreted as a list of objects with the same attributes. They are converted to a list of dictionaries whose name is the first cell of each line and the keys are the headers of each column.

CSV and TSV use the same loader, just with different delimiters. A different delimiter can be provided with the argument `--csv-delimiter`. To use the delimiter in a value, it can be escaped by defining an escape character with the argument `--csv-escapechar`, for instance the backslash "`\`".

By default, the whitespace around the keys and values in the CSV is stripped. This behaviour can be disabled with the argument `--csv-dontstrip`.

``` csv
keys,key1,key2,key3
test_dict1,1,2,3
test_dict2,11,12,13
test_dict3,21,22,23
```

``` tsv
keys  key1  key2  key3
test_dict1  1  2  3
test_dict2  11  12  13
test_dict3  21  22  23
```

## Scripting in J2GPP templates

An advanced use of the template feature and filters of Jinja2 and J2GPP allow this tool to do some amount of scripting. The main features allowing this usage are explained in this section.

### Conditional and do extension

The basic Jinja2 feature of conditional blocks `if`/`elif`/`else` can be used alongside the `do` extension to more easily manipulate variables and complex objects such as Python dictionaries.

Note that, if possible, it is preferable to process the variables after loading and before rendering by providing a Python function with the `--vars-post-processor` command line argument.

### Conditional and filters

As filters are Python functions, they can be very powerful, especially when coupled with the use of conditional blocks. However, Jinja2 optimizes processing by running some filters during the compilation phase, while conditional blocks are resolved at render time.

To fix this, you can use the `@render_time_only` decorator to force a filter or test to execute at render time only. This decorator is [currently](https://github.com/pallets/jinja/pull/1759) only available by installing a custom fork of Jinja2 :

``` shell
git clone https://github.com/Louis-DR/jinja.git
cd jinja
pip3 install ./
```

### Writing files

The J2GPP filters `write` and `append` allow exporting the content of a block to another file. This can be used for a file combining elements contributed by multiple templates, for alternative versions of a file from a single template, for generating small annex files to a large template, for generating a files for each element in a list, etc. When coupled with the `include` or `macro` statements with nested temlates, it allows for even more complex outputs.

#### Write example

For example, with the parent template `parent.txt.j2`:

``` jinja2
This will be rendered to the parent output file
{% filter write("child.txt") %}
This will be rendered to the child output file
{% endfilter %}
```

``` shell
>>> tree
.
└── parent.txt.j2

>>> j2gpp ./parent.txt.j2
[...]

>>> tree
.
├── child.txt
├── parent.txt
└── parent.txt.j2

>>> cat parent.txt
This will be rendered to the parent output file

>>> cat child.txt
This will be rendered to the child output file
```

#### Append example

If the file doesn't exists, the `append` filter will create it and be equivalent to `write`. However, if the file already exists, `write` will override it while `append` will append to the end of it. For example, with the parent template `parent.txt.j2`:

``` jinja2
This will be rendered to the parent output file
{% filter append("child.txt") %}
This will be rendered to the child output file
{% endfilter %}
```

``` shell
>>> tree
.
└── parent.txt.j2

>>> j2gpp ./parent.txt.j2
[...]

>>> tree
.
├── child.txt
├── parent.txt
└── parent.txt.j2

>>> cat parent.txt
This will be rendered to the parent output file

>>> cat child.txt
This will be rendered to the child output file

>>> j2gpp ./parent.txt.j2
[...]

>>> cat child.txt
This will be rendered to the child output file
This will be rendered to the child output file

>>> j2gpp ./parent.txt.j2
[...]

>>> cat child.txt
This will be rendered to the child output file
This will be rendered to the child output file
This will be rendered to the child output file
```

#### Path argument

The `write` and `append` filters require at least one argument, the name or path of the second file to generate. The path can be absolute, or relative to the generated file of the parent template. Non-existing directories will be created. For example, with the parent template `parent.txt.j2`:

``` jinja2
{% filter write("foo/child.txt") %}
This will be rendered to the child output file
{% endfilter %}
```

``` shell
>>> tree
.
└── src
    └── parent.txt.j2

>>> j2gpp ./src/parent.txt.j2 --outdir ./gen/
[...]

>>> tree
.
├── src
│   └── parent.txt.j2
└── gen
    ├── foo
    │   └── child.txt
    └── parent.txt
```

#### Writing to both files

By default, the content of the block is only written to the child file, and is not written to the parent rendered template. This behaviour can be changed by providing the filter argument `preserve` as `True`. For example, with the parent template `parent.txt.j2`:

``` jinja2
{% filter write("child.txt", preserve=True) %}
This will be rendered to both parent and child output files
{% endfilter %}
```

``` shell
>>> j2gpp ./parent.txt.j2 --outdir ./gen/
[...]

>>> cat ./parent.txt
This will be rendered to both parent and child output files

>>> cat ./child.txt
This will be rendered to both parent and child output files
```

#### Skipping the parent file

The source template can also be prevented from resulting in a generated file by providing the filter argument `write_source` as `False`, and only the content of `write` and `append` blocks will generate files. For example, with the parent template `parent.txt.j2`:

``` jinja2
This will not be written to any file
{% filter write("child.txt") %}
This will be rendered to the child output file
{% endfilter %}
```

``` shell
>>> tree
.
└── parent.txt.j2

>>> j2gpp ./parent.txt.j2
[...]

>>> tree
.
├── child.txt
└── parent.txt.j2

>>> cat child.txt
This will be rendered to the child output file
```
