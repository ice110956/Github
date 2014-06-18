#!usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Patrick'

import os
import re


def vs(num):
    """read the -1.txt and 1.txt files
    and get the info into the result.txt"""

    file_list = ['-1.txt', '1.txt']
    r = re.compile(r'^\d+\. .*? ')
    res = re.compile('\s$')
    gen_list = []
    for f in file_list:
        fi = open(f)
        fi_t = fi.read().splitlines()
        count = 1
        for text in fi_t:
            if r.match(text):
                s = r.match(text).group(0).split('. ')
                s[1] = res.sub('', s[1])
                if s[1] == 'Co-expression':
                    continue
                print s
                if s[1] not in gen_list:
                    count += 1
                    gen_list.append(s[1])
            if count > num:
                break
        fi.close()
    fi = open('result.txt', 'w+')
    count = 1
    tt = '\t-1\n\r'
    for gen in gen_list:
        st = gen + tt
        fi.writelines(st)
        count += 1
        if count > num:
            count = 1
            fi.writelines('\n\r')
            tt = '\t1\n\r'
    fi.close()

if __name__ == '__main__':
    os.chdir('vs')
    n = 100
    vs(n)