""" Marshal Compiler """

import sys
import argparse
import os

import lex.scanner as scanner
import syntax.ast as ast
import visit.visit_c_prot as visit_c_prot
import visit.visit_c_header as visit_c_header
import visit.visit_c_code as visit_c_code

def options():
    def get_ext_out(arg, files, has_input, print_all, prot, ext):
        do_print = (arg == False and print_all) or arg != False;
        if do_print or prot:
            if has_input:
                if arg == None or arg == False:
                    return [open(os.path.splitext(f)[0]+'.'+ext, "w") for f in files]
                else:
                    return [open(arg, "w")] * len(files)
            else:
                if arg == None or arg == False:
                    return [sys.stdout] * len(files)
                else:
                    return [open(arg, "w")] * len(files)
        return [None for _ in files]

    parser = argparse.ArgumentParser(description='Marshal Compiler')
    parser.add_argument('code', metavar='interface.m', nargs='*', help='marshal source files')
    parser.add_argument('-H', metavar='header.h', nargs='?', default=False, help='generate C header code; optionally generates a specific .h file')
    parser.add_argument('-c', metavar='source.c', nargs='?', default=False, help='generate C source code; optionally generates a specific .c file')
    parser.add_argument('-p', action='store_true', help='generate function prototypes for the C file')
    parser.add_argument('-n', metavar='namespace', nargs=1, default=None, help='prefix all public facing functions with namespace_ ; the default is the name of the file (minus extension)')

    args = parser.parse_args()
    in_files = [open(c, "r") for c in args.code]
    print_all = all(arg == False for arg in [args.c, args.H, args.p])
    has_input = len(in_files) != 0;
    if not has_input:
        in_files = [sys.stdin]
        args.code += ['']

    headers = get_ext_out(args.H, args.code, has_input, print_all, False, 'h')
    codes   = get_ext_out(args.c, args.code, has_input, print_all, args.p, 'c')
    what_to_print = 0; # print nothing
    if (args.p and args.c) or print_all:
        what_to_print = 3
    elif args.p:
        what_to_print = 2;
    elif args.c != False:
        what_to_print = 1;


    if args.n == None:
        if args.code:
            namespaces = [f.split('/')[-1].split('.')[0]+'_' for f in args.code]
        else:
            namespaces = ['' for _ in args.code]
    else:
        namespaces = [args.n[0] + '_' for n in args.code];

    return in_files, headers, codes, what_to_print, namespaces

def main():
    """ main compiler routine """
    cins, headers, codes, what_to_print, namespaces = options();
    for cin, header, code, namespace in zip(cins, headers, codes, namespaces):
        astree = ast.make_ast(scanner.scan(cin));
        if header:
            if header.name != '<stdout>':
                print(f'/**\n * {header.name}\n */'+'\n', file=header)
                print('#pragma once\n', file=header)

            print('/***\n * headers\n */', file = header)
            print(visit_c_header.generate(astree, header.name != '<stdout>', namespace), file=header);
        if code:
            if header and header.name != '<stdout>':
                print(f'/**\n * {code.name}\n */'+'\n', file=code)
                print(f'#include "{header.name}"', file = code)
                print('#include <string.h>', file = code)
                print('\n', file = code)
            if what_to_print in [2, 3]:
                print('/***\n * protoyped declarations\n */', file = code)
                print(visit_c_prot.generate(astree, namespace), file = code);
            if what_to_print in [1, 3]:
                print('/***\n * code\n */', file = code)
                print(visit_c_code.generate(astree, namespace), file = code);

    return 0

if __name__ == '__main__':
    sys.exit(main());

