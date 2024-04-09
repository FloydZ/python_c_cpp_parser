
    def parse(self):
        """
        this function is called to generate a `AST` from the given C code
        to extract the callable functions and its arguments

        :return 0 on success
                1 on any error
        """
        # A simple visitor for FuncDef nodes that prints the names and
        # locations of function definitions.
        class FuncDefVisitor(c_ast.NodeVisitor):
            def visit_FuncDef(self, node):
                names = [n.name for n in node.decl.type.args.params]
                types = [n.type.type.type.names for n in node.decl.type.args.params]
                const = [n.type.type.quals for n in node.decl.type.args.params]
                funcs[node.decl.name] = {
                        "nr_args": len(node.decl.type.args.params),
                        "names:": names,
                        "types": types,
                        "const": const
                    }

        # TODO this looks wrong
        f = tempfile.NamedTemporaryFile(delete=False)
        name = f.name
        f.write(self.c_code.encode())
        f.flush()
        f.close()

        funcs = {}
        ast = parse_file(name, use_cpp=True)
        v = FuncDefVisitor()
        v.visit(ast)
        
        if self.target == "" and len(list(funcs.keys())) > 1:
            print("Multiple Symbols found, cannot choose the correct one")
            return 1

        # set the target
        if self.target == "" and len(list(funcs.keys())) == 1:
            self.target = list(funcs.keys())[0]
        
        # well this is going to be an problem source
        if funcs[self.target]["nr_args"] == 0:
            self.arg_num_in = 0
            self.arg_num_out = 0
        elif funcs[self.target]["nr_args"] == 1:
            self.arg_num_in = 1
            self.arg_num_out = 0
        elif funcs[self.target]["nr_args"] > 1:
            self.arg_num_in = funcs[self.target]["nr_args"] - 1
            self.arg_num_out = 1

        if DEBUG:
            print(funcs)

        return 0
