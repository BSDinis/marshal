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
        funcs.append('\n'.join([
            '// function prototypes',
            'ssize_t func_resp_sz(uint8_t code);',
            'int func_parse_exec(uint8_t * cmd, ssize_t, uint8_t *resp, ssize_t);'
            'int resp_parse_exec(uint8_t const * const cmd, ssize_t const);'
            ]))
        for fun in ast['funcs']:
            funcs.append('\n'.join([
                '// function {f}'.format(f = fun.name),
                gen_handler_typedef(fun),
                'ssize_t const func_{f}_sz = {sz};'.format(f = fun.name, sz = size(fun)),
                'int func_{f}_register(func_{f}_t);'.format(f = fun.name),
                ]))


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
