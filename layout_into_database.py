#!usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Patrick'
#把layout文件写入database中，database格式为两个表，info（id,name,user）,lay(l_id,pos_x,pos_y,width,g_name)
#输入：.txt的layout文件，文件名为layout名
#输出：写入数据库中，无输出


import MySQLdb
import os
import logging
import sys


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


if __name__ == '__main__':
    conn = sql()
    cur = conn.cursor()
    path = 'layout'
    files = os.listdir(path)
    lay_list = []
    id = 1
    for f in files:
        file_name = open(path + '/' + f)
        print f
        l_list = []
        while 1:
            line = file_name.readline()
            if not line:
                break
            l_name = line.split()[0]
            l_width = line.split()[2]
            l_x = line.split()[1]
            l_y = line.split()[3]
            l_list.append([l_name, l_width, l_x, l_y])
        file_name.close()

        _sql = "insert into info (l_id,l_name,l_user) values(%s,%s,%s)"
        param = (int(id), f.replace('.txt', ''), 'patrick')
        try:
            cur.execute(_sql, param)
            conn.commit()
        except:
            print 'insert into database error'
            continue
        for item in l_list:
            _sql = "insert into lay (l_id,pos_x,pos_y,width,g_name) values(%s,%s,%s,%s,%s)"
            param = (int(id), item[2], item[3], item[1], item[0])
            print param
            try:
                cur.execute(_sql, param)
            except:
                print "insert error"
                continue
            conn.commit()
        id += 1
    close_sql(cur, conn)