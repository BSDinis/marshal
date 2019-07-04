""" Type helping """

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

