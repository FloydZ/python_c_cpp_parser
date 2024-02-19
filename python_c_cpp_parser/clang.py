#!/usr/bin/env python3
import copy
from subprocess import Popen, PIPE, STDOUT
from typing import Union
from pathlib import Path
import logging
import sys
import os
import json
import tempfile
import re

# TODO remove
functions_decls = []
compound_decls = []
for_loop_decls = []
while_loop_decls = []
do_loop_decls = []

# NOTE: some design decisions
#   for each `function|compound_stmt` the following node are traced for fast access
#       for_loop
#       while_loop
#       do_loop
#       if_loop
#
#   for each VarDecl its referenced are traced

def str_to_class(classname: str):
    """translate for example the string `TranslationUnitDecl` into that class"""
    return getattr(sys.modules[__name__], classname)


def type2width(t: str) -> Union[int, None]:
    """
    TODO: probably via dict
    """
    # pointer
    if "*" in t:
        # well actually 
        return 8

    if t == "int":
        return 4
    elif t == "long int":
        return 8
    else:
        print(t, "not implemented")
        return -1


class Range:
    """
    TODO describe
    """

    def __init__(self, begin_offset: int, begin_col: int, begin_tokLen: int,
                 end_offset: int, end_col: int, end_tokLen: int):
        self.begin_offset, self.begin_col, self.begin_tokLen = begin_offset, begin_col, begin_tokLen
        self.end_offset, self.end_col, self.end_tokLen = end_offset, end_col, end_tokLen


class Location:
    """
    wrapper around clangs `loc` field.
    """

    def __init__(self, offset: int, file: str, line: int, col: int, tokLen: int):
        self.offset = offset
        self.file = file
        self.line = line
        self.col = col
        self.tokLen = tokLen

    def __str__(self):
        return self.file + str(self.line) + ":" + str(self.col) + ":" + str(self.tokLen)


class Node:
    """
    """

    def __init__(self, id: str, kind: str, *args, **kwargs):
        """
        id and kind are mandatory, hence we are enforcing them
        as function arguments
        """
        self.id = id
        self.kind = kind
        self.__dict__.update((k, v) for k, v in kwargs.items() if k not in ["inner"])
        self.parent = None
        self.__parse_inner(**kwargs)

    def __parse_inner(self, **kwargs):
        """
        recursively parses the next nodes
        """
        inner = kwargs["inner"] if "inner" in kwargs else []
        self.inner = []
        if type(inner) is list and len(inner) > 0:
            for inn in inner:
                if len(inn.keys()) == 0:
                    continue

                C = str_to_class(inn["kind"])
                n = C(**inn)
                n.parent = self
                self.inner.append(n)
        else:
            self.inner = None

    def reparse(self, out, t, recursive=True, check=None):
        """ reparse the current `inner` nodes for type `t` and appends them
        to out"""
        if self.inner is not None:
            for tmp in self.inner:
                if type(tmp) is t:
                    if check is None:
                        out.append(tmp)
                    else:
                        if check(out, tmp):
                            out.append(tmp)
                if recursive:
                    tmp.reparse(out, t, recursive=recursive, check=check)

        return out

    def reparse_single(self, out, t):
        """ reparse the current `inner` nodes for a single type `t`. The
        on first occurrence will set `out` to it, quits afterward"""
        out = None

        # empty compound stmt = empty func
        if self.inner is not None:
            for i in self.inner:
                if type(i) is t:
                    out = i
                    break
        return out

    def get_file(self):
        """
        returns the path to the file where this AST element is located.
        if no location is available: None is returned
        """
        try:
            return self.loc["file"]
        except:
            return None

    def get_location(self):
        """
        returns a `Locations` object if available else None
        """
        try:
            offset = self.loc["offset"]
            file = self.loc["file"] if "file" in self.loc else ""
            line = self.loc["line"]
            col = self.loc["col"]
            tokLen = self.loc["tokLen"]
            return Location(offset, file, line, col, tokLen)
        except:
            return None

    def get_type(self):
        """
        """
        if "type" in self.__dict__.keys():
            return self.type["qualType"]
        return None

    def is_empty(self):
        return len(self.inner) == 0
    
    def width(self):
        t = self.get_type()
        if t is None:
            return None
        return type2width(t)

    def __str__(self, depth=0):
        ret = str(self.id) + " " + str(self.__class__) + "\n"
        if self.inner:
            depth += 1
            t = "\t" * depth
            for a in self.inner:
                ret += t + a.__str__(depth)
        return ret

    def print(self):
        print(self.__dict__)


