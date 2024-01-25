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


def str_to_class(classname: str):
    return getattr(sys.modules[__name__], classname)


class Range:
    def __init__(self, begin_offset: int, begin_col: int, begin_tokLen: int, 
                 end_offset: int, end_col: int, end_tokLen: int):
        self.begin_offset, self.begin_col, self.begin_tokLen = begin_offset, begin_col,begin_tokLen
        self.end_offset, self.end_col, self.end_tokLen = end_offset, end_col, end_tokLen


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
    pass

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
        super().__init__(id, kind, *args, **kwargs)
        self.__arguments = []
        for i in self.inner:
            if type(i) is ParmVarDecl:
                self.__arguments.append(i)


class CompoundStmt(Node):
    pass

class DeclStmt(Node):
    pass

class VarDecl(Node):
    pass

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
        #data = json.loads(data, object_hook=lambda d: SimpleNamespace(**d))
        data = json.loads(data)
        data = Node(**data)
        return data


c = clang_parser("../test/test2.c")
print(c.execute())
