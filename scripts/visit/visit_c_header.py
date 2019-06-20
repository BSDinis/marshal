""" Marshal C header file visitor """

import sys
import lex.scanner
import syntax.ast
from visit.helpers import *;

def gen_includes(ast, to_file, namespace):
    includes = str()
    if ast['includes'] and to_file:
        includes += '\n'
        for inc in ast['includes']:
            includes += '#include {f}\n'.format(f = inc)

    return includes

def gen_defines(ast, to_file, namespace):
    defines = str()
    if ast['defines'] and to_file:
        defines += '\n'
        for d in ast['defines']:
           defines += '#define {o} {n}\n'.format(o = d[0], n = d[1])

    return defines

def gen_structs(ast, namespace):
    structs = list();
    if ast['structs']:
        for struct in ast['structs']:
            code = '// {t}\n'.format(t = struct['typedef'])
            code += 'typedef struct ' + struct['struct'] + '\n{\n';
            for member in struct['members']:
                code += '  ' + member[0] + ' ' + member[1] + ';\n';
            code += '} ' + struct['typedef'] + ';';
            structs.append(code);

    return structs;

def gen_typedefs(ast, namespace):
    typedefs = list();
    if ast['typedefs']:
        typedefs.append('// typedefs')
        for typedef in ast['typedefs']:
            typedefs.append('typedef {o} {n};'.format(n = typedef['new'], o = typedef['old']))

    return typedefs


def gen_funcs(ast, namespace):
    funcs = list()
    if ast['funcs']:
        funcs.append('\n'.join([
            '// function prototypes',
            'ssize_t '+namespace+'func_resp_sz(uint8_t code);',
            'int '+namespace+'func_parse_exec(uint8_t * cmd, ssize_t);',
            'int '+namespace+'resp_parse_exec(uint8_t * const resp, ssize_t);'
            ]))
        for code, fun in enumerate(ast['funcs']):
            rett = fun['return_t']
            name = fun['name']
            a = arg_list(fun, False)
            funcs.append('\n'.join([
                '// function {f}'.format(f = name),
                'uint8_t const {ns}func_{f}_code = {c};'.format(ns = namespace, f = name, c = code + 1),
                'ssize_t const {ns}func_{f}_sz = {sz};'.format(ns = namespace, f = name, sz = fun_size(ast, fun)),
                'ssize_t const {ns}resp_{f}_sz = {sz};'.format(ns = namespace, f = name, sz = fun_ret_size(ast, fun)),
                'typedef int (* {ns}func_{n}_handler_t)(uint32_t ticket{args});'.format(ns = namespace, n = name, args = ', ' + a if a else ''),
                'typedef int (* {ns}resp_{n}_handler_t)(uint32_t ticket{r});'.format(ns = namespace, r = ', ' + rett if rett != 'void' else '', n = name),
                'int {ns}func_{f}_register({ns}func_{f}_handler_t);'.format(ns = namespace, f = name),
                'int {ns}resp_{f}_register({ns}resp_{f}_handler_t);'.format(ns = namespace, f = name),
                'int {ns}func_{f}_marshal(uint8_t *, ssize_t sz, uint32_t ticket{args});'.format(ns = namespace, f = name, args = ', ' + a if a else ''),
                'int {ns}resp_{f}_marshal(uint8_t *, ssize_t sz, uint32_t ticket{args});'.format(ns = namespace, f = name, args = ', ' + rett if rett != 'void' else ''),
                ]))
    return funcs;



def generate(ast, to_file, namespace):
    includes = gen_includes(ast, to_file, namespace);
    defines = gen_defines(ast, to_file, namespace);
    types = list();
    structs = gen_structs(ast, namespace);
    typedefs = gen_typedefs(ast, namespace);
    funcs = gen_funcs(ast, namespace);


    code = includes + defines;
    for frag in [types, structs, typedefs, funcs]:
        if frag:
            for el in frag:
                code += '\n' + el + '\n'

    return code;

if __name__ == '__main__':
    ast = ast.make_ast(scanner.scan(sys.stdin));
    print(generate(ast, true, ''), end='');
    sys.exit(0);
