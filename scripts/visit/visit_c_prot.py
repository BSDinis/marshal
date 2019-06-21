""" Marshal C prototype visitor """

import sys
import lex.scanner
import syntax.ast
from visit.helpers import *
from utils.typehelpers import *


def gen_typename(typename, ref, real_t):
    typename_u = typename.replace(' ', '_')
    code = str()
    variable = str()
    if ref: variable = '{t} *'.format(t = typename);
    else:   variable = '{t}'.format(t = typename);
    code  = 'static int marshal_{t_}(uint8_t ** const ptr, ssize_t * const rem, const {v});\n'.format(t_ = linearize_type(typename), v=variable)
    if '[' in real_t:
        code += 'static int unmarshal_{t_}(uint8_t ** const ptr, ssize_t * const rem, {t});'.format(t_ = linearize_type(typename), t=gen_type_decl([typename, 'val']))
    else:
        code += 'static int unmarshal_{t_}(uint8_t ** const ptr, ssize_t * const rem, {t} *);'.format(t_ = linearize_type(typename), t=typename)
    return code

def gen_type(t, mappings):
    real_t = mappings[t] if t in mappings else t;
    return gen_typename(t, False, real_t);

def gen_struct(s, mappings):
    return gen_typename(s['typedef'], True, s['typedef'])

def gen_func(f, namespace):
    return '\n'.join([
        '// function {n}'.format(n = f['name']),
        'static int func_{n}_parse_exec(uint8_t *cmd , ssize_t);'.format(n = f['name']),
        'static int resp_{n}_parse_exec(uint8_t *resp, ssize_t);'.format(n = f['name']),
        'static {ns}func_{n}_handler_t func_{n}_handler = NULL;'.format(ns = namespace, n = f['name']),
        'static {ns}resp_{n}_handler_t resp_{n}_handler = NULL;'.format(ns = namespace, n = f['name']),
        ])

def generate(ast, namespace):
    types = list();
    structs = list();
    typedefs = list();
    funcs = list();

    mappings = real_types(ast);

    if ast['types']:
        for typ in ast['types']:
            types.append('// {t}\n'.format(t = typ) + gen_type(typ, mappings))

    if ast['structs']:
        for struct in ast['structs']:
            structs.append('// {t}\n'.format(t = struct['typedef']) + gen_struct(struct, mappings))

    if ast['funcs']:
        for func in ast['funcs']:
            funcs.append(gen_func(func, namespace))

    code = str()
    for frag in [typedefs, types, structs, funcs]:
        if frag:
            for el in frag:
                code += '\n' + el + '\n'

    return code;

if __name__ == '__main__':
    ast = ast.make_ast(scanner.scan(sys.stdin));
    print(generate(ast), end='');
    sys.exit(0);