class TranslationUnitDecl(Node):
    pass


class BuiltinType(Node):
    pass


class IntegerLiteral(Node):
    pass


class ParmVarDecl(Node):
    def __init__(self, id: str, kind: str, *args, **kwargs):
        """
        """
        super().__init__(id, kind, *args, **kwargs)

    def get_width(self):
        """
        returns the width if the variable in bytes
        """
        t = self.get_type()
        assert t
        return type2width(t)

    def is_integral(self):
        """
        returns if a variable is integral: int, long int, ....
        """
        try:
            type2width(self.get_type())
            return True
        except:
            return False

    def get_init_value(self):
        """
        this only makes sense for c++.
        """
        return None

    def is_const(self):
        """
        returns true if variable is const
        """
        raise NotImplementedError


class TypedefDecl(Node):
    pass


class RecordType(Node):
    pass


class PointerType(Node):
    pass


class ConstantArrayType(Node):
    pass


class FunctionDecl(Node):
    def __init__(self, id: str, kind: str, *args, **kwargs):
        """
        exports this additional fields:
        - arguments
        - body
        """
        super().__init__(id, kind, *args, **kwargs)
        self.__arguments = []
        self.__return_type = []
        self.__body = None

        # find the function arguments
        if self.inner is not None:
            for i in self.inner:
                if type(i) is ParmVarDecl:
                    self.__arguments.append(i)

            # find the function body:
            for i in self.inner:
                if type(i) is CompoundStmt:
                    self.__body = i

        # kind of strange
        self.__return_type = kwargs["type"]["qualType"]
        # NOTE: we cannot assert this, because there are empty function
        # assert self.__body
        functions_decls.append(self)

    def get_arguments(self):
        return self.__arguments

    def get_body(self):
        return self.__body

    def get_return_type(self):
        return self.__return_type


class CompoundStmt(Node):
    def __init__(self, id: str, kind: str, *args, **kwargs):
        """
        exports this additional fields:
        - var_decls
        - for_loops
        - do_loops
        - while_loops
        - calls
        """
        super().__init__(id, kind, *args, **kwargs)
        self.__var_decls = []
        self.__for_loops = []
        self.__while_loops = []
        self.__calls = []
        self.__do_loops = []
        self.__isempty = self.inner is None

        self.reparse(self.__var_decls, DeclStmt, recursive=False)
        self.reparse(self.__for_loops, ForStmt)
        self.reparse(self.__while_loops, WhileStmt)
        self.reparse(self.__do_loops, DoStmt)
        self.reparse(self.__calls, CallExpr)
        compound_decls.append(self)

    def get_var_decls(self, i: int = None):
        if i is not None:
            if i > len(self.__var_decls):
                print("OOB")
                return None
            return self.__var_decls[i]
        return self.__var_decls

    def get_for_loops(self, i: int = None):
        if i is not None:
            if i > len(self.__for_loops):
                print("OOB")
                return None
            return self.__for_loops[i]
        return self.__for_loops

    def get_do_loops(self, i: int = None):
        if i is not None:
            if i > len(self.__do_loops):
                print("OOB")
                return None
            return self.__do_loops[i]
        return self.__do_loops

    def get_while_loops(self, i: int = None):
        if i is not None:
            if i > len(self.__while_loops):
                print("OOB")
                return None
            return self.__while_loops[i]
        return self.__while_loops

    def print(self):
        print(self.__dict__)


