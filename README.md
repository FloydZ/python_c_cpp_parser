## Note
This project was archived as [pycparser](https://github.com/eliben/pycparser)
already implements everything.

## Installation

via pip:
```shell 
pip install git+https://github.com/FloydZ/python_c_cpp_parser
```

## Build

If you want to work on the project you can directly download it via:
```shell
git clone https://github.com/FloydZ/AssemblyLinePython
```

If you have `nixos` you can install all dependencies via:
```shell 
nix-shell
```
otherwise dependencies can be installed via:
```shell 
pip install -r requirements.txt
```

## Usage:
``` python
from python_c_cpp_parser import clang_parser

c = clang_parser("test/c/for_loops/simple.c")
c.execute()
assert len(c.get_function_decls()) == 1
f = c.get_function_decls(0)
body = f.get_body()
assert body
fl = body.get_for_loops(0)
assert fl
assert fl.is_basic_loop()
assert len(fl.get_var_decls()) == 0

assert fl.get_lower_limit()
assert fl.get_upper_limit()
assert fl.get_step_size()
```

## TODOs

- [] parse variable into z3 variable
- [] allow to parse only selected functions
