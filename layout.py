# -*- coding: utf-8 -*-
__author__ = 'patrick'

import os


def read_layouts():
    """read the layout file in one fold
    return a list contain several dictionary
    and the dictionary's feature 'name' is the layout's name which is the file name"""

    path = 'layout'
    files = os.listdir(path)
    lay_list = []
    for f in files:
        file_name = open(path + '/' + f)
        print f
        l_list = []
        l_list.append(['name', f])
        while 1:
            line = file_name.readline()
            if not line:
                break
            l_name = line.split()[0]
            l_width = line.split()[2]
            l_list.append([l_name, l_width])
        l_dict = dict(l_list)
        #print l_dict
        lay_list.append(l_dict)
        file_name.close()
    return lay_list


def read_express():
    """read a express and return a list"""

    express = 'express/GeneExpression2.txt'
    en_ex = []
    file_name = open(express)
    while 1:
        line = file_name.readline()
        if not line:
            break
        e_name = line.split()[0]
        e_high = line.split()[1]
        en_ex.append([e_name, e_high])
    file_name.close()
    return en_ex


def similarity(lay_out,express):
    """computer the similarity between a layout and a express
    where layout is a dict and express is a list
    return the weight and overlap"""

    w = 0
    overlap = 0
    for e in express:
        e_name = e[0]
        e_high = e[1]
        if lay_out.has_key(e_name):
            w += abs(float(e_high))
            w += abs(float(lay_out[e_name]))
            w += 10
            overlap += 1
        else:
            pass
    result = (lay_out['name'].replace('.txt', ''), w, overlap)
    return result


def sort(similar):
    """sort as the weight and get the top 10 layout
    and return"""

    re = sorted(similar, key=lambda s: s[1], reverse=True)
    return re[:9]


if __name__ == '__main__':
    layout = read_layouts()
    express = read_express()
    res = []
    for l in layout:
        res.append(similarity(l, express))

    top = sort(res)
    output = open('result.txt', 'w')
    for t in top:
        print t
        output.write(str(t[0]) + '\t')
        output.write(str(t[1]) + '\t')
        output.write(str(t[2]) + '\n')
    output.close()


