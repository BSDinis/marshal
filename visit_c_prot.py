#!/usr/bin/env python3
""" Marshal C prototype visitor """

import sys
import scanner
import ast

def gen_func(f):
    return ['']

def gen_typename(typename, ref):
    typename_u = typename.replace(' ', '_')
    code = str()
    variable = str()
    if ref: variable = 'const {t} *'.format(t = typename);
    else:   variable = '{t}'.format(t = typename);
    code  = 'static int marshall_{t_}(uint8_t ** ptr, ssize_t * rem, {v} val);\n'.format(t_ = typename_u, v=variable)
    code += 'static int unmarshall_{t_}(uint8_t ** ptr, ssize_t * rem, {t} * val);'.format(t_ = typename_u, t=typename)
    return code

def gen_type(t):
    return gen_typename(t, False);

def gen_struct(s):
    return gen_typename(s['typedef'], True)


def generate(ast):
    types = list();
    structs = list();
    typedefs = list();
    funcs = list();

    if ast['types']:
        for typ in ast['types']:
            types.append('// {t}\n'.format(t = typ) + gen_type(typ))

    if ast['structs']:
        for struct in ast['structs']:
            structs.append('// {t}\n'.format(t = struct['typedef']) + gen_struct(struct))

    if ast['funcs']:
        typedefs.append('// function prototypes')
        for func in ast['funcs']:
            funcs.append(gen_func(func))

    code = str()
    for frag in [types, structs, typedefs, funcs]:
        if frag:
            for el in frag:
                code += '\n' + el + '\n'

    return code;

if __name__ == '__main__':
    ast = ast.make_ast(scanner.scan(sys.stdin));
    print(generate(ast), end='');
    sys.exit(0);
