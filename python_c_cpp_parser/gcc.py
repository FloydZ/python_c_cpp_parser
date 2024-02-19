#!/usr/bin/env python3
from subprocess import Popen, PIPE, STDOUT
from typing import Union
from pathlib import Path
from types import SimpleNamespace
import logging
import sys
import os
import json
import re
import tempfile

from python_c_cpp_parser.clang import *


def is_empty_str(s: str):
    if s == "" or len(s) == 0:
        return True 
    return False


def split_line(line: str):
    splits = line.split(" ")
    # first remove all the spaces
    options = []
    for i, s in enumerate(splits):
        if not is_empty_str(s) and s != ":":
            if s == "op":
                s += splits[i + 1]
                splits.pop(i+1)
            options.append(s)

    return options


class ParsingNode:
    """
    just a helper class for parsing the gcc output
    """
    def __init__(self, *args, **kwargs):
        self.__dict__.update(**kwargs)

    @staticmethod
    def from_line(line: str):
        """
        creates from a string like this:
        @1      bind_expr        type: @2       vars: @3       body: @4

        a new node
        """
        options = split_line(line)
        assert len(options) >= 2
        assert options[0][0] == "@"
        id = options[0][1:]
        kind = options[1]
        d = {"id": id, "kind": kind}

        assert len(options) % 2 == 0
        for i in range(2, len(options), 2):
            opt = options[i]
            val = options[i + 1]
            d[opt] = val

        return ParsingNode(**d)

    def __str__(self):
        return str(self.__dict__)


class gcc_parser:
    """
    wrapper around the command: `gcc -fdump-tree-original-raw=outfile.data input.c`
    """

    BINARY = ["gcc"]
    COMMANDS = ["-c", "-o", "/tmp/kek.o"]
    COMMAND = "-fdump-tree-original-raw="

    def __init__(self, file: Union[str, Path]):
        self.__file = file if type(file) is str else file.absolute()
        self.__outfile = tempfile.NamedTemporaryFile(suffix=".data")

    def execute(self):
        cmd = gcc_parser.BINARY + gcc_parser.COMMANDS + [gcc_parser.COMMAND+str(self.__outfile.name)]
        cmd += [self.__file]
        print(cmd)

        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        p.wait()

        if p.returncode != 0 and p.returncode is not None:
            logging.error("couldn't execute:")
            print(p.stdout.read())
            return None

        self.__outfile.flush()
        self.__outfile.seek(0)
        lines = self.__outfile.readlines()
        lines = [
            str(a).replace("b'", "").replace("\\n'", "").lstrip()
            for a in lines
        ]
        return self.parse(lines)

    def parse(self, lines: list[str]):
        """
        parses something like:
        ...
        @1      bind_expr        type: @2       vars: @3       body: @4      
        @2      void_type        name: @5       algn: 8       
        @3      var_decl         name: @6       type: @7       scpe: @8      
                                 srcp: test2.c:3               init: @9      
                                 size: @10      algn: 32       used: 1   
        ...

        :return a dictonary which keys are the node ids and values the nodes are.
        """
        # first find the entry
        i = 0
        while is_empty_str(lines[i]) or lines[i].startswith(";"):
            i = i + 1

        # now start the actual parsing
        lines = lines[i:]
        i = 0
        cNode = None
        nodes = {}
        while i < len(lines):
            # if the line starts with `@` create a new node and pus the old one
            if lines[i].startswith("@"):
                if cNode is not None:
                    assert cNode.id
                    nodes[cNode.id] = (cNode)
                
                cNode = ParsingNode.from_line(lines[i])
                i = i + 1
                continue

            # if not a new node update the current one:
            assert cNode
            options = split_line(lines[i])
            assert len(options) % 2 == 0
            for j in range(0, len(options), 2):
                opt = options[j]
                val = options[j + 1]
                cNode.__dict__[opt] = val

            i = i + 1

        return nodes


c = gcc_parser("../test/c/test2.c")
nodes = c.execute()
for n in nodes.values():
    print(n)
