""" Marshal C source file visitor """

import sys
import lex.scanner
import syntax.ast
from visit.helpers import *;
from utils.typehelpers import *;

def gen_types(ast, namespace, mappings):
    def find_last(s, ch): return [p for p, c in enumerate(s) if c == ch][-1];
    def gen_array_marshal(typename, real_typ):
        size = real_typ.split('[')[1].split(']')[0]
        prev_type = real_typ[:find_last(real_typ, '[')]
        code  = \
'''static int marshal_{t_}(uint8_t ** const ptr, ssize_t * const rem, {param})
{{
  for (ssize_t i = 0; i < {sz}; i++) {{
    int ret = marshal_{prev_t}(ptr, rem, val[i]);
    if (ret) return ret;
  }}

  return 0;
}}
'''
        return code.format(t_ = linearize_type(typename),
                param = gen_type_decl([typename, 'const val']),
                sz = size,
                prev_t = linearize_type(prev_type)
                )

    def gen_array_unmarshal(typename, real_typ):
        size = real_typ.split('[')[1].split(']')[0]
        prev_type = real_typ[:find_last(real_typ, '[')]
        code  = \
'''static int unmarshal_{t_}(uint8_t ** const ptr, ssize_t * const rem, {param})
{{
  for (ssize_t i = 0; i < {sz}; i++) {{
    int ret = unmarshal_{prev_t}(ptr, rem, {possible}val[i]);
    if (ret) return ret;
  }}

  return 0;
}}
'''
        return code.format(t_ = linearize_type(typename),
                param = gen_type_decl([typename, 'val']),
                sz = size,
                prev_t = linearize_type(prev_type),
                possible = '' if '[' in prev_type else '&'
                )



    def gen_type_marshal(typename, real_typ):
        code  = \
'''static int marshal_{t_}(uint8_t ** const ptr, ssize_t * const rem, {t} const val)
{{
  if (ptr == NULL) return 1;
  if (rem && *rem < sizeof({t})) return -1;

'''
        nconv = network_convert(ast, real_typ, True, 'val')
        if nconv:
            code += nconv.replace('{', '{{').replace('}', '}}')
            code += '  memcpy(*ptr, &tmp, sizeof({t}));\n'
        else:
            code += '  memcpy(*ptr, &val, sizeof({t}));\n'
        code  += \
'''
  *ptr += sizeof({t});
  if (rem) *rem -= sizeof({t});

  return 0;
}}'''
        return code.format(t_ = linearize_type(typename), t = typename)

    def gen_type_unmarshal(typename, real_typ):
        typename_u = typename.replace(' ', '_').replace('[', '_').replace(']', '')
        code  = \
'''static int unmarshal_{t_}(uint8_t ** const ptr, ssize_t * const rem, {t} * const val)
{{
  if (ptr == NULL) return 1;
  if (rem && *rem < sizeof({t})) return -1;

  memcpy(val, *ptr, sizeof({t}));
'''
        nconv = network_convert(ast, real_typ, False, '*val')
        if nconv:
            code += nconv.replace('{', '{{').replace('}', '}}')
        code  += \
'''
  *ptr += sizeof({t});
  if (rem) *rem -= sizeof({t});

  return 0;
}}'''
        return code.format(t_ = linearize_type(typename), t = typename)


    types = list();
    if ast['types']:
        for typ in ast['types']:
            if '[' not in mappings[typ]:
                types.append('\n'.join([
                    '// {t}'.format(t = typ),
                    gen_type_marshal(typ, mappings[typ]),
                    gen_type_unmarshal(typ, mappings[typ])
                    ]))
            else:
                types.append('\n'.join([
                    '// {t}'.format(t = typ),
                    gen_array_marshal(typ, mappings[typ]),
                    gen_array_unmarshal(typ, mappings[typ])
                    ]))

    return types;

def gen_structs(ast):
    def gen_struct_marshal(ast, s):
        typename = s['typedef']
        typename_u = typename.replace(' ', '_')
        sz_decl = 'ssize_t const sz = ' + ' + '.join(['sizeof(' + m[0] + ')' for m in s['members']])
        code = \
