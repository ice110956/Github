# _*_ coding:utf-8 _*_
__author__ = 'Patrick'


import socket
import threading
import sys
import simplejson


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


def new_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('localhost',3368))
        #绑定本地地址,端口3368
        print "get the service"
    except:
        print("Server is unavailable")
        sys.exit()
    ex = read_express()
    print ex
    json_object = simplejson.dumps(ex)
    sock.send(json_object)
    json_recv = sock.recv(1024000)
    print json_recv
    print type(json_recv)
    print simplejson.loads(json_recv)
    print type(simplejson.loads(json_recv))
    sock.close()
    return


if __name__ == '__main__':
    new_client()
    print "it is done!"