class DeclStmt(Node):
    def __init__(self, id: str, kind: str, *args, **kwargs):
        """
        """
        super().__init__(id, kind, *args, **kwargs)
        self.refs = []

    def get_references(self):
        return self.refs


class VarDecl(Node):
    def __init__(self, id: str, kind: str, *args, **kwargs):
        """
        """
        super().__init__(id, kind, *args, **kwargs)
        self.__init_value = None

        # parse/check for integer declarations
        if (self.inner is not None and
                len(self.inner) == 1 and
                type(self.inner[0]) is IntegerLiteral):
            self.__init_value = self.inner[0].value

    def get_width(self):
        """
        returns the width if the variable in bytes
        """
        return type2width(self.get_type())

    def is_integral(self):
        """
        returns if a variable is integral: int, long int, ....
        """
        try:
            type2width(self.get_type())
            return True
        except:
            return False

    def get_init_value(self):
        """
        """
        return self.__init_value

    def is_const(self):
        """
        returns true if variable is const
        """
        raise NotImplementedError


class ParmVarDecl(Node):
    def __init__(self, id: str, kind: str, *args, **kwargs):
        """
        """
        super().__init__(id, kind, *args, **kwargs)

    def get_width(self):
        """
        returns the width if the variable in bytes
        """
        t = self.get_type()
        assert t
        return type2width(t)

    def is_integral(self):
        """
        returns if a variable is integral: int, long int, ....
        """
        try:
            type2width(self.get_type())
            return True
        except:
            return False

    def get_init_value(self):
        """
        this only makes sense for c++.
        """
        return None

    def is_const(self):
        """
        returns true if variable is const
        """
        raise NotImplementedError

    def usages(self):
        """
        This is rather cool: returns the list of usages of this variable.
        This is just the list of Nodes where this is in the `inner` field
        as a `DeclRef`
        """
        raise NotImplementedError


class TypedefDecl(Node):
    pass


class RecordType(Node):
    pass


class PointerType(Node):
    pass


class ConstantArrayType(Node):
    pass


class ReturnStmt(Node):
    pass


class ImplicitCaseExpr(Node):
    pass


class ImplicitCastExpr(Node):
    pass


class DeclRefExpr(Node):
    def __init__(self, id: str, kind: str, *args, **kwargs):
        """
        exports this additional fields:
        - referenced_decl
        """
        super().__init__(id, kind, *args, **kwargs)
        # print(kwargs)

    def value_category(self):
        """ something like `lvalue` """
        return self.valueCategory

    def get_reference_id(self):
        return self.__dict__["referencedDecl"]["id"]

class BinaryOperator(Node):
    pass


class UnaryOperator(Node):
    pass


class ArraySubscriptExpr(Node):
    pass


class CompoundAssignOperator(Node):
    pass


class ForStmt(Node):
    def __init__(self, id: str, kind: str, *args, **kwargs):
        """
        exports this additional fields:
        - var_decls
        - func_calls
        - break_stmt

        additional information tracked
        - lower_limit
        - upper_limit
        - step_size
        - body
        """
        super().__init__(id, kind, *args, **kwargs)
        self.__var_decls = []
        self.__func_calls = []
        self.__break_stmts = []

        self.__is_basic_loop = False
        self.__lower_limit = None
        self.__upper_limit = None
        self.__step_size = None
        self.__body = None

        self.__body = self.reparse_single(self.__body, CompoundStmt)
        if self.__body is not None:
            self.__var_decl = self.__body.reparse(self.__var_decls, DeclStmt)
            self.__func_calls = self.__body.reparse(self.__func_calls, CallExpr)
            self.__break_stmts = self.__body.reparse(self.__break_stmts, BreakStmt, recursive=False)

        # TODO currently we only support the trivial for loop
        # TODO account for loops with mutliple counter variables
        if len(self.inner) == 4:
            self.__is_basic_loop = True
            self.__lower_limit = self.inner[0]
            self.__upper_limit = self.inner[1]
            self.__step_size = self.inner[2]

        # append the decl to the global declaration
        for_loop_decls.append(self)

    def is_basic_loop(self):
        """
        returns true if the loop is of the simplest form:
            for(int i = 0; i < 32; i++){ ... }

        """
        return self.__is_basic_loop

    def get_var_decls(self):
        return self.__var_decls

    def get_func_calls(self):
        return self.__func_calls

    def get_break_stmts(self):
        return self.__break_stmts

    def get_lower_limit(self):
        return self.__lower_limit

    def get_upper_limit(self):
        return self.__lower_limit

    def get_step_size(self):
        return self.__step_size

    def get_body(self):
        return self.__body

    def get_variables(self):
        return self.__var_decls
    
    def print(self):
        print(self.__dict__)


