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


functions_decls = []
compound_decls = []

def str_to_class(classname: str):
    return getattr(sys.modules[__name__], classname)


def type2width(t: str) -> Union[int, None]:
    # pointer
    if "*" in t:
        return 8

    if t == "int":
        return 4
    elif t == "long int":
        return 8
    else:
        print(t, "not implemented")
        return -1

class Range:
    def __init__(self, begin_offset: int, begin_col: int, begin_tokLen: int, 
                 end_offset: int, end_col: int, end_tokLen: int):
        self.begin_offset, self.begin_col, self.begin_tokLen = begin_offset, begin_col,begin_tokLen
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
                pField = "_" + inn["kind"]
                n = C(**inn)

                # this is kind of weird, I dont know whats happening, but internal fields from subclasses
                # are now called `_FuncDecl__arguments`. The following code renames them back to their original name.
                #for bla in list(n.__dict__.keys()):
                #    if pField in bla:
                #        bla2 = bla.replace(pField, "")
                #        n.__dict__[bla2] = n.__dict__.pop(bla)

                self.inner.append(n)
        else:
            self.inner = None

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
            t = "\t"*depth
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
        """
        try:
            return self.value
        except:
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
        for i in self.inner:
            if type(i) is ParmVarDecl:
                self.__arguments.append(i)

        # find the function body:
        for i in self.inner:
            if type(i) is CompoundStmt:
                self.__body = i

        assert self.__body
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
        """
        super().__init__(id, kind, *args, **kwargs)
        self.__var_decls = []
        self.__isempty = self.inner is None

        # empty compound stmt = empty func
        if self.inner is not None:
            for i in self.inner:
                if type(i) is DeclStmt:
                    if len(i.inner) == 1 and type(i.inner[0]) is VarDecl:
                        self.__var_decls.append(i.inner[0])

        compound_decls.append(self)

    def get_variables(self):
        return self.__var_decls


class DeclStmt(Node):
    pass


class VarDecl(Node):
    def __init__(self, id: str, kind: str, *args, **kwargs):
        """
        """
        super().__init__(id, kind, *args, **kwargs)
        print(kwargs)

        self.__init_value = None

        # parse/check for integer declarations
        if len(self.inner) == 1 and type(self.inner[0]) == IntegerLiteral:
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
    pass




class clang_parser:
    """
    parser build around the command:
        clang -fsyntax-only -Xclang -ast-dump=json file.c
    """
    BINARY="clang"
    COMMAND = ["-fsyntax-only", "-Xclang", "-ast-dump=json",
               "-fno-color-diagnostics", "-Wno-visibility", "-Wno-everything"]
    COMMAND_FUNCTION_FILER = ["-Xclang", "-ast-dump-filter="]

    def __init__(self, file: Union[str, Path], functions:list[str]=[]):
        """
        :param functions: if fiven only parse the given functions into an AST
        """
        self.__file = file if type(file) is str else file.absolute()
        self.__outfile = tempfile.NamedTemporaryFile(suffix=".json")
        self.__functions = functions
        if not os.path.isfile(self.__file):
            logging.error("file does not exists")
            return

    def execute(self):
        cmd = [clang_parser.BINARY] + clang_parser.COMMAND
        for f in self.__functions:
            cmd += clang_parser.COMMAND_FUNCTION_FILER + [f]
        
        cmd += [self.__file]
        print(cmd)

        p = Popen(cmd, stdin=PIPE, stdout=self.__outfile, stderr=STDOUT)
        p.wait()

        if p.returncode != 0 and p.returncode is not None:
            logging.error("couldn't execute:")
            return None
        self.__outfile.flush()
        self.__outfile.seek(0)
        data = self.__outfile.read()
        data = json.loads(data)
        data = Node(**data)
        return data


c = clang_parser("../test/test2.c")
d = c.execute()
print(d)

print("\n".join([str(a.__dict__) for a in functions_decls]))
print("\n".join([str(a.get_arguments()) for a in functions_decls]))
print("\n".join([str(a.get_location()) for a in functions_decls]))
print("\n".join([str(a.get_file()) for a in functions_decls]))

d = functions_decls[0]

print()
print("function arguments:")
print(",".join(str(a.get_type()) for a in d.get_arguments()))
print(",".join(str(a.get_width()) for a in d.get_arguments()))

d = compound_decls[0]
print()
print("compound statements")
print(d.get_variables())
print(",".join(str(a) for a in d.get_variables()))
print(",".join(str(a.get_init_value()) for a in d.get_variables()))
