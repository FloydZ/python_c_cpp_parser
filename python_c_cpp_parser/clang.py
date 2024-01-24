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
    def __init__(self, 
                 id="", 
                 kind="", 
                 loc=None, 
                 range={},
                 isImplicit=None, 
                 name="",
                 valueCategory="",
                 referenceDecl={},
                 inner=[],
                 *args,
                 **kwargs):
        self.id = id
        self.kind = kind
        assert kind

        self.loc = None
        self.range = range
        self.isImplicit = isImplicit
        self.name = name
        self.valueCategory = valueCategory
        self.type = kwargs["type"] if "type" in kwargs else None
        self.inner = []

        if type(inner) is list and len(inner) > 0:
            for inn in inner:
                n = Node(**inn)
                n.__class__ = str_to_class(n.kind)
                self.inner.append(n)
        else:
            self.inner = None

    def __str__(self, depth=0):
        ret = str(self.id) + " " + str(self.__class__) +"\n"
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

class TypedefDecl(Node):
    pass

class RecordType(Node):
    pass

class PointerType(Node):
    pass

class ConstantArrayType(Node):
    pass

class FunctionDecl(Node):
    pass

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




test_str = """
{
  "id": "0x1450cc8",
  "kind": "TranslationUnitDecl",
  "loc": {},
  "range": {
    "begin": {},
    "end": {}
  },
  "inner": [
    {
      "id": "0x14514f0",
      "kind": "TypedefDecl",
      "loc": {},
      "range": {
        "begin": {},
        "end": {}
      },
      "isImplicit": true,
      "name": "__int128_t",
      "type": {
        "qualType": "__int128"
      },
      "inner": [
        {
          "id": "0x1451290",
          "kind": "BuiltinType",
          "type": {
            "qualType": "__int128"
          }
        }
      ]
    },
    {
      "id": "0x1451560",
      "kind": "TypedefDecl",
      "loc": {},
      "range": {
        "begin": {},
        "end": {}
      },
      "isImplicit": true,
      "name": "__uint128_t",
      "type": {
        "qualType": "unsigned __int128"
      },
      "inner": [
        {
          "id": "0x14512b0",
          "kind": "BuiltinType",
          "type": {
            "qualType": "unsigned __int128"
          }
        }
      ]
    },
    {
      "id": "0x1451868",
      "kind": "TypedefDecl",
      "loc": {},
      "range": {
        "begin": {},
        "end": {}
      },
      "isImplicit": true,
      "name": "__NSConstantString",
      "type": {
        "qualType": "struct __NSConstantString_tag"
      },
      "inner": [
        {
          "id": "0x1451640",
          "kind": "RecordType",
          "type": {
            "qualType": "struct __NSConstantString_tag"
          },
          "decl": {
            "id": "0x14515b8",
            "kind": "RecordDecl",
            "name": "__NSConstantString_tag"
          }
        }
      ]
    },
    {
      "id": "0x1451900",
      "kind": "TypedefDecl",
      "loc": {},
      "range": {
        "begin": {},
        "end": {}
      },
      "isImplicit": true,
      "name": "__builtin_ms_va_list",
      "type": {
        "qualType": "char *"
      },
      "inner": [
        {
          "id": "0x14518c0",
          "kind": "PointerType",
          "type": {
            "qualType": "char *"
          },
          "inner": [
            {
              "id": "0x1450d70",
              "kind": "BuiltinType",
              "type": {
                "qualType": "char"
              }
            }
          ]
        }
      ]
    },
    {
      "id": "0x1451bf8",
      "kind": "TypedefDecl",
      "loc": {},
      "range": {
        "begin": {},
        "end": {}
      },
      "isImplicit": true,
      "name": "__builtin_va_list",
      "type": {
        "qualType": "struct __va_list_tag[1]"
      },
      "inner": [
        {
          "id": "0x1451ba0",
          "kind": "ConstantArrayType",
          "type": {
            "qualType": "struct __va_list_tag[1]"
          },
          "size": 1,
          "inner": [
            {
              "id": "0x14519e0",
              "kind": "RecordType",
              "type": {
                "qualType": "struct __va_list_tag"
              },
              "decl": {
                "id": "0x1451958",
                "kind": "RecordDecl",
                "name": "__va_list_tag"
              }
            }
          ]
        }
      ]
    },
    {
      "id": "0x14acde0",
      "kind": "FunctionDecl",
      "loc": {
        "offset": 4,
        "file": "../test/test.c",
        "line": 1,
        "col": 5,
        "tokLen": 4
      },
      "range": {
        "begin": {
          "offset": 0,
          "col": 1,
          "tokLen": 3
        },
        "end": {
          "offset": 42,
          "line": 4,
          "col": 1,
          "tokLen": 1
        }
      },
      "name": "main",
      "mangledName": "main",
      "type": {
        "qualType": "int ()"
      },
      "inner": [
        {
          "id": "0x14acfd0",
          "kind": "CompoundStmt",
          "range": {
            "begin": {
              "offset": 11,
              "line": 1,
              "col": 12,
              "tokLen": 1
            },
            "end": {
              "offset": 42,
              "line": 4,
              "col": 1,
              "tokLen": 1
            }
          },
          "inner": [
            {
              "id": "0x14acf70",
              "kind": "DeclStmt",
              "range": {
                "begin": {
                  "offset": 14,
                  "line": 2,
                  "col": 2,
                  "tokLen": 3
                },
                "end": {
                  "offset": 26,
                  "col": 14,
                  "tokLen": 1
                }
              },
              "inner": [
                {
                  "id": "0x14acee8",
                  "kind": "VarDecl",
                  "loc": {
                    "offset": 18,
                    "col": 6,
                    "tokLen": 4
                  },
                  "range": {
                    "begin": {
                      "offset": 14,
                      "col": 2,
                      "tokLen": 3
                    },
                    "end": {
                      "offset": 25,
                      "col": 13,
                      "tokLen": 1
                    }
                  },
                  "isUsed": true,
                  "name": "sum1",
                  "type": {
                    "qualType": "int"
                  },
                  "init": "c",
                  "inner": [
                    {
                      "id": "0x14acf50",
                      "kind": "IntegerLiteral",
                      "range": {
                        "begin": {
                          "offset": 25,
                          "col": 13,
                          "tokLen": 1
                        },
                        "end": {
                          "offset": 25,
                          "col": 13,
                          "tokLen": 1
                        }
                      },
                      "type": {
                        "qualType": "int"
                      },
                      "valueCategory": "prvalue",
                      "value": "0"
                    }
                  ]
                }
              ]
            },
            {
              "id": "0x14acfc0",
              "kind": "ReturnStmt",
              "range": {
                "begin": {
                  "offset": 29,
                  "line": 3,
                  "col": 2,
                  "tokLen": 6
                },
                "end": {
                  "offset": 36,
                  "col": 9,
                  "tokLen": 4
                }
              },
              "inner": [
                {
                  "id": "0x14acfa8",
                  "kind": "ImplicitCastExpr",
                  "range": {
                    "begin": {
                      "offset": 36,
                      "col": 9,
                      "tokLen": 4
                    },
                    "end": {
                      "offset": 36,
                      "col": 9,
                      "tokLen": 4
                    }
                  },
                  "type": {
                    "qualType": "int"
                  },
                  "valueCategory": "prvalue",
                  "castKind": "LValueToRValue",
                  "inner": [
                    {
                      "id": "0x14acf88",
                      "kind": "DeclRefExpr",
                      "range": {
                        "begin": {
                          "offset": 36,
                          "col": 9,
                          "tokLen": 4
                        },
                        "end": {
                          "offset": 36,
                          "col": 9,
                          "tokLen": 4
                        }
                      },
                      "type": {
                        "qualType": "int"
                      },
                      "valueCategory": "lvalue",
                      "referencedDecl": {
                        "id": "0x14acee8",
                        "kind": "VarDecl",
                        "name": "sum1",
                        "type": {
                          "qualType": "int"
                        }
                      }
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}"""

data = json.loads(test_str)
data = Node(**data)
print(data)
exit(1)


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

c = clang_parser("../test/test.c")
print(c.execute())
