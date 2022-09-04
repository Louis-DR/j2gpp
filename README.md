# j2gpp - Jinja2-based General Purpose Preprocessor

`j2gpp` is a command-line tool for rendering templates using the Jinja2 syntax. It's intended purpose is to serve as a preprocessor for any programming or markup language with a unified syntax and flow accross languages.

## Basic usage

`j2gpp` requires at least one source be provided. The source paths can be relative or absolute, and can use UNIX-style patterns such as wildcards. Template file names must end with the `.j2` extension which will be stripped at render.

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

```
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

| Argument      | Description                                                |
|---------------|------------------------------------------------------------|
| `-O/--outdir` | Output directory for all rendered templates                |
| `-o/--output` | Output file for single template                            |
| `-I/--incdir` | Include search directory for include and import statements |
| `-D/--define` | Inline global variables for all templates                  |

## Specify output directory

By default the rendered files are saved next to the source templates. You can provide an output directory with the `-O/--outdir` argument. The output directory path can be relative or absolute. If the directory doesn't exist, it will be created.

For instance the following command will write the rendered file to `./bar/foo.c`.

```
j2gpp ./foo.c.j2 --outdir ./bar/
```

## Specifying output file

By default the rendered files are saved next to the source templates. If a single source template is provided, you can specify the output file directory and name with the `-o/--output` argument. The output file path can be relative or absolute. If the directory doesn't exist, it will be created.

For instance the following command will write the rendered file to `./bar.c`.

```
j2gpp ./foo.c.j2 --output ./bar.c
```

## Include search directory

The `include` and `import` Jinja2 statements require specifying the directory in which the renderer will search. That is provided using the `-I/--incidr` argument.

For instance, with the following command, the files in the directory `./includes/` will be available to `include` and `import` statements when rendering the template `foo.c.j2`.

```
j2gpp ./foo.c.j2 --incdir ./includes/
```

## Passing variables in command line

You can pass global variables to all templates rendered using the `-D/--define` argument with a list of variables in the format `name=value`. Integers and floats are automatically cast to allow math operations in the templates.

For instance, with the following command, the variable `bar` will have the value `42` when rendering the template `foo.c.j2`.

```
j2gpp ./foo.c.j2 --define bar=42
```
