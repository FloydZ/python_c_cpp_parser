#!/usr/bin/env python3
from python_c_cpp_parser.clang import *


def test_available():
    c = clang_parser("c/funcs/simple.c")
    c.__available__()


def test_simple_func():
    c = clang_parser("c/funcs/simple.c")
    c.execute()
    assert len(c.get_function_decls()) == 1
    f = c.get_function_decls(0)
    body = f.get_body()
    assert body


def test_int_return_func():
    c = clang_parser("c/funcs/int_ret_type.c")
    c.execute()
    assert len(c.get_function_decls()) == 1
    f = c.get_function_decls(0)
    rt = f.get_return_type()
    assert rt
    assert rt == "int ()"


def test_var_decls_func():
    c = clang_parser("c/funcs/decl.c")
    c.execute()
    assert len(c.get_function_decls()) == 1
    f = c.get_function_decls(0)
    body = f.get_body()
    assert body
    vd = body.get_var_decls()
    assert len(vd) == 1


def test_simple_for_loop():
    c = clang_parser("c/for_loops/simple.c")
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


def test_var_decls_for_loop():
    c = clang_parser("c/for_loops/var_decls.c")
    c.execute()
    assert len(c.get_function_decls()) == 1
    f = c.get_function_decls(0)
    body = f.get_body()
    assert body
    fl = body.get_for_loops(0)
    assert fl
    assert fl.is_basic_loop()
    assert len(fl.get_var_decls()) == 1

    assert fl.get_lower_limit()
    assert fl.get_upper_limit()
    assert fl.get_step_size()


def test_simple_var_decls():
    c = clang_parser("c/var_decl/simple.c")
    c.execute()
    assert len(c.get_function_decls()) == 1
    f = c.get_function_decls(0)
    body = f.get_body()
    assert body
    print()
    print(body)
    assert len(body.get_var_decls()) == 1
    vd = body.get_var_decls(0)
    assert vd
    assert vd.get_width() == 4
    print(vd)
