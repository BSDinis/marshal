#!/usr/bin/env python3
""" Marshal C header file visitor """

import sys
import scanner
import ast

def generate(ast, to_file):
    includes = str();
    defines = str();
    types = list();
    structs = list();
    typedefs = list();
    funcs = list();

    if to_file:
        if ast['includes']:
            includes += '\n'
            for inc in ast['includes']:
                includes += '#include {f}\n'.format(f = inc)

        if ast['defines']:
            defines += '\n'
            for d in ast['defines']:
               defines += '#define {o} {n}\n'.format(o = d[0], n = d[1])

    if ast['structs']:
        for struct in ast['structs']:
            code = '// {t}\n'.format(t = struct['typedef'])
            code += 'typedef struct ' + struct['struct'] + '\n{\n';
            for member in struct['members']:
                code += '  ' + member[0] + ' ' + member[1] + ';\n';
            code += '} ' + struct['typedef'] + ';';
            structs.append(code);

    if ast['typedefs']:
        typedefs.append('// typedefs')
        for typedef in ast['typedefs']:
            typedefs.append('typedef {o} {n};'.format(n = typedef['new'], o = typedef['old']))

    if ast['funcs']:
        typedefs.append('// function prototypes')

    code = includes + defines;
    for frag in [types, structs, typedefs, funcs]:
        if frag:
            for el in frag:
                code += '\n' + el + '\n'

    return code;

if __name__ == '__main__':
    ast = ast.make_ast(scanner.scan(sys.stdin));
    print(generate(ast), end='');
    sys.exit(0);
