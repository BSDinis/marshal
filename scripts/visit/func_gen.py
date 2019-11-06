""" function generation """

from visit.helpers import *
from utils.typehelpers import *

def gen_size(ast, t):
    if t == 'void':
        return ''
    elif t in ast['private_types'].union(ast['exported_types']):
        return ' + ssizeof({r})'.format(r = t)
    else:
        return ' + ' + struct_size(next(s for s in sorted(ast['structs'], key = lambda x: x['struct']) if s['typedef'] == t))

def func_resp_sz(ast, namespace):
    rett = [f['return_t'] for f in sorted(ast['funcs'], key = lambda x: x['name'])];
    resp_sz = ['ssizeof(uint8_t)' + gen_size(ast, t) for t in rett];
    code = \
'''
ssize_t {ns}func_resp_sz(uint8_t const code)
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


def func_parse_exec(ast, namespace):
    code = \
'''
int {ns}parse_exec(uint8_t const * cmd, ssize_t sz)
{{
  if (!cmd || sz < 1) return -1;
  int32_t ticket = -1;
  do {{
    uint8_t const * ptr = cmd;
    switch (cmd[0]) {{
'''

    for fcode, fun in enumerate(ast['funcs']):
        code += '      case {c}:\n        (void)func_{f}_parse_exec(&cmd, &sz);break;\n'.format(c = fcode + 1, f = fun['name'])
        code += '      case {c} | (1<<7):\n        (void)resp_{f}_parse_exec(&cmd, &sz);break;\n'.format(c = fcode + 1, f = fun['name'])
    code += \
'''      default:
      if (unmarshal_int32_t(&ptr, &sz, &ticket) == -1) return -1;
      return ticket;
    }}
  }} while (sz > 1);
  return 0;
}}
'''
    return code.format(ns = namespace)


def gen_func(ast, namespace, f, fcode):
    name = f['name'];
    args = f['args'];
    rett = f['return_t'];
    a = arg_list(f, True)
    mappings = real_types(ast)
    def resp_f_parse_exec(f):
        code = \
'''
static int resp_{f}_parse_exec(uint8_t const ** cmd, ssize_t * sz)
{{
  if (!cmd || !sz || !(*cmd) || !resp_{f}_handler || *sz < 1) return -1;

  uint8_t const * ptr = *cmd + 1;
  *sz -= 1;

  int32_t __ticket = 0;
  if (unmarshal_int32_t(&ptr, sz, &__ticket)) return -1;

  {typ} ret;
'''
        real_typ = mappings[f['return_t']] if f['return_t'] in mappings else f['return_t']
        if '[' in real_typ:
            code += '  if (unmarshal_{typ_}(&ptr, sz, ret) != 0) return -1;\n'
        else:
            code += '  if (unmarshal_{typ_}(&ptr, sz, &ret) != 0) return -1;\n'

        code += \
'''
  *cmd = ptr;
  return resp_{f}_handler(__ticket, ret);
}}
'''
        return code.format(f = name, typ = f['return_t'], typ_ = linearize_type(f['return_t']))

    def func_f_parse_exec(f):
        code = \
'''
static int func_{f}_parse_exec(uint8_t const ** cmd, ssize_t * sz)
{{
  if (!cmd || !sz || !(*cmd) || !func_{f}_handler || *sz < 1) return -1;

  uint8_t const * ptr = *cmd + 1;
  *sz -= 1;

  int32_t __ticket = 0;
  if (unmarshal_int32_t(&ptr, sz, &__ticket)) return -1;
'''
        for arg in args:
            real_typ = mappings[arg[0]] if arg[0] in mappings else  arg[0]
            code += \
'''
  {typ_decl};
  if (unmarshal_{typ_}(&ptr, sz, {argname}) != 0) return -1;
'''.format(typ_decl = gen_type_decl([arg[0] , arg[1]]), typ_ = linearize_type(arg[0]), argname = '&'+arg[1] if '[' not in real_typ else arg[1] )

        code += \
'''
  *cmd = ptr;
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
int {ns}resp_{f}_marshal(uint8_t * cmd, ssize_t sz, int32_t const ticket{rarg})
{{
  if (!cmd || sz < 1) return -1;

  cmd[0] = {cd} | (1 << 7);

  uint8_t * ptr = cmd + 1;
  sz -= 1;

  if (marshal_int32_t(&ptr, &sz, ticket) != 0) return -1;

'''
        if rett == 'void':
            pass
        elif rett in ast['private_types'].union(ast['exported_types']):
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
int {ns}func_{f}_marshal(uint8_t * cmd, ssize_t sz, int32_t const ticket{aargs})
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
            elif arg[0] in ast['private_types'].union(ast['exported_types']):
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
