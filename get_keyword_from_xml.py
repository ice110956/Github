#!usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Patrick'
#读取xml中的内容，提取关键字‘**Name’,写入数据库中，配合程序match.py用于匹配
#输入：keyword文件夹下的XML文件，无输入
#输出：写入database，格式：des（id，d_name）无输出

import os
import re
import MySQLdb
import logging
import sys


res = re.compile(' {2,}')


def log():
    logging.basicConfig(filename=os.path.join(os.getcwd(), 'log.txt'), level=logging.INFO, format='%(asctime)s %(thread)d %(funcName)s %(levelname)s %(message)s', filemode='w')


def sql():
    """create a new connection to database
    return the connection"""
    for tr in range(3):
        try:
            conn = MySQLdb.connect(host='192.168.1.108', user='mdx', passwd='medeolinx86', db='des_data', port=3306,
                                   charset="utf8")
        except Exception, e:
            logging.error(e)
            sys.exit()
    return conn


def pro_str(st):
    """字符串预处理，变小写，去_,-,'s,多个空格等"""

    st = st.lower()
    st = st.replace("-", ' ')
    st = st.replace("_", ' ')
    st = st.replace("'s", '')
    st = st.replace(",", '')
    st = st.strip()
    st = re.sub(res, ' ', st)
    return st


def get_xml(f_name, s):
    """get the xml use readline()
    f_name is the name of the fiel
    s is the key_word"""

    file_name = f_name + '.xml'
    f = open(file_name)
    res_0 = re.compile(s + '>')
    res_1 = re.compile('</.*?>')
    li = []
    while True:
        name = f.readline()
        if name:
            if res_0.search(name):
                #print name
                if not res_1.search(name):
                    name = f.readline().strip().replace('<String>', '').replace('</String>', '').replace('&amp; ', '')
                    li.append(name)
                    f.readline()
                else:
                    res_2 = re.compile('<.*?>')
                    name = re.sub(res_2, '', name.strip()).replace('&amp; ', '')
                    li.append(name)
        else:
            break
    f.close()

    #字符串处理，去重复等
    se = set(li)
    li = [pro_str(i) for i in se]

    #插入数据库
    conn = sql()
    cur = conn.cursor()
    _sql = 'insert into des(d_name) values(%s)'
    param = []
    for j in li:
        param.append((j,))
    try:
        cur.executemany(_sql, param)
        conn.commit()
    except:
        print 'inser into database error'

if __name__ == '__main__':
    os.chdir('keyword')
    f_list = ['pa2014', 'desc2014', 'qual2014', 'supp2014']
    s = 'Name'
    #s 是要匹配的字符
    l = f_list[1]
    get_xml(l, s)
    print l + 'done!'