class WhileStmt(Node):
    def __init__(self, id: str, kind: str, *args, **kwargs):
        """
        exports this additional fields:
        - var_decls
        - func_calls
        - lower_limit
        - upper_limit
        - step_size
        - body
        """
        super().__init__(id, kind, *args, **kwargs)
        self.__var_decls = []
        self.__func_calls = []
        self.__break_stmts = []
        self.__body = None

        self.__body = self.reparse_single(self.__body, CompoundStmt)
        if self.__body is not None:
            self.__var_decl = self.__body.reparse(self.__var_decls, DeclStmt)
            self.__func_calls = self.__body.reparse(self.__func_calls, CallExpr)
            self.__break_stmts = self.__body.reparse(self.__break_stmts, BreakStmt, recursive=False)

        while_loop_decls.append(self)

    def get_variables(self):
        return self.__var_decls

    def print(self):
        print(self.__dict__)


class DoStmt(Node):
    def __init__(self, id: str, kind: str, *args, **kwargs):
        """
        exports this additional fields:
        - var_decls
        - func_calls
        - lower_limit
        - upper_limit
        - step_size
        - body
        """
        super().__init__(id, kind, *args, **kwargs)
        self.__var_decls = []
        self.__func_calls = []
        self.__break_stmts = []
        self.__body = None

        self.reparse_single(self.__body, CompoundStmt)
        if self.__body is not None:
            self.__var_decl = self.__body.reparse(self.__var_decls, DeclStmt)
            self.__func_calls = self.__body.reparse(self.__func_calls, CallExpr)
            self.__break_stmts = self.__body.reparse(self.__break_stmts, BreakStmt, recursive=False)

        while_loop_decls.append(self)

    def get_variables(self):
        return self.__var_decls

    def print(self):
        print(self.__dict__)


class BreakStmt(Node):
    pass


class IfStmt(Node):
    pass


class ElaboratedType(Node):
    pass


class TypedefType(Node):
    pass


class RecordDecl(Node):
    pass


class FieldDecl(Node):
    pass


class FunctionProtoType(Node):
    pass


class QualType(Node):
    pass


class NoThrowAttr(Node):
    pass


class NonNullAttr(Node):
    pass


class RestrictAttr(Node):
    pass


class WarnUnusedResultAttr(Node):
    pass


class BuiltinAttr(Node):
    pass


class FormatAttr(Node):
    pass


class AsmLabelAttr(Node):
    pass


class ColdAttr(Node):
    pass


class CallExpr(Node):
    def __init__(self, id: str, kind: str, *args, **kwargs):
        """
        exports this additional fields:
        - arguments
        """
        super().__init__(id, kind, *args, **kwargs)
        self.__arguments = []
        self.reparse(self.__arguments, DeclRefExpr)


class GNUInlineAttr(Node):
    pass


class ParenExpr(Node):
    pass


class ConditionalOperator(Node):
    pass


class MemberExpr(Node):
    pass


