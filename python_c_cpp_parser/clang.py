#!/usr/bin/env python3

from subprocess import Popen, PIPE, STDOUT
from typing import Union
from pathlib import Path
from types import SimpleNamespace
import logging
import sys
import os
import json
import tempfile
import re

# TODO remove
functions_decls = []
compound_decls = []


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
                self.inner.append(n)
        else:
            self.inner = None

    def reparse(self, out, t, recursive=True):
        """ reparse the current `inner` nodes for type `t` and appends them
        to out"""
        if self.inner is not None:
            for tmp in self.inner:
                if type(tmp) is t:
                    out.append(t)

                if recursive:
                    tmp.reparse(out, t, recursive)

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

    def __str__(self, depth=0):
        ret = str(self.id) + " " + str(self.__class__) + "\n"
        if self.inner:
            depth += 1
            t = "\t" * depth
            for a in self.inner:
                ret += t + a.__str__(depth)
        return ret


class TranslationUnitDecl(Node):
    pass


class BuiltinType(Node):
    pass


class IntegerLiteral(Node):
    pass


class ParmVarDecl(Node):
    def __init__(self, id: str, kind: str, *args, **kwargs):
        """
        exports this additional fields:
        - var_decls
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
        this only makes sence for c++.
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

        # TODO: there exist functions without an compound statment?
        # assert self.__body
        functions_decls.append(self)

    def get_arguments(self):
        return self.__arguments

    def get_body(self):
        return self.__arguments


class CompoundStmt(Node):
    def __init__(self, id: str, kind: str, *args, **kwargs):
        """
        exports this additional fields:
        - var_decls
        - for_loops
        - do_loops
        - while_loops
        """
        super().__init__(id, kind, *args, **kwargs)
        self.__var_decls = []
        self.__for_loops = []
        self.__while_loops = []
        self.__do_loops = []
        self.__isempty = self.inner is None

        # empty compound stmt = empty func
        if self.inner is not None:
            for i in self.inner:
                if type(i) is DeclStmt:
                    if i.inner is not None and len(i.inner) == 1 and \
                            type(i.inner[0]) is VarDecl:
                        self.__var_decls.append(i.inner[0])

        self.reparse(self.__for_loops, ForStmt)
        self.reparse(self.__while_loops, WhileStmt)
        self.reparse(self.__do_loops, DoStmt)
        compound_decls.append(self)

    def get_variables(self):
        return self.__var_decls

    def get_for_loops(self):
        return self.__for_loops

    def get_do_loops(self):
        return self.__do_loops

    def get_while_loops(self):
        return self.__while_loops


class DeclStmt(Node):
    pass


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


class ReturnStmt(Node):
    pass


class ImplicitCaseExpr(Node):
    pass


class ImplicitCastExpr(Node):
    pass


class DeclRefExpr(Node):
    pass


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
        - lower_limit
        - upper_limit
        - step_size
        - body
        """
        super().__init__(id, kind, *args, **kwargs)
        print(kwargs)
        # TODO parse this stuff
        self.__var_decls = []
        self.__func_calls = []
        self.__lower_limit = None
        self.__upper_limit = None
        self.__step_size = None
        self.__body = None


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
        # TODO parse this stuff
        self.__var_decls = []
        self.__func_calls = []
        self.__body = None


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
        # TODO parse this stuff
        self.__var_decls = []
        self.__func_calls = []
        self.__body = None


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
    pass


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
        :param functions: if fiven only parse the given functions into an AST
        """
        self.__file = file if type(file) is str else file.absolute()
        self.__outfile = tempfile.NamedTemporaryFile(suffix=".json")
        self.__functions = functions
        if not os.path.isfile(self.__file):
            logging.error("file does not exists")
            return

    def __available__(self):
        """
        :return true if `clang` is available else false
        """
        cmd = [clang_parser.BINARY] + ["--version"]
        p = Popen(cmd, stdin=PIPE, stdout=self.__outfile, stderr=STDOUT)
        p.wait()
        assert p.stdout

        if p.returncode != 0 and p.returncode is not None:
            logging.error("couldn't execute: %s %s", " ".join(cmd), p.stdout.read())
            return None

        data = p.stdout.readlines()
        data = [str(a).replace("b'", "")
                .replace("\\n'", "")
                .lstrip() for a in data]

        assert len(data) > 1
        data = data[0]
        ver = re.findall(r'\d.\d.\n', data)
        assert len(ver) == 1
        return ver[0]

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


# TODO
# for each function / for loop/ while loop/ do loop /compount statment / call / if else/
#  track the number of each of those + VarDecl

c = clang_parser("../test/test2.c")
d = c.execute()
# print(d)

print("\n".join([str(a.__dict__) for a in functions_decls]))
print("\n".join([str(a.get_arguments()) for a in functions_decls]))
print("\n".join([str(a.get_location()) for a in functions_decls]))
print("\n".join([str(a.get_file()) for a in functions_decls]))

d = functions_decls[0]

print()
print("function arguments:")
print(",".join(str(a.get_type()) for a in d.get_arguments()))
print(",".join(str(a.get_width()) for a in d.get_arguments()))

for d in compound_decls:
    print()
    print("compound statements")
    print(d.get_variables())
    print(",".join(str(a) for a in d.get_variables()))
    print(",".join(str(a.get_init_value()) for a in d.get_variables()))
    print(d.get_for_loops())
