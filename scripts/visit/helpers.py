""" Type helping """

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
            ast['types'].add(arg[0])
            sizes.append('sizeof('+arg[0]+')')

    return ' + '.join(sizes);

def fun_ret_size(ast, f):
    sizes = ['sizeof(uint8_t)']
    if f['return_t'] in ast['types']:
        sizes.append('sizeof('+f['return_t']+')')
    elif any(f['return_t'] == s['typedef'] for s in ast['structs']):
        sizes.append(struct_size(next(s for s in ast['structs'] if f['return_t'] == s['typedef'])))
    else:
        ast['types'].add(f['return_t'])
        sizes.append('sizeof('+f['return_t']+')')

    return ' + '.join(sizes);

def arg_list(f, full):
    if full:
        return ', '.join(' '.join(arg) for arg in f['args'])
    else:
        return ', '.join(arg[0] for arg in f['args'])
