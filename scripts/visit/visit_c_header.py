""" Marshal C header file visitor """

import sys
import lex.scanner
import syntax.ast
from visit.helpers import *;
from utils.typehelpers import *;
from visit.type_gen import *;

def gen_includes(ast, to_file, namespace):
    includes = str()
    if ast['includes'] and to_file:
        includes += '\n'
        for inc in sorted(ast['includes']):
            includes += '#include {f}\n'.format(f = inc)

    return includes

def gen_defines(ast, to_file, namespace):
    defines = str()
    if ast['defines'] and to_file:
      defines += '\n'
      for d in ast['defines']:
        defines += '#ifndef {o}\n'.format(o = (d[0].split('(')[0]))
        defines += '#define {o} {n}\n'.format(o = d[0], n = d[1])
        defines += '#endif\n'

    return defines

def gen_structs(ast, namespace):
    structs = list();
    if ast['structs']:
        for struct in ast['structs']:
            code = '// {t}\n'.format(t = struct['typedef'])
            code += 'typedef struct ' + struct['struct'] + '\n{\n';
            for member in struct['members']:
                if '[' in member[0]:
                    base_type, dim = slice_arr_type(member[0])
                else:
                    base_type, dim = member[0], ''

                code += '  ' + base_type + ' ' + member[1] + dim + ';\n';
            code += '} ' + struct['typedef'] + ';';
            structs.append(code);

    return structs;

def gen_typedefs(ast, namespace):
    typedefs = list();
    if ast['typedefs']:
        typedefs.append('// typedefs')
        for typedef in ast['typedefs']:
            dim = ''
            if '[' in typedef['old']:
                dim = typedef['old'][typedef['old'].find('['):]

            typedefs.append('typedef {o} {n}{d};'.format(n = typedef['new'], o = typedef['old'].split('[')[0], d = dim))

    return typedefs


def gen_funcs(ast, namespace):
    funcs = list()
    if ast['funcs']:
        funcs.append('\n'.join([
            '// function prototypes',
            'ssize_t '+namespace+'func_resp_sz(uint8_t code);',
            'int '+namespace+'parse_exec(uint8_t const * cmd, ssize_t);',
            ]))
        for code, fun in enumerate(ast['funcs']):
            rett = fun['return_t']
            name = fun['name']
            a = arg_list(fun, False)
            funcs.append('\n'.join([
                '// function {f}'.format(f = name),
                'static uint8_t const {ns}func_{f}_code = {c};'.format(ns = namespace, f = name, c = code + 1),
                'static ssize_t const {ns}func_{f}_sz = {sz};'.format(ns = namespace, f = name, sz = fun_size(ast, fun)),
                'static ssize_t const {ns}resp_{f}_sz = {sz};'.format(ns = namespace, f = name, sz = fun_ret_size(ast, fun)),
                'typedef int (* {ns}func_{n}_handler_t)(int32_t ticket{args});'.format(ns = namespace, n = name, args = ', ' + a if a else ''),
                'typedef int (* {ns}resp_{n}_handler_t)(int32_t ticket{r});'.format(ns = namespace, r = ', ' + rett if rett != 'void' else '', n = name),
                'int {ns}func_{f}_register({ns}func_{f}_handler_t);'.format(ns = namespace, f = name),
                'int {ns}resp_{f}_register({ns}resp_{f}_handler_t);'.format(ns = namespace, f = name),
                'int {ns}func_{f}_marshal(uint8_t *, ssize_t sz, int32_t const ticket{args});'.format(ns = namespace, f = name, args = ', ' + a if a else ''),
                'int {ns}resp_{f}_marshal(uint8_t *, ssize_t sz, int32_t const ticket{args});'.format(ns = namespace, f = name, args = ', ' + rett if rett != 'void' else ''),
                ]))
    return funcs;


def gen_types(ast):
    mappings = real_types(ast);
    return ['\n'.join(
        ['// {}'.format(typ), gen_public_type_decl(typ, mappings)]
        ) for typ in sorted(ast['exported_types'])] \
                +\
        ['\n'.join(['// {}'.format(s['typedef']), gen_struct_decl(s)])
            for s in ast['structs'] if s['public']]

def generate(ast, to_file, namespace):
    includes = gen_includes(ast, to_file, namespace);
    defines = gen_defines(ast, to_file, namespace);
    types = gen_types(ast);
    structs = gen_structs(ast, namespace);
    typedefs = gen_typedefs(ast, namespace);
    funcs = gen_funcs(ast, namespace);


    code = includes + defines;
    for frag in [typedefs, structs, types, funcs]:
        if frag:
            for el in frag:
                code += '\n' + el + '\n'

    return code;

if __name__ == '__main__':
    ast = ast.make_ast(scanner.scan(sys.stdin));
    print(generate(ast, true, ''), end='');
    sys.exit(0);
