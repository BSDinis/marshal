#!/usr/bin/env python3

import sys
import scanner

TYPE    = 0
STRUCT  = 1
FUNC    = 2
TYPEDEF = 3
INCLUDE = 4
DEFINE  = 5

has_nested_list = lambda x : any(isinstance(i, list) for i in x);

def make_type(ast, stmt):
    node = ' '.join(stmt)
    return TYPE, node;

def make_typedef(ast, stmt):
    new_type = stmt[-1];
    old_type = ' '.join(stmt[1:-1])
    node = {'old': old_type, 'new': new_type}
    return TYPEDEF, node;

def make_struct(ast, stmt):
    struct = dict();
    offset = 0;
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
        for name in sub_stmt[1:]:
            if name == ',':
                continue
            if any(pair[1] == name for pair in members):
                raise SyntaxError('Duplicate member named ' + name);

            members.append((typename, name));

    struct['members'] = members;
    return STRUCT, struct;

def make_preprocessor(ast, stmt):
    if stmt[1] == 'include':
        return INCLUDE, ''.join(stmt[2:]);
    elif stmt[1] == 'define':
        return DEFINE, (stmt[2], ' '.join(stmt[3:]));
    else:
        raise SyntaxError('invalid preprocessor primitive: ' + stmt)

def make_node(ast, stmt):
    if has_nested_list(stmt):
        return make_struct(ast, stmt);
    elif stmt[0] == '#':
        return make_preprocessor(ast, stmt)
    elif 'typedef' in stmt:
        return make_typedef(ast, stmt);
    else:
        return make_type(ast, stmt);

def make_ast(stmts):
    ast = {
            'types': set(),
            'structs': list(),
            'funcs': list(),
            'typedefs': list(),
            'includes': {'<stddef.h>', '<stdint.h>', '<stdlib.h>'},
            'defines': list(),
    };
    for stmt in stmts:
        typename, node = make_node(ast, stmt);
        if typename   == TYPE:
            ast['types'].add(node);
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
            elif m[0] not in ast['types']:
                ast['types'].add(m[0])
    return ast;

if __name__ == '__main__':
    stmts = scanner.scan(sys.stdin)
    print(make_ast(stmts))
    sys.exit(0)
