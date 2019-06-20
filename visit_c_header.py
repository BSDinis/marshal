""" Marshal C header file visitor """

import sys
import scanner
import ast
from ast import arg_list
from ast import fun_size
from ast import fun_ret_size

def gen_includes(ast, to_file):
    includes = str()
    if ast['includes'] and to_file:
        includes += '\n'
        for inc in ast['includes']:
            includes += '#include {f}\n'.format(f = inc)

    return includes

def gen_defines(ast, to_file):
    defines = str()
    if ast['defines'] and to_file:
        defines += '\n'
        for d in ast['defines']:
           defines += '#define {o} {n}\n'.format(o = d[0], n = d[1])

    return defines

def gen_structs(ast):
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

def gen_typedefs(ast):
    typedefs = list();
    if ast['typedefs']:
        typedefs.append('// typedefs')
        for typedef in ast['typedefs']:
            typedefs.append('typedef {o} {n};'.format(n = typedef['new'], o = typedef['old']))

    return typedefs


def gen_funcs(ast):
    funcs = list()
    if ast['funcs']:
        funcs.append('\n'.join([
            '// function prototypes',
            'ssize_t func_resp_sz(uint8_t code);',
            'int func_parse_exec(uint8_t * cmd, ssize_t);',
            'int resp_parse_exec(uint8_t * const resp, ssize_t);'
            ]))
        for code, fun in enumerate(ast['funcs']):
            rett = fun['return_t']
            name = fun['name']
            a = arg_list(fun, True)
            funcs.append('\n'.join([
                '// function {f}'.format(f = name),
                'uint8_t const func_{f}_code = {c};'.format(f = name, c = code + 1),
                'ssize_t const func_{f}_sz = {sz};'.format(f = name, sz = fun_size(ast, fun)),
                'ssize_t const resp_{f}_sz = {sz};'.format(f = name, sz = fun_ret_size(ast, fun)),
                'typedef int (* func_{n}_handler_t)({args});'.format(n = name, args = arg_list(fun, False)),
                'typedef int (* resp_{n}_handler_t)({r});'.format(r = rett if rett != 'void' else '', n = name),
                'int func_{f}_register(func_{f}_handler_t);'.format(f = name),
                'int resp_{f}_register(resp_{f}_handler_t);'.format(f = name),
                'int func_{f}_marshal(uint8_t *, ssize_t sz{args});'.format(f = name, args = ', ' + a if a else ''),
                'int resp_{f}_marshal(uint8_t *, ssize_t sz{args});'.format(f = name, args = ', ' + rett if rett != 'void' else ''),
                ]))
    return funcs;



def generate(ast, to_file):
    includes = gen_includes(ast, to_file);
    defines = gen_defines(ast, to_file);
    types = list();
    structs = gen_structs(ast);
    typedefs = gen_typedefs(ast);
    funcs = gen_funcs(ast);


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
