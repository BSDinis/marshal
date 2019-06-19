""" Marshal C source file visitor """

import sys
import scanner
import ast


def gen_func(f):
    return ['']

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

def generate(ast):
    types = list();
    structs = list();
    typedefs = list();
    funcs = list();

    if ast['types']:
        for typ in ast['types']:
            types.append([
                '// {t}'.format(t = typ),
                gen_type_marshal(typ),
                gen_type_unmarshal(typ)
                ])

    if ast['structs']:
        for struct in ast['structs']:
            structs.append([
                '// {t}'.format(t = struct['typedef']),
                gen_struct_marshal(ast, struct),
                gen_struct_unmarshal(ast, struct)
            ])

    if ast['funcs']:
        for func in ast['funcs']:
            funcs.append([gen_func(func)])

    code = str()
    for frag in [types, structs, typedefs, funcs]:
        if frag:
            for group in frag:
                code += '\n'
                for el in group:
                    code += el + '\n';

    return code;

if __name__ == '__main__':
    ast = ast.make_ast(scanner.scan(sys.stdin));
    print(generate(ast), end='');
    sys.exit(0);
