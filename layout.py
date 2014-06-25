#!usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Patrick'

import os
import MySQLdb
import logging
import sys


def log():
    logging.basicConfig(filename=os.path.join(os.getcwd(), 'log.txt'), level=logging.INFO, filemode='w')


def sql():
    """create a new connection to database
    return the connection"""
    for tr in range(3):
        try:
            conn = MySQLdb.connect(host='192.168.1.108', user='mdx', passwd='medeolinx86', db='layout', port=3306,
                                   charset="utf8")
        except Exception, e:
            logging.error(e)
            sys.exit()
    return conn


def close_sql(cursor, conn):
    """close the connection and cursor of a database"""

    cursor.close()
    conn.close()


def read_layouts():
    """read the layout file in one fold
    return a list contain several dictionary
    and the dictionary's feature 'name' is the layout's name which is the file name"""

    conn = sql()
    cur = conn.cursor()

    _sql = 'select distinct l_id from lay'
    cur.execute(_sql)
    ids = cur.fetchall()

    lay_list = []
    for id in ids:
        _sql = 'select width,g_name,pos_x,pos_y from lay where l_id=%s'
        param = id[0]
        cur.execute(_sql, param)
        items = cur.fetchall()
        l_list = []
        l_list.append(['id', id[0]])
        for item in items:
            l_name = item[1]
            l_l = [item[0], item[2], item[3]]
            l_list.append([l_name, l_l])
        l_dict = dict(l_list)
        lay_list.append(l_dict)
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
    where layout is a dictionary and express is a list
    return the weight and overlap"""

    w = 0
    #记录重叠权值
    overlap = 0
    #记录重叠个数
    overlap_list = []
    #记录重叠的基因
    for e in express:
        e_name = e[0]
        e_high = e[1]
        if lay_out.has_key(e_name):
            #如果有重叠
            w += abs(float(e_high))*abs(float(lay_out[e_name][0]))
            w += 10
            overlap += 1
            overlap_list.append([e_name,  lay_out[e_name][0], lay_out[e_name][1], lay_out[e_name][2]])
        else:
            pass
    result = (lay_out['id'], w, overlap, overlap_list)
    return result


def sort(similar):
    """sort as the weight and get the top 10 layout
    and return"""

    re = sorted(similar, key=lambda s: s[1], reverse=True)
    return re[:9]


if __name__ == '__main__':
    log()
    layout = read_layouts()
    express = read_express()
    res = []
    for l in layout:
        res.append(similarity(l, express))

    top = sort(res)
    output = open('result.txt', 'w')
    for t in top:
        #print t
        output.write(str(t[0]) + '\t')
        output.write(str(t[1]) + '\t')
        output.write(str(t[2]) + '\n')
        for gene in t[3]:
            output.write(str(gene[0] + ' ' + gene[1] + ' ' + gene[2] + ' ' + gene[3]))
            output.write('\n')
    output.close()


