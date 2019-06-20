""" Marshal C source file visitor """

import sys
import scanner
import ast
from ast import struct_size;
from ast import fun_size;
from ast import arg_list;


def gen_types(ast):
    def gen_type_marshal(typename):
        typename_u = typename.replace(' ', '_')
        code = str()
        variable = str()
        code  = \
'''static int marshall_{t_}(uint8_t ** const ptr, ssize_t * const rem, {t} const val)
{{
  if (ptr == NULL) return 1;
  if (rem && *rem < sizeof({t})) return -1;

  memcpy(*ptr, &val, sizeof({t}));

  *ptr += sizeof({t});
  if (rem) *rem -= sizeof({t});

  return 0;
}}'''
        return code.format(t_ = typename_u, t = typename)

    def gen_type_unmarshal(typename):
        typename_u = typename.replace(' ', '_')
        code = str()
        variable = str()
        code  = \
'''static int unmarshall_{t_}(uint8_t ** const ptr, ssize_t * const rem, {t} * const val)
{{
  if (ptr == NULL) return 1;
  if (rem && *rem < sizeof({t})) return -1;

  memcpy(val, *ptr, sizeof({t}));

  *ptr += sizeof({t});
  if (rem) *rem -= sizeof({t});

  return 0;
}}'''
        return code.format(t_ = typename_u, t = typename)


    types = list();
    if ast['types']:
        for typ in ast['types']:
            types.append('\n'.join([
                '// {t}'.format(t = typ),
                gen_type_marshal(typ),
                gen_type_unmarshal(typ)
                ]))

    return types;

def gen_structs(ast):
    def gen_struct_marshal(ast, s):
        typename = s['typedef']
        typename_u = typename.replace(' ', '_')
        sz_decl = 'ssize_t const sz = ' + ' + '.join(['sizeof(' + m[0] + ')' for m in s['members']])
        code = str()
        variable = str()
        code = \
'''static int marshall_{t_}(uint8_t ** const ptr, ssize_t * const rem, {t} const * val)
{{
  if (ptr == NULL) return 1;

  {szdecl};
  if (rem && *rem < sz) return -1;
  int ret = 0;


'''
        for m in s['members']:
            if any(struct['typedef'] == m[0] for struct in ast['structs']):
                code += '  ret = marshall_{t}(ptr, rem, &(val->{data_m}));\n'.format(t = m[0], data_m = m[1]);
            else:
                code += '  ret = marshall_{t}(ptr, rem, val->{data_m});\n'.format(t = m[0], data_m = m[1]);
            code += '  if (ret) return ret; // error\n\n'

        code += \
'''
  *ptr += sz;
  if (rem) *rem -= sz;
  return 0;
}}'''
        return code.format(t_ = typename_u, t = typename, szdecl = sz_decl)


    def gen_struct_unmarshal(ast, s):
        typename = s['typedef']
        typename_u = typename.replace(' ', '_')
        sz_decl = 'const ssize_t sz = ' + ' + '.join(['sizeof(' + m[0] + ')'  for m in s['members']])
        code = str()
        variable = str()
        code = \
'''static int unmarshall_{t_}(uint8_t ** const ptr, ssize_t * const rem, {t} * val)
{{
  if (ptr == NULL) return 1;

  {szdecl};
  if (rem && *rem < sz) return -1;
  int ret = 0;


'''
        for m in s['members']:
            code += '  ret = unmarshall_{t}(ptr, rem, &(val->{data_m}));\n'.format(t = m[0], data_m = m[1]);
            code += '  if (ret) return ret; // error\n\n'

        code += \
'''
  *ptr += sz;
  if (rem) *rem -= sz;
  return 0;
}}'''
        return code.format(t_ = typename_u, t = typename, szdecl = sz_decl)

    structs = list();
    if ast['structs']:
        for struct in ast['structs']:
            structs.append('\n'.join([
                '// {t}'.format(t = struct['typedef']),
                gen_struct_marshal(ast, struct),
                gen_struct_unmarshal(ast, struct)
            ]))
    return structs;

def gen_funcs(ast):
    def func_resp_sz(ast):
        rett = [f['return_t'] for f in ast['funcs']];
        def gen_size(t):
            if t == 'void':
                return ''
            elif t in ast['types']:
                return ' + sizeof({r})'.format(r = t)
            else:
                return ' + ' + struct_size(next(s for s in ast['structs'] if s['typedef'] == t))

        resp_sz = ['sizeof(uint8_t)' + gen_size(t) for t in rett];
        code = \
'''
ssize_t func_resp_sz(uint8_t code)
{
  switch (code) {
'''
        for fcode, sz in enumerate(resp_sz):
            code += '    case {c}:\n      return {s};\n'.format(c = fcode + 1, s = sz);

        code += \
'''    default:
      return -1;
  }
  return -1;
}
'''
        return code

    def resp_parse_exec(ast):
        code = \
'''
int resp_parse_exec(uint8_t * const resp, ssize_t sz)
{
  if (!resp || sz < 1) return -1;
  memset(resp, 0, sz);
  switch (resp[0]) {
'''

        for fcode, fun in enumerate(ast['funcs']):
            code += '    case {c}:\n      return resp_{f}_parse_exec(resp, sz);\n'.format(c = fcode + 1, f = fun['name'])
        code += \
