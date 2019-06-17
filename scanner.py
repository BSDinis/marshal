#!/usr/bin/env python3
""" Marshal Lexer """

import sys
import re

def scan(cin):
    def rem_comments(text):
        """ remove the comments from text """
        def rem_c_comments(text):
            begin_comment_idx = list();
            last_comment_idx = list();
            stripped = str();
            nest = 0
            for idx, ch in enumerate(text):
                if text[idx: idx + 2] == '/*':
                    begin_comment_idx.append(idx);
                    nest += 1
                elif text[idx: idx + 2] == '*/':
                    if nest == 1:
                        last_comment_idx.append(idx + 2);
                    else:
                        begin_comment_idx.pop();
                    nest -= 1

            base = 0

            for i in range(len(last_comment_idx)):
                stripped += text[base: begin_comment_idx[i]];
                base = last_comment_idx[i] + 1;

            return stripped + text[base:];

        def rem_line_comments(text):
            return re.sub('//.*', '', text);

        return rem_line_comments(rem_c_comments(text));

    def group_braces(tokens):
        grouped = list();
        begin_brace = list();
        last_brace = list();
        curr_list = list();
        for tok in tokens:
            if tok == '}':
                grouped += [curr_list];
                curr_list = [];
            elif tok == '{':
                grouped += curr_list
                curr_list = [];
            else:
                curr_list += [tok];

        if curr_list: grouped += curr_list
        return grouped;

    def make_sentences(lists):
        sentences = list();
        sentence = list();
        for el in lists:
            if isinstance(el, list):
                sentence += [make_sentences(el)]
            else:
                if el == ';':
                    sentences += [sentence];
                    sentence = list();
                else:
                    sentence += [el];

        return sentences

    text = rem_comments(cin.read()).replace('\n', '');
    text = text.replace('}', ' } ');
    text = text.replace('{', ' { ');
    text = text.replace(',', ' , ');
    text = text.replace(';', ' ; ');
    sentences = text.split(' ')
    sentences = [s for s in sentences if s != '']
    sentences = group_braces(sentences);
    return make_sentences(sentences);

if __name__ == '__main__':
    print(scan(sys.stdin))
    sys.exit(0)

