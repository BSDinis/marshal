""" type generation """
from visit.helpers import *
from utils.typehelpers import *

def get_prev_arr_type(typename):
    if '[' not in typename:
        raise TypeError(typename + ' is not an array type')

    last_open_brack = [p for p, c in enumerate(typename) if c == '['][-1]
    last_close_brack = [p for p, c in enumerate(typename) if c == ']'][-1]
    return typename[:last_open_brack], typename[last_open_brack + 1: last_close_brack]

def gen_var_decl(typename, real_t, is_ref, is_const, name):
    qual = 'const ' if is_const else ''
    if '[' in real_t:
        base, dim = slice_arr_type(real_t)
        return '{b} {q}{n}{d}'.format(b = base, q = qual, n = name, d = dim)
    else:
        return '{t} {q}{r} {n}'.format(\
                t = typename, \
                q = qual,\
                r = '* const' if is_ref else '',\
                n = name)

##################################################################
#                                                                #
#                                                                #
#                         DECLs                                  #
#                                                                #
#                                                                #
##################################################################

def gen_type_marshal_decl(typename, real_typ, is_ref, is_public):
    u_name = linearize_type(typename);
    mvar = gen_var_decl(typename, real_typ, is_ref, True, 'val');
    qualifier = '' if is_public else 'static ';
    return '{q}int marshal_{u}(uint8_t ** const ptr, ssize_t * const rem, {v});\n'.format(\
            q = qualifier, u = u_name, v = mvar);

def gen_type_unmarshal_decl(typename, real_typ, is_arr, is_public):
    u_name = linearize_type(typename);
    umvar = gen_var_decl(typename, real_typ, True, False, 'val');
    qualifier = '' if is_public else 'static ';
    return '{q}int unmarshal_{u}(uint8_t const ** const ptr, ssize_t * const rem, {v});\n'.format(\
            q = qualifier, u = u_name, v = umvar);

def gen_type_decl(typename, real_typ, is_ref, is_arr, is_public):
    return gen_type_marshal_decl(typename, real_typ, is_ref, is_public) + \
            gen_type_unmarshal_decl(typename, real_typ, is_arr, is_public)

def gen_public_type_decl(typename, mappings):
    real_t = mappings[typename] if typename in mappings else typename
    return gen_type_decl(typename, real_t, False, '[' in real_t, True)

def gen_private_type_decl(typename, mappings):
    real_t = mappings[typename] if typename in mappings else typename
    return gen_type_decl(typename, real_t, False, '[' in real_t, False)

def gen_struct_decl(s):
    return gen_type_decl(s['typedef'], s['typedef'], True, '[' in s['typedef'], s['public'])

##################################################################
#                                                                #
#                                                                #
#                         BODYs                                  #
#                                                                #
#                                                                #
##################################################################

def gen_type_marshal(ast, typename):
    mappings = real_types(ast)
    real_typ = mappings[typename] if typename in mappings else typename

    is_public = typename in ast['exported_types']

    if '[' in real_typ:
        return gen_type_array_marshal(ast, typename, real_typ, is_public)
    else:
        return gen_type_base_marshal(ast, typename, real_typ, is_public)

def gen_type_base_marshal(ast, typename, real_typ, is_public):
    header = gen_type_marshal_decl(typename, real_typ, False, is_public).replace(';', '')
    body = \
'''{{
  if (ptr == NULL) return 1;
  if (rem && *rem < sizeof({t})) return -1;

'''
    nconv = network_convert(ast, real_typ, True, 'val')
    if nconv:
        body += nconv.replace('{', '{{').replace('}', '}}')
        body += '  memcpy(*ptr, &tmp, sizeof({t}));\n'
    else:
        body += '  memcpy(*ptr, &val, sizeof({t}));\n'
    body  += \
'''
  *ptr += sizeof({t});
  if (rem) *rem -= sizeof({t});

  return 0;
}}'''

    return header + body.format(t = typename)

def gen_type_array_marshal(ast, typename, real_typ, is_public):
    header = gen_type_marshal_decl(typename, real_typ, False, is_public).replace(';', '')

    prev, dim = get_prev_arr_type(real_typ)
    body = \
'''{{
  if (ptr == NULL) return 1;
  if (rem && *rem < sizeof({t})) return -1;

  for (ssize_t i = 0; i < {sz}; i++) {{
    int ret = marshal_{prev_t}(ptr, rem, val[i]);
    if (ret) return ret;
  }}

  return 0;
}}'''.format(t = typename, sz = dim, prev_t = linearize_type(prev));

    return header + body

def gen_type_unmarshal(ast, typename):
    mappings = real_types(ast)
    real_typ = mappings[typename] if typename in mappings else typename

    is_public = typename in ast['exported_types']

    if '[' in real_typ:
        return gen_type_array_unmarshal(ast, typename, real_typ, is_public)
    else:
        return gen_type_base_unmarshal(ast, typename, real_typ, is_public)

def gen_type_base_unmarshal(ast, typename, real_typ, is_public):
    header = gen_type_unmarshal_decl(typename, real_typ, False, is_public).replace(';', '')
    body = \
'''{{
  if (ptr == NULL) return 1;
  if (rem && *rem < sizeof({t})) return -1;

  memcpy(val, *ptr, sizeof({t}));
'''
    nconv = network_convert(ast, real_typ, False, '*val')
    if nconv:
        body += nconv.replace('{', '{{').replace('}', '}}')
    body  += \
'''
  *ptr += sizeof({t});
  if (rem) *rem -= sizeof({t});

  return 0;
}}'''

    return header + body.format(t = typename)

def gen_type_array_unmarshal(ast, typename, real_typ, is_public):
    header = gen_type_unmarshal_decl(typename, real_typ, False, is_public).replace(';', '')

    prev, dim = get_prev_arr_type(real_typ)
    body = \
'''{{
  if (ptr == NULL) return 1;
  if (rem && *rem < sizeof({t})) return -1;

  for (ssize_t i = 0; i < {sz}; i++) {{
    int ret = unmarshal_{prev_t}(ptr, rem, {maybe}val[i]);
    if (ret) return ret;
  }}

  return 0;
}}'''.format(t = typename, sz = dim, prev_t = linearize_type(prev), maybe = '&' if '[' not in prev else '');

    return header + body


def gen_struct_marshal(ast, s):
    typename = s['typedef']
    typename_u = typename.replace(' ', '_')
    sz_decl = 'ssize_t const sz = ' + ' + '.join(['sizeof(' + m[0] + ')' for m in s['members']])
    header = gen_struct_decl(s).split(';')[0]
    code = \
'''
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
    return header + code.format(t_ = typename_u, t = typename, szdecl = sz_decl)


def gen_struct_unmarshal(ast, s):
    mappings = real_types(ast);
    typename = s['typedef']
    typename_u = typename.replace(' ', '_')
    sz_decl = 'const ssize_t sz = ' + ' + '.join(['sizeof(' + m[0] + ')'  for m in s['members']])
    header = gen_struct_decl(s).replace('\n','').split(';')[1]+'\n'
    code = \
'''
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
    return header + code.format(t_ = typename_u, t = typename, szdecl = sz_decl)
