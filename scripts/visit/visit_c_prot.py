""" Marshal C prototype visitor """

import sys
import lex.scanner
import syntax.ast
from visit.helpers import *
from utils.typehelpers import *
from visit.type_gen import *;


def gen_typename(typename, ref, real_t):
    code = str()
    variable = str()
    if ref: variable = '{t} *'.format(t = typename);
    else:   variable = '{t}'.format(t = typename);
    code  = 'static int marshal_{t_}(uint8_t ** const ptr, ssize_t * const rem, const {v});\n'.format(t_ = linearize_type(typename), v=variable)
    if '[' in real_t:
        code += 'static int unmarshal_{t_}(uint8_t const ** const ptr, ssize_t * const rem, {t});'.format(t_ = linearize_type(typename), t=gen_type_decl([typename, 'val']))
    else:
        code += 'static int unmarshal_{t_}(uint8_t const ** const ptr, ssize_t * const rem, {t} *);'.format(t_ = linearize_type(typename), t=typename)
    return code

def gen_struct(s, mappings):
    return gen_typename(s['typedef'], True, s['typedef'])

def gen_func(f, namespace):
    return '\n'.join([
        '// function {n}'.format(n = f['name']),
        'static int func_{n}_parse_exec(uint8_t const * cmd , ssize_t);'.format(n = f['name']),
        'static int resp_{n}_parse_exec(uint8_t const * resp, ssize_t);'.format(n = f['name']),
        'static {ns}func_{n}_handler_t func_{n}_handler = NULL;'.format(ns = namespace, n = f['name']),
        'static {ns}resp_{n}_handler_t resp_{n}_handler = NULL;'.format(ns = namespace, n = f['name']),
        ])

def generate(ast, namespace):
    mappings = real_types(ast);
    types = ['\n'.join(
        ['// {t}'.format(t = typ), gen_private_type_decl(typ, mappings)]
        ) for typ in ast['private_types']]
    structs = ['\n'.join(['// {}'.format(s['typedef']), gen_struct_decl(s)])
            for s in ast['structs']]

    funcs = [gen_func(func, namespace) for func in ast['funcs']]

    code = str()
    for frag in [list(), types, structs, funcs]:
        if frag:
            for el in frag:
                code += '\n' + el + '\n'

    return code;

if __name__ == '__main__':
    ast = ast.make_ast(scanner.scan(sys.stdin));
    print(generate(ast), end='');
    sys.exit(0);
