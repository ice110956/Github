# _*_ coding:utf-8 _*_
__author__ = 'Patrick'


import socket
import threading
import sys
import simplejson
import logging
import os
import MySQLdb
import base64
import hashlib
import struct


# ====== config ======
HOST = 'localhost'
PORT = 3368
MAGIC_STRING = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
HANDSHAKE_STRING = "HTTP/1.1 101 Switching Protocols\r\n" \
                   "Upgrade:websocket\r\n" \
                   "Connection: Upgrade\r\n" \
                   "Sec-WebSocket-Accept: {1}\r\n" \
                   "WebSocket-Location: ws://{2}/chat\r\n" \
                   "WebSocket-Protocol:chat\r\n\r\n"
Hash = ['111', '222', '333']


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
    lap = str(overlap) + '(' + str(round(1.0*overlap/length*100)) + '%)'
    result = (lay_out['name'], lay_out['user'], w, lap, overlap_list)
    #result是元组
    return result


def sort(similar):
    """sort as the weight and get the top 10 layout
    and return"""

    re = sorted(similar, key=lambda s: s[1], reverse=True)
    return re[:9]


class Th(threading.Thread):
    """the thread class to handle the connect
    receive the express and send the sorted retult"""

    def __init__(self, connection, layout):
        threading.Thread.__init__(self)
        self.layout = layout
        self.con = connection

    def run(self):
        while True:
            try:
                hash = self.recv_data(1024)
                if hash not in Hash:
                    break
                buf = self.recv_data(102400)
                buf = buf[9:len(buf)-2]
                line = buf.split(r"\r\n")
                express = []
                for l in line:
                    item = l.split(r'\t')
                    express.append(item)
                #express = simplejson.loads(buf)
                print 'it is express', express
                print len(express)
                if len(express) == 0:
                    print "recv nothing"
                    continue
            except socket.timeout:
                print 'rec time out'
                continue
            res = []
            for l in self.layout:
                res.append(similarity(l, express))
            top = sort(res)
            #top为列表，其中元素为元组
            try:
                self.send_data(simplejson.dumps(top))
                print simplejson.dumps(top)
            except:
                print "send result time out"
        self.con.close()

    def recv_data(self, num):
        try:
            all_data = self.con.recv(num)
            if not len(all_data):
                return False
        except:
            return False
        else:
            code_len = ord(all_data[1]) & 127
            if code_len == 126:
                masks = all_data[4:8]
                data = all_data[8:]
            elif code_len == 127:
                masks = all_data[10:14]
                data = all_data[14:]
            else:
                masks = all_data[2:6]
                data = all_data[6:]
            raw_str = ""
            i = 0
            for d in data:
                raw_str += chr(ord(d) ^ ord(masks[i % 4]))
                i += 1
            return raw_str

    # send data
    def send_data(self, data):
        if data:
            data = str(data)
        else:
            return False
        token = "\x81"
        length = len(data)
        if length < 126:
            token += struct.pack("B", length)
        elif length <= 0xFFFF:
            token += struct.pack("!BH", 126, length)
        else:
            token += struct.pack("!BQ", 127, length)
        data = '%s%s' % (token, data)
        self.con.send(data)
        return True


    # handshake
def handshake(con):
    headers = {}
    shake = con.recv(1024)

    if not len(shake):
        return False

    header, data = shake.split('\r\n\r\n', 1)
    for line in header.split('\r\n')[1:]:
        key, val = line.split(': ', 1)
        headers[key] = val

    if 'Sec-WebSocket-Key' not in headers:
        print ('This socket is not websocket, client close.')
        con.close()
        return False

    sec_key = headers['Sec-WebSocket-Key']
    res_key = base64.b64encode(hashlib.sha1(sec_key + MAGIC_STRING).digest())

    str_handshake = HANDSHAKE_STRING.replace('{1}', res_key).replace('{2}', HOST + ':' + str(PORT))
    print str_handshake
    con.send(str_handshake)
    return True


def new_service():
    """start a service socket and listen
    when coms a connection, start a new thread to handle it"""

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('localhost', 3368))
        sock.listen(1000)
        #链接队列大小
        print "bind 3368,ready to use"
    except:
        print("Server is already running,quit")
        sys.exit()
    layout = read_layouts()

    while True:
        connection, address = sock.accept()
        #返回元组（socket,add），accept调用时会进入waite状态
        print "Got connection from ", address
        if handshake(connection):
            print "handshake success"
            try:
                t = Th(connection, layout)
                t.start()
                print 'new thread for client ...'
            except:
                print 'start new thread error'
                connection.close()


if __name__ == '__main__':
    new_service()