class CStyleCastExpr(Node):
    pass


class ConstAttr(Node):
    pass


class AlwaysInlineAttr(Node):
    pass


class ArtificialAttr(Node):
    pass


class UnaryExprOrTypeTraitExpr(Node):
    pass


# C++ stuff
class CXXNullPtrLiteralExpr(Node):
    pass


class clang_parser:
    """
    parser build around the command:
        clang -fsyntax-only -Xclang -ast-dump=json file.c
    """
    BINARY = "clang"
    COMMAND = ["-fsyntax-only", "-Xclang", "-ast-dump=json",
               "-fno-color-diagnostics", "-Wno-visibility", "-Wno-everything"]
    COMMAND_FUNCTION_FILER = ["-Xclang", "-ast-dump-filter="]

    def __init__(self, file: Union[str, Path], functions: list[str] = []):
        """
        :param functions: if given only parse the given functions into an AST
        """
        self.__file = file if type(file) is str else file.absolute()
        self.__outfile = tempfile.NamedTemporaryFile(suffix=".json")
        self.__functions = functions # TODO not implemented

        # reset global variables
        global functions_decls, compound_decls, for_loop_decls, while_loop_decls, do_loop_decls
        functions_decls = []
        compound_decls = []
        for_loop_decls = []
        while_loop_decls = []
        do_loop_decls = []

        self.__function_decls = []
        self.__compound_decls = []
        self.__for_loop_decls = []
        self.__while_loop_decls = []
        self.__do_loop_decls = []

        if not os.path.isfile(self.__file):
            logging.error("file does not exists")
            return

    def get_function_decls(self, i: int = None):
        if i is not None:
            if i > len(self.__function_decls):
                print("OOB")
                return None

            return self.__function_decls[i]
        return self.__function_decls

    def __available__(self):
        """
        :return: true if `clang` is available else false
        """
        cmd = [clang_parser.BINARY] + ["--version"]
        p = Popen(cmd, stdin=PIPE, stdout=self.__outfile, stderr=STDOUT)
        p.wait()
        assert p.stdout

        if p.returncode != 0 and p.returncode is not None:
            logging.error("couldn't execute: %s %s", " ".join(cmd), p.stdout.read())
            return False, ""

        data = p.stdout.readlines()
        data = [str(a).replace("b'", "")
                .replace("\\n'", "")
                .lstrip() for a in data]

        assert len(data) > 1
        data = data[0]
        ver = re.findall(r'\d.\d.\n', data)
        assert len(ver) == 1
        return True, ver[0]

    def execute(self):
        cmd = [clang_parser.BINARY] + clang_parser.COMMAND
        for f in self.__functions:
            cmd += clang_parser.COMMAND_FUNCTION_FILER + [f]

        cmd += [self.__file]
        logging.info(cmd)
        p = Popen(cmd, stdin=PIPE, stdout=self.__outfile, stderr=STDOUT)
        p.wait()

        if p.returncode != 0 and p.returncode is not None:
            logging.error("couldn't execute: %s", " ".join(cmd))
            return None

        self.__outfile.flush()
        self.__outfile.seek(0)
        data = self.__outfile.read()
        data = json.loads(data)
        data = Node(**data)

        # copy global variables into locaL variables
        global functions_decls, compound_decls, for_loop_decls, while_loop_decls, do_loop_decls
        self.__function_decls = copy.copy(functions_decls)
        self.__compound_decls = copy.copy(compound_decls)
        self.__for_loop_decls = copy.copy(for_loop_decls)
        self.__while_loop_decls = copy.copy(while_loop_decls)
        self.__do_loop_decls = copy.copy(do_loop_decls)
        return data

    def insert(self, line: str, pos: int):
        """
        insert the code-line `line` at line `pos`
        """
        NotImplementedError  # TODO

    def replace(self, line: str, pos: int):
        """
        replaces the code-line `pos` with `line`
        """
        NotImplementedError  # TODO
