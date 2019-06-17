#!/usr/bin/env python3
""" Marshal C header file visitor """

import sys
import scanner
import ast

def generate(ast):
    types = list();
    structs = list();
    typedefs = list();
    funcs = list();

    if ast['structs']:
        structs.append('// struct definitions')
        for struct in ast['structs']:
            code = 'typedef struct ' + struct['struct'] + '\n{\n';
            for member in struct['members']:
                code += '  ' + member[0] + ' ' + member[1] + ';\n';
            code += '} ' + struct['typedef'] + ';';
            structs.append(code);

    if ast['typedefs']:
        typedefs.append('// typedefs')
        for typedef in ast['typedefs']:
            typedefs.append('typedef {n} {o};'.format(n = typedef['new'], o = typedef['old']))

    if ast['funcs']:
        typedefs.append('// function prototypes')

    code = str()
    for frag in [types, structs, typedefs, funcs]:
        if frag:
            for el in frag:
                code += el + '\n\n'
            code += '\n'

    return code;

if __name__ == '__main__':
    ast = ast.make_ast(scanner.scan(sys.stdin));
    print(generate(ast), end='');
    sys.exit(0);
