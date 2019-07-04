""" Marshal C source file visitor """

import sys
import lex.scanner
import syntax.ast
from visit.helpers import *;
from utils.typehelpers import *;
from visit.type_gen import *;
from visit.func_gen import *;

def gen_types(ast, namespace, mappings):
    return ['\n'.join([
            '// {}'.format(typ),
            gen_type_marshal(ast, typ),
            gen_type_unmarshal(ast, typ)])
            for typ in ast['private_types'].union(ast['exported_types'])]

def gen_structs(ast):
    return ['\n'.join([
                '// {t}'.format(t = struct['typedef']),
                gen_struct_marshal(ast, struct),
                gen_struct_unmarshal(ast, struct)
            ]) for struct in ast['structs']]

def gen_funcs(ast, namespace):
    funcs = list()
    if ast['funcs']:
        funcs.append('\n'.join([
            '// functions',
            func_resp_sz(ast, namespace),
            func_parse_exec(ast, namespace),
            ]))

        for code, func in enumerate(ast['funcs']):
            funcs.append('\n'.join([
                '\n\n// function {f}'.format(f = func['name']),
                gen_func(ast, namespace, func, code + 1)
                ]))

    return funcs

def generate(ast, namespace):
    types = gen_types(ast, namespace, real_types(ast));
    structs = gen_structs(ast);
    funcs = gen_funcs(ast, namespace);

    code = str()
    for frag in [types, structs, funcs]:
        if frag:
            code += '\n' + '\n'.join(frag)

    return code;

if __name__ == '__main__':
    ast = ast.make_ast(scanner.scan(sys.stdin));
    print(generate(ast, ''), end='');
    sys.exit(0);
