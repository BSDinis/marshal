""" Marshal C source file visitor """

import sys
import scanner
import ast


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
    def gen_func(f):
        name = f['name'];
        args = f['args'];
        def func_parse_exec(f):
            code = \
'''
static int func_{f}_parse_exec(uint8_t *cmd, ssize_t sz)
{{
  if (!cmd || !func_{f}_handler_t || sz < 1) return -1;

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
}}'''
            return code.format(f = name, a = ', '.join([arg[1] for arg in args]))
        return func_parse_exec(f)



    funcs = list()
    if ast['funcs']:
        for func in ast['funcs']:
            funcs.append('\n'.join([
                '// function {f}'.format(f = func['name']),
                gen_func(func)
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
