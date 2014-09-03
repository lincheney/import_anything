# import_anything

Tested on Python 3.3

`import_anything` is a python3 library to allow you to import anything ... so long as you can translate it into python first.

Once you have a source-to-python compiler for your custom code implemented, `import_anything` will allow you treat your files as if they were python modules.

This means you'll be able to:
- import them with an ordinary `import` statement
- import any supported files on `sys.path`
- have your custom code further compiled to python bytecode which is then cached
- have the bytecode recompiled whenever the source file changes or your compiler changes

`import_anything` also modifies the AST (abstract syntax tree) line numbers to point back to the correct lines in the original source, so your error tracebacks will actually look correct.

## Using `import_anything`

```python
import import_anything

class Compiler(import_anything.Compiler):
    def translate(self, file):
        # insert some code here to translate @file into python
        ...

loader = import_anything.Loader.factory(compiler = Compiler)
import_anything.Finder.register(loader, ['.custom-py', '.another-py'])

import your_custom_module
```

The above code will look for `your_custom_module.custom-py` or `your_custom_module.another-py` on sys.path, run the file through `Compiler.translate` and then import the resulting python code.

`Compiler.translate` should yield `(line-number, line-of-python)`. The line-number refers to the line in the original untranslated file; this is what allows you to get tracebacks that actually show the correct line.
