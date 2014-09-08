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

class MyCompiler(import_anything.Compiler):
    def translate(self, file):
        # insert some code here to translate @file into python
        ...

loader = import_anything.Loader.factory(compiler = Compiler)
import_anything.Finder.register(loader, ['.custom-py', '.another-py'])

import your_custom_module
```

The above code will look for `your_custom_module.custom-py` or `your_custom_module.another-py` on sys.path, run the file through `Compiler.translate` and then import the resulting python code.

`Compiler.translate` should yield `(line-number, line-of-python)`. The line-number refers to the line in the original untranslated file; this is what allows you to get tracebacks that actually show the correct line.

You can find some examples under examples/.

## Bytecode recompiling

Since your custom code is treated as a normal Python module, this means the cached bytecode in `__pycache__` is automatically recompiled everytime the source changes. However, if your `Compiler` changes (e.g. new version) and you want the bytecode to automatically recompile, you need to use some `MAGIC`.

```python
class MyCompiler(import_anything.Compiler):
    MAGIC = 5
    ...
```

`MyCompiler.MAGIC` is XORed against the Python interpreter's own magic number which is used to track Python version changes. It should fit in a 16-bit unsigned integer.

You can also set the `MAGIC_TAG`:

```python
class MyCompiler(import_anything.Compiler):
    MAGIC = 5
    MAGIC_TAG = 'custom-bytecode'
    ...
```

The tag will be used as part of the cached bytecode filename.
e.g. **name_of_module.cpython-33.custom-bytecode.pyc**
You can use this to differentiate between different compilers/source types. Avoid using tags to indicate compiler versions, since you will just end up with lots of stale bytecode for old compiler versions.
