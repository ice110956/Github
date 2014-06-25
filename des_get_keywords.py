#!usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Patrick'
#根据给定的描述字符串，匹配数据库中的关键词，得到前5个关键词
#输入：keyword文件夹下，包含描述字符串的des.txt文件
#输出：一个列表，包含5个关键词

import MySQLdb
import sys
import logging
import os
import re


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


def data_base():
    """get the data and turn into array and return it
    从数据库中取出关键词，放入列表中返回"""

    conn = sql()
    cur = conn.cursor()
    _sql = 'select d_name from des'
    try:
        cur.execute(_sql)
        r = cur.fetchall()
    except:
        print 'fetch database error'
        sys.exit()
    results = []
    for i in r:
        results.append(i[0])
    return results


def pre_str(st):
    """字符串预处理，变小写，去_,-,'s,多个空格等"""

    res = re.compile(' {2,}')
    st = st.lower()
    st = st.replace("-", ' ')
    st = st.replace("_", ' ')
    st = st.replace("'s", '')
    st = st.replace(',', '')
    st = st.strip()
    st = re.sub(res, ' ', st)
    return st


def get_des(file_path):
    """use the file path to get the description file and turn it into string after pre process
    根据文件路径读取文件，预处理后返回描述字符串"""

    try:
        f = open(file_path).read()
    except:
        print 'file read error'
        sys.exit()
    return pre_str(f)


def simple_match(arr, des):
    """the database array match the description
    return an array contain the match words
    把数据库中的所有关键词依次完全匹配描述
    用post去重，再通过top_five排序，返回前5个关键字"""

    li = []
    for i in arr:
        if des.find(i) != -1:
            li.append(i)
    return top_five(post_pro(li))


def post_pro(li):
    """after match check the key-words and delete the overlaps
    去掉相互包含的字串，返回去重后的结果列表"""

    result = []
    for i in li:
        flag = True
        for j in li:
            if i != j:
                if j.find(i) != -1:
                    flag = False
                    break
        if flag:
            result.append(i)
    return result


def top_five(li):
    """return the top 5 key word
    根据长度排序，返回前5个关键字"""

    li.sort(lambda w1, w2: cmp(len(w2), len(w1)))
    return li[:5]


def main():
    f_name = 'des.txt'
    des = get_des(f_name)
    #从文件中拿到描述
    print 'description: ', des
    words = data_base()
    #从数据库中取出关键词表
    results = simple_match(words, des)
    #匹配算法
    print 'key_word ', results


if __name__ == '__main__':
    #在子文件夹keyword中完成操作
    os.chdir('keyword')
    main()