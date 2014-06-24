# _*_ coding:utf-8 _*_
__author__ = 'Patrick'

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
    res = re.compile(s + '>')
    res_1 = re.compile('</.*?>')
    li = []
    while True:
        name = f.readline()
        if name:
            if res.search(name):
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
    se = set(li)
    print "process..."
    li = [pro_str(i) for i in se]
    print "over"
    conn = sql()
    cur = conn.cursor()
    _sql = 'insert into des(d_name) values(%s)'
    param = []
    for j in li:
        param.append((j,))
    cur.executemany(_sql, param)
    conn.commit()
       # try:
         #   cur.execute(_sql, param)
        #    conn.commit()
       # except:
          # logging.error("insert error")

if __name__ == '__main__':
    os.chdir('xml')
    f_list = ['pa2014', 'desc2014', 'qual2014', 'supp2014']
    s = 'Name'
    #for l in f_list:
    #s = 'DescriptorName'
    #get_xml('desc2014', s)
    l = f_list[1]
    get_xml(l, s)
    print l + 'done!'