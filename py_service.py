# _*_ coding:utf-8 _*_
__author__ = 'Patrick'


import socket
import threading
import sys
import simplejson
import logging
import os
import MySQLdb


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
    and the dictionary's feature 'name' is the layout's name which is the file name
    and the 'user' is the layout's user"""

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

        _sql = 'select l_name,l_user from info where l_id=%s'
        cur.execute(_sql, param)
        name = cur.fetchall()
        for t in name:
            l_list.append(['name', t[0]])
            l_list.append(['user', t[1]])

        for item in items:
            l_name = item[1]
            l_l = [item[0], item[2], item[3]]
            l_list.append([l_name, l_l])
        l_dict = dict(l_list)
        lay_list.append(l_dict)
    close_sql(cur, conn)
    return lay_list


def similarity(lay_out, express):
    """computer the similarity between a layout and a express
    where layout is a dict and express is a list
    return the weight and overlap"""

    w = 0
    overlap = 0
    overlap_list = []
    for e in express:
        e_name = e[0]
        e_high = e[1]
        if lay_out.has_key(e_name):
            w += abs(float(e_high))*abs(float(lay_out[e_name][0]))
            w += 10
            overlap += 1
            overlap_list.append([e_name,  lay_out[e_name][0], lay_out[e_name][1], lay_out[e_name][2]])
        else:
            pass
    length = len(express)
    result = (lay_out['name'], lay_out['user'], w, overlap/length, overlap_list)
    return result


def sort(similar):
    """sort as the weight and get the top 10 layout
    and return"""

    re = sorted(similar, key=lambda s: s[1], reverse=True)
    return re[:9]


class Th(threading.Thread):
    def __init__(self, layout, express):
        threading.Thread.__init__(self)
        self.layout = layout
        self.express = express

    def run(self):
        res = []
        for l in self.layout:
            res.append(similarity(l, self.express))
        top = sort(res)
        print type(top)
        print top


def new_service():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('localhost', 3368))
        sock.listen(100)
        print "bing 3368,ready to use"
    except:
        print("Server is already running,quit")
        sys.exit()
    layout = read_layouts()
    while True:
        connection, address = sock.accept()
        print "Got connection from ", address
        buf = connection.recv(10240)
        express = simplejson.loads(buf)
        t = Th(layout, express)
        t.start()
        print 'new thread for client ...'


if __name__ == '__main__':
    new_service()