'''    default:
      return -1;
  }
  return 0;
}
'''
        return code
    def func_parse_exec(ast):
        code = \
'''
int func_parse_exec(uint8_t * cmd, ssize_t sz)
{
  if (!cmd || sz < 1) return -1;
  memset(cmd, 0, sz);
  switch (cmd[0]) {
'''

        for fcode, fun in enumerate(ast['funcs']):
            code += '    case {c}:\n      return func_{f}_parse_exec(cmd, sz);\n'.format(c = fcode + 1, f = fun['name'])
        code += \
'''    default:
      return -1;
  }
  return 0;
}
'''
        return code


    def gen_func(f, fcode):
        name = f['name'];
        args = f['args'];
        rett = f['return_t'];
        a = arg_list(f, True)
        def resp_f_parse_exec(f):
            code = \
'''
static int resp_{f}_parse_exec(uint8_t *cmd, ssize_t sz)
{{
  if (!cmd || !resp_{f}_handler || sz < 1) return -1;

  uint8_t * ptr = cmd + 1;
  sz -= 1;

  {typ} ret;
  if (unmarshall_{typ_}(&ptr, &sz, &ret) != 0) return -1;

  return resp_f_handler(ret);
}}
'''
            return code.format(f = name, typ = f['return_t'], typ_ = f['return_t'].replace(' ', '_'))

        def func_f_parse_exec(f):
            code = \
'''
static int func_{f}_parse_exec(uint8_t *cmd, ssize_t sz)
{{
  if (!cmd || !func_{f}_handler || sz < 1) return -1;

  uint8_t * ptr = cmd + 1;
  sz -= 1;
'''
            for arg in args:
                code += \
'''
  {typ} {argname};
  if (unmarshall_{typ_}(&ptr, &sz, &{argname}) != 0) return -1;
'''.format(typ = arg[0], typ_ = arg[0].replace(' ', '_'), argname = arg[1])

            code += \
'''
  return func_f_handler({a});
}}
'''
            return code.format(f = name, a = ', '.join([arg[1] for arg in args]))

        def resp_f_register(f):
            code = \
'''
int resp_{f}_register(resp_{f}_handler_t handler)
{{
  resp_{f}_handler = handler;
  return 0;
}}
'''
            return code.format(f = name)

        def func_f_register(f):
            code = \
'''
int func_{f}_register(func_{f}_handler_t handler)
{{
  func_{f}_handler = handler;
  return 0;
}}
'''
            return code.format(f = name)

        def resp_f_marshal(f, fcode):
            code = \
'''
int resp_{f}_marshal(uint8_t * cmd, ssize_t sz{rarg})
{{
  if (!cmd || sz < 1) return -1;

  cmd[0] = {cd};

  uint8_t * ptr = cmd + 1;
  sz -= 1;
'''
            if rett == 'void':
                pass
            elif rett in ast['types']:
                code += '  if (marshall_{typ_}(&ptr, &sz, ret) != 0)\n    return -1;\n'.format(typ_ = rett.replace(' ', '_'))
            else:
                code += '  if (marshall_{typ_}(&ptr, &sz, &{ret}) != 0)\n    return -1;\n'.format(typ_ = rett.replace(' ', '_'))
            code += \
'''
  return 0;
}}
'''
            return code.format(f = name, cd = fcode, rarg = ', ' + rett + ' ret' if rett != 'void' else '')

        def func_f_marshal(f, fcode):
            code = \
'''
int func_{f}_marshal(uint8_t * cmd, ssize_t sz{aargs})
{{
  if (!cmd || sz < 1) return -1;

  cmd[0] = {cd};

  uint8_t * ptr = cmd + 1;
  sz -= 1;
'''
            for arg in args:
                if arg[0] == 'void':
                    pass
                elif arg[0] in ast['types']:
                    code += '  if (marshall_{typ_}(&ptr, &sz, {argname}) != 0)\n    return -1;\n'.format(typ_ = arg[0].replace(' ', '_'), argname = arg[1])
                else:
                    code += '  if (marshall_{typ_}(&ptr, &sz, &{argname}) != 0)\n    return -1;\n'.format(typ_ = arg[0].replace(' ', '_'), argname = arg[1])
            code += \
'''
  return 0;
}}
'''
            return code.format(f = name, cd = fcode, aargs = ', ' + a if a else '')

        return func_f_parse_exec(f) + resp_f_parse_exec(f) +\
                func_f_register(f) + resp_f_register(f) + \
                func_f_marshal(f, fcode) + resp_f_marshal(f, fcode)

    funcs = list()
    if ast['funcs']:
        funcs.append('\n'.join([
            '// functions',
            func_resp_sz(ast),
            func_parse_exec(ast),
            resp_parse_exec(ast),
            ]))

        for code, func in enumerate(ast['funcs']):
            funcs.append('\n'.join([
                '\n\n// function {f}'.format(f = func['name']),
                gen_func(func, code + 1)
                ]))

    return funcs

def generate(ast):
    types = gen_types(ast);
    structs = gen_structs(ast);
    funcs = gen_funcs(ast);


    code = str()
    for frag in [types, structs, funcs]:
        if frag:
            code += '\n' + '\n'.join(frag)

    return code;

if __name__ == '__main__':
    ast = ast.make_ast(scanner.scan(sys.stdin));
    print(generate(ast), end='');
    sys.exit(0);
