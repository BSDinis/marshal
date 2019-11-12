""" Type helping """

def gen_struct_size(ast, s):
    def real_t(t, real):return real[t] if t in real else t;
    sizes = list()
    real = real_types(ast)
    for arg in s['members']:
        if arg[0] in ast['private_types'].union(ast['exported_types']):
            sizes.append('ssizeof('+real_t(arg[0], real)+')')
        elif any(arg[0] == s['typedef'] for s in ast['structs']):
            sizes.append(gen_struct_size(ast, next(s for s in ast['structs'] if arg[0] == s['typedef'])))
        else:
            add_private_type(ast, arg[0])
            sizes.append('ssizeof('+real_t(arg[0], real)+')')

    return ' + '.join(sizes)

def real_types(ast):
    def find_base(mappings, t):
        while t in mappings:
            t = mappings[t];
        return t

    typedefs = {m['new']: m['old'] for m in ast['typedefs']}
    mappings = {typ: find_base(typedefs, typ) for typ in ast['private_types'].union(ast['exported_types'])}
    return mappings

def slice_arr_type(typ):
    first_brack = typ.find('[')
    last_brack = [p for p, c in enumerate(typ) if ']'][-1]
    return typ[:first_brack], typ[first_brack:last_brack+1]