'''static int marshal_{t_}(uint8_t ** const ptr, ssize_t * const rem, {t} const * val)
{{
  if (ptr == NULL) return 1;

  {szdecl};
  if (rem && *rem < sz) return -1;
  int ret = 0;


'''
        for m in s['members']:
            if any(struct['typedef'] == m[0] for struct in ast['structs']):
                code += '  ret = marshal_{t}(ptr, rem, &(val->{data_m}));\n'.format(t = m[0], data_m = m[1]);
            else:
                code += '  ret = marshal_{t}(ptr, rem, val->{data_m});\n'.format(t = linearize_type(m[0]), data_m = m[1]);
            code += '  if (ret) return ret; // error\n\n'

        code += \
'''
  *ptr += sz;
  if (rem) *rem -= sz;
  return 0;
}}'''
        return code.format(t_ = typename_u, t = typename, szdecl = sz_decl)


    def gen_struct_unmarshal(ast, s):
        mappings = real_types(ast);
        typename = s['typedef']
        typename_u = typename.replace(' ', '_')
        sz_decl = 'const ssize_t sz = ' + ' + '.join(['sizeof(' + m[0] + ')'  for m in s['members']])
        code = \
'''static int unmarshal_{t_}(uint8_t ** const ptr, ssize_t * const rem, {t} * val)
{{
  if (ptr == NULL) return 1;

  {szdecl};
  if (rem && *rem < sz) return -1;
  int ret = 0;


'''
        for m in s['members']:
            real_typ = mappings[m[0]] if m[0] in mappings else m[0];
            if '[' in real_typ:
                code += '  ret = unmarshal_{t}(ptr, rem, val->{data_m});\n'.format(t = linearize_type(m[0]), data_m = m[1]);
            else:
                code += '  ret = unmarshal_{t}(ptr, rem, &(val->{data_m}));\n'.format(t = linearize_type(m[0]), data_m = m[1]);
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

