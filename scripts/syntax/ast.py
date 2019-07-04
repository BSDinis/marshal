""" Marshal ast generator """

import sys
import lex.scanner
from utils.typehelpers import *

TYPE    = 0
STRUCT  = 1
FUNC    = 2
TYPEDEF = 3
INCLUDE = 4
DEFINE  = 5

has_nested_list = lambda x : any(isinstance(i, list) for i in x);

def add_exported_type(ast, t):
    def last_pos(string, char): return [pos for pos, c in enumerate(string) if char == c][-1]
    ast['exported_types'].add(t)
    if t in ast['private_types']:
        ast['private_types'].remove(t)

    real_type = real_types(ast)[t]
    if '[' in real_type:
        add_private_type(ast, real_type[:last_pos(real_type, '[')])

def add_private_type(ast, t):
    def last_pos(string, char): return [pos for pos, c in enumerate(string) if char == c][-1]
    ast['private_types'].add(t)
    real_type = real_types(ast)[t]
    if '[' in real_type:
        add_private_type(ast, real_type[:last_pos(real_type, '[')])

def make_type(ast, stmt):
    node = ' '.join(stmt)
    return TYPE, node;

def make_typedef(ast, stmt):
    new_type = stmt[-1].split('[')[0];
    if '[' in stmt[-1]:
        arr_dim = stmt[-1][stmt[-1].find('['):]
    else:
        arr_dim = ''
    old_type = ' '.join(stmt[1:-1])+arr_dim
    node = {'old': old_type, 'new': new_type}
    return TYPEDEF, node;

def make_struct(ast, stmt, print_types):
    struct = dict();
    offset = 0;
    struct['public'] = print_types
    if stmt[0] == 'typedef':
        offset += 1
        if isinstance(stmt[-1], str):
            struct['typedef'] = stmt[-1]
        else:
            raise SyntaxError(stmt[-1] + " must be a string to name a type");

    if stmt[offset] != 'struct':
        raise SyntaxError("invalid construct");
    if not isinstance(stmt[offset+1], str):
        raise SyntaxError(stmt[offset+1] + " does not name a type");
    if not isinstance(stmt[offset+2], list):
        raise SyntaxError(stmt[offset+2] + " must be a list");

    struct['struct'] = stmt[offset+1]
    if 'typedef' not in struct:
        struct['typedef'] = struct['struct'];

    members = list();
    for sub_stmt in stmt[offset+2]:
        if any(not isinstance(i, str) for i in sub_stmt):
            raise SyntaxError('All elements of the statement must be strings');
        if len(sub_stmt) < 2:
            raise SyntaxError('Should have at least two');

        typename = sub_stmt[0];
        _names = ''.join(sub_stmt[1:]).split(',')
        for n in _names:
            if '[' in n:
                base_name, dim = slice_arr_type(n)
            else:
                base_name, dim = n, ''

            if any(pair[1] == base_name for pair in members):
                raise SyntaxError('Duplicate member named ' + base_name);

            members.append((typename+dim, base_name));

    struct['members'] = members;
    return STRUCT, struct;

def make_func(ast, stmt):
    f = {
            'name': str(),
            'return_t': str(),
            'args': list(),
        }

    for idx, s in enumerate(stmt):
        if s == '(':
            break
    else:
        raise SyntaxError('no parens in function ' + str(stmt))

    f['return_t'] = ' '.join(stmt[:idx - 1]);
    f['name'] = stmt[idx - 1];

    arg = []
    for i, s in enumerate(stmt[idx + 1:]):
        if s == ')':
            if arg:
                f['args'].append((' '.join(arg[:-1]), arg[-1]))
            break
        elif s == ',':
            f['args'].append((' '.join(arg[:-1]), arg[-1]))
            arg = []
        else:
            arg += [s]
    else:
        raise SyntaxError('unmatched parens' + str(stmt))

    return FUNC, f



def make_preprocessor(ast, stmt):
    if stmt[1] == 'include':
        return INCLUDE, ''.join(stmt[2:]);
    elif stmt[1] == 'define':
        return DEFINE, (stmt[2], ' '.join(stmt[3:]));
    else:
        raise SyntaxError('invalid preprocessor primitive: ' + stmt)

def make_node(ast, stmt, print_types):
    if has_nested_list(stmt):
        return make_struct(ast, stmt, print_types);
    elif stmt[0] == '#':
        return make_preprocessor(ast, stmt)
    elif 'typedef' in stmt:
        return make_typedef(ast, stmt);
    elif '(' in stmt:
        return make_func(ast, stmt);
    else:
        return make_type(ast, stmt);

def make_ast(stmts, print_types):
    ast = {
            'exported_types': set(),
            'private_types': {'int32_t'},
            'structs': list(),
            'funcs': list(),
            'typedefs': list(),
            'includes': {'<arpa/inet.h>', '<stddef.h>', '<stdint.h>', '<stdlib.h>'},
            'defines': list(),
    };
    for stmt in stmts:
        typename, node = make_node(ast, stmt, print_types);
        if typename   == TYPE:
            if print_types:
                add_exported_type(ast, node);
            else:
                add_private_type(ast, node);
        elif typename == STRUCT:
            ast['structs'].append(node)
        elif typename == TYPEDEF:
            ast['typedefs'].append(node);
        elif typename == FUNC:
            ast['funcs'].append(node);
        elif typename == INCLUDE:
            ast['includes'].add(node);
        elif typename == DEFINE:
            ast['defines'].append(node);
        else:
            raise ValueError(str(typename)  + ' does not name a node type');

    for s in ast['structs']:
        for m in s['members']:
            if any(struct['typedef'] == m[0] for struct in ast['structs']):
                pass
            elif m[0] not in ast['private_types'].union(ast['exported_types']) :
                add_private_type(ast, m[0])

    for f in ast['funcs']:
        if f['return_t'] != 'void' and not any(f['return_t'] == s['typedef'] for s in ast['structs']):
            add_private_type(ast, f['return_t'])

        for t in f['args']:
            if t[0] != 'void' and not any(t[0] == s['typedef'] for s in ast['structs']):
                add_private_type(ast, t[0])

    return ast;

if __name__ == '__main__':
    stmts = scanner.scan(sys.stdin)
    print(make_ast(stmts, True))
    sys.exit(0)
