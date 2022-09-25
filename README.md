# j2gpp - Jinja2-based General Purpose Preprocessor

`j2gpp` is a command-line tool for rendering templates using the Jinja2 syntax. It's intended purpose is to serve as a preprocessor for any programming or markup language with a unified syntax and flow across languages.

## Installation

With `Python >= 3.6`, Install from Pypi :

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
  printf({{message}});
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
  printf(Hello, world!);
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
| `--csv-delimiter`       | CSV delimiter (default: ',')                                   |
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

### Option flags

Some arguments are flags to enable or disable special features. This is more advanced but can be useful in niche situations.

`--csv-delimiter` followed by a string will change the delimiter used to parse CSV variables files. The default is "`,`".

`--csv-escapechar` followed by a character will set the escape character used to parse CSV variables files. There is no escape character by default.

`--csv-dontstrip` will disable the stripping of whitespace from CSV keys and values.

`--render-non-template` forces every source file found to be rendered, even if they are not recognized as a template (by ending with a template extension). The resulting file will be saved in the location following the rules of regular templates, but instead of removing the template extension, they will have a suffix added before the file extensions. By default, this suffix is `_j2gpp`, but this can be replaced by whatever is specified after the flag argument.

`--copy-non-template` will copy the source files that are not recognized as templates or the files in the source directories to the output directory when one is provided with the `--outdir` argument.

`--force-glob` enables globbing UNIX-like patterns in the source files paths even if they are surrounded by quotes. This is disabled by default to allow processing files with `*` and `[...]` in their path. Paths provided without quotes are preprocessed by the shell and any wildcard or other patterns cannot be prevented.

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

Note that XML expects data to be divided in sections with a header in square brackets. To avoid having to specify the root element when using the variables in a template, J2GPP automatically flattens the section whose header is "`_`".

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

CSV and TSV use the same loader, just with different delimiters. A different delimiter can be provided with the argument `--csv-delimiter`. To use the delimiter in a value, it can be escaped by defining an escape character with the argument `csv-escapechar`, for instance the backslash "`\`".

By default, the whitespace around the keys and values in the CSV is stripped. This behaviour can be disabled with the argument `csv-dontstrip`.

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