def gen_funcs(ast, namespace):
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
ssize_t {ns}func_resp_sz(uint8_t code)
{{
  switch (code) {{
'''
        for fcode, sz in enumerate(resp_sz):
            code += '    case {c}:\n      return {s};\n'.format(c = fcode + 1, s = sz);

        code += \
'''    default:
      return -1;
  }}
  return -1;
}}
'''
        return code.format(ns = namespace);

    def resp_parse_exec(ast):
        code = \
'''
int {ns}resp_parse_exec(uint8_t * const resp, ssize_t sz)
{{
  if (!resp || sz < 1) return -1;
  memset(resp, 0, sz);
  int32_t ticket = -1;
  uint8_t * ptr = resp;
  switch (resp[0]) {{
'''

        for fcode, fun in enumerate(ast['funcs']):
            code += '    case {c}:\n      return resp_{f}_parse_exec(resp, sz);\n'.format(c = fcode + 1, f = fun['name'])
        code += \
'''    default:
      if (unmarshal_int32_t(&ptr, &sz, &ticket) == -1) return -1;
      return ticket;
  }}
  return 0;
}}
'''
        return code.format(ns = namespace)
    def func_parse_exec(ast):
        code = \
'''
int {ns}func_parse_exec(uint8_t * cmd, ssize_t sz)
{{
  if (!cmd || sz < 1) return -1;
  int32_t ticket = -1;
  uint8_t * ptr = cmd;
  switch (cmd[0]) {{
'''

        for fcode, fun in enumerate(ast['funcs']):
            code += '    case {c}:\n      return func_{f}_parse_exec(cmd, sz);\n'.format(c = fcode + 1, f = fun['name'])
        code += \
'''    default:
      if (unmarshal_int32_t(&ptr, &sz, &ticket) == -1) return -1;
      return ticket;
  }}
  return 0;
}}
'''
        return code.format(ns = namespace)


    def gen_func(f, fcode):
        name = f['name'];
        args = f['args'];
        rett = f['return_t'];
        a = arg_list(f, True)
        mappings = real_types(ast)
        def resp_f_parse_exec(f):
            code = \
'''
static int resp_{f}_parse_exec(uint8_t *cmd, ssize_t sz)
{{
  if (!cmd || !resp_{f}_handler || sz < 1) return -1;

  uint8_t * ptr = cmd + 1;
  sz -= 1;

  int32_t __ticket = 0;
  if (unmarshal_int32_t(&ptr, &sz, &__ticket)) return -1;

  {typ} ret;
'''
            real_typ = mappings[f['return_t']] if f['return_t'] in mappings else f['return_t']
            if '[' in real_typ:
                code += '  if (unmarshal_{typ_}(&ptr, &sz, ret) != 0) return -1;\n'
            else:
                code += '  if (unmarshal_{typ_}(&ptr, &sz, &ret) != 0) return -1;\n'

            code += \
'''
  return resp_{f}_handler(__ticket, ret);
}}
'''
            return code.format(f = name, typ = f['return_t'], typ_ = linearize_type(f['return_t']))

        def func_f_parse_exec(f):
            code = \
'''
static int func_{f}_parse_exec(uint8_t *cmd, ssize_t sz)
{{
  if (!cmd || !func_{f}_handler || sz < 1) return -1;

  uint8_t * ptr = cmd + 1;
  sz -= 1;

  int32_t __ticket = 0;
  if (unmarshal_int32_t(&ptr, &sz, &__ticket)) return -1;
'''
            for arg in args:
                real_typ = mappings[arg[0]] if arg[0] in mappings else  arg[0]
                code += \
'''
  {typ_decl};
  if (unmarshal_{typ_}(&ptr, &sz, {argname}) != 0) return -1;
'''.format(typ_decl = gen_type_decl([arg[0] , arg[1]]), typ_ = linearize_type(arg[0]), argname = '&'+arg[1] if '[' not in real_typ else arg[1] )

            code += \
'''
  return func_{f}_handler({a});
}}
'''
            return code.format(f = name, a = ', '.join([arg[1] for arg in [('', '__ticket')] + args]))

        def resp_f_register(f):
            code = \
'''
int {ns}resp_{f}_register({ns}resp_{f}_handler_t handler)
{{
  resp_{f}_handler = handler;
  return 0;
}}
'''
            return code.format(f = name, ns = namespace)

        def func_f_register(f):
            code = \
'''
int {ns}func_{f}_register({ns}func_{f}_handler_t handler)
{{
  func_{f}_handler = handler;
  return 0;
}}
'''
            return code.format(f = name, ns = namespace)

        def resp_f_marshal(f, fcode):
            code = \
'''
int {ns}resp_{f}_marshal(uint8_t * cmd, ssize_t sz, int32_t ticket{rarg})
{{
  if (!cmd || sz < 1) return -1;

  cmd[0] = {cd};

  uint8_t * ptr = cmd + 1;
  sz -= 1;

  if (marshal_int32_t(&ptr, &sz, ticket) != 0) return -1;

'''
            if rett == 'void':
                pass
            elif rett in ast['types']:
                code += '  if (marshal_{typ_}(&ptr, &sz, ret) != 0) return -1;\n'.format(typ_ = linearize_type(rett))
            else:
                code += '  if (marshal_{typ_}(&ptr, &sz, &ret) != 0) return -1;\n'.format(typ_ = linearize_type(rett))
            code += \
'''
  return 0;
}}
'''
            return code.format(ns = namespace, f = name, cd = fcode, rarg = ', ' + rett + ' ret' if rett != 'void' else '')

        def func_f_marshal(f, fcode):
            code = \
'''
int {ns}func_{f}_marshal(uint8_t * cmd, ssize_t sz, int32_t ticket{aargs})
{{
  if (!cmd || sz < 1) return -1;

  cmd[0] = {cd};

  uint8_t * ptr = cmd + 1;
  sz -= 1;

  if (marshal_int32_t(&ptr, &sz, ticket) != 0) return -1;

'''
            for arg in args:
                if arg[0] == 'void':
                    pass
                elif arg[0] in ast['types']:
                    code += '  if (marshal_{typ_}(&ptr, &sz, {argname}) != 0) return -1;\n'.format(typ_ = linearize_type(arg[0]), argname = arg[1])
                else:
                    code += '  if (marshal_{typ_}(&ptr, &sz, &{argname}) != 0) return -1;\n'.format(typ_ = linearize_type(arg[0]), argname = arg[1])
            code += \
'''
  return 0;
}}
'''
            return code.format(ns = namespace, f = name, cd = fcode, aargs = ', ' + a if a else '')

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
