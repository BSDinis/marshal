""" Type helping """

from syntax.ast import add_type

def linearize_type(t):
    return t.replace(' ', '_').replace('[', '_').replace(']', '')

def network_convert(ast, typ, to_network, name):
    """
    convert type to network order
    basically checks if the type is like int (ie, int, long, or typedef to it)
    this needs to be formatted (with val)
    """
    real_typ = next((t['old'] for t in ast['typedefs'] if t['new'] == typ), typ);
    if '*' in name:
        lval = name;
    else:
        lval = 'int tmp'

    if 'int' in real_typ or 'long' in real_typ or 'short' in real_typ:
        if '64' in real_typ or 'long long' in real_typ:
            raise SyntaxError('Cannot convert 64 bit type {t} {qual} ordering'.format(t = real_typ, qual = 'network' if to_network else 'host'))
        elif '32' in real_typ or real_typ == 'int':
            if to_network:
                return '  {l} = htonl({n});\n'.format(n = name, l = lval)
            else:
                return '  {l} = ntohl({n});\n'.format(n = name, l = lval)
        elif '16' in real_typ or 'short' in real_typ:
            if to_network:
                return '  {l} = htons({n});\n'.format(n = name, l = lval)
            else:
                return '  {l} = ntohs({n});\n'.format(n = name, l = lval)
    return None;

def struct_size(s):
    return ' + '.join(['sizeof({t})'.format(t = m[0]) for m in s['members']])

def fun_size(ast, f):
    sizes = ['sizeof(uint8_t)']
    for arg in f['args']:
        if arg[0] in ast['types']:
            sizes.append('sizeof('+arg[0]+')')
        elif any(arg[0] == s['typedef'] for s in ast['structs']):
            sizes.append(struct_size(next(s for s in ast['structs'] if arg[0] == s['typedef'])))
        else:
            add_type(ast, arg[0])
            sizes.append('sizeof('+arg[0]+')')

    return ' + '.join(sizes);

def fun_ret_size(ast, f):
    sizes = ['sizeof(uint8_t)']
    if f['return_t'] in ast['types']:
        sizes.append('sizeof('+f['return_t']+')')
    elif any(f['return_t'] == s['typedef'] for s in ast['structs']):
        sizes.append(struct_size(next(s for s in ast['structs'] if f['return_t'] == s['typedef'])))
    else:
        add_type(ast, f['return_t'])
        sizes.append('sizeof('+f['return_t']+')')

    return ' + '.join(sizes);

def gen_type_decl(t_list):
    def find_slice(s):
        first = s.find('[')
        if first == -1: return None
        last = [p for p, c in enumerate(s) if c == ']'][-1]
        return (first, last + 1)

    s = ' '.join(t_list)
    slic = find_slice(s)
    if slic:
        first = slic[0]
        last = slic[1]
        s = s[:first] + s[last:] + s[first:last]
    return s;

def arg_list(f, full):
    if full:
        return ', '.join(gen_type_decl(arg) for arg in f['args'])
    else:
        return ', '.join(arg[0] for arg in f['args'])
