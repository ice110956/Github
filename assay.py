#!usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Patrick'
#多线程，下载https://www.assaydepot.com/中的内容
#包括目录，services，provider，s-p对等，写入数据库中
#数据库的模板为文件mydb.sql

import MySQLdb
import sys
import urllib2
import re
import urllib
import logging
from bs4 import BeautifulSoup
import os
import threading
import time


def log():
    logging.basicConfig(filename=os.path.join(os.getcwd(), 'log.txt'), level=logging.INFO, format='%(asctime)s %(thread)d %(funcName)s %(levelname)s %(message)s', filemode='w')


def open_url(url):
    """尝试三次链接到特定的URL，成功返回response，否者返回False"""

    flag = False
    for tr in range(3):
        try:
            response = urllib2.urlopen(url)
            flag = True
        except:
            logging.info("open url " + url + 'fail and retry ' + str(tr))
            time.sleep(1)
            flag = False
            #get url error and wait 1s
            continue
        break
    if flag is False:
        return False
    else:
        return response


def translate(text):
    """翻译函数，English 到 Chinese"""

    values = {'client': 't', 'sl': 'en', 'tl': 'zh-CN', 'hl': 'zh-CN', 'ie': 'UTF-8', 'oe': 'UTF-8', 'prev': 'btn',
              'ssel': '0', 'tsel': '0', 'q': text}
    url = "http://translate.google.cn/translate_a/t"
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    browser = "Mozilla/5.0 (Windows NT 6.1; WOW64)"
    req.add_header('User-Agent', browser)
    flag = False
    for tr in range(3):
        try:
            response = urllib2.urlopen(req)
            flag = True
        except:
            logging.info("google translate is unreachable and try again")
            time.sleep(1)
            #等待一秒继续尝试连接
            flag = False
            #get url error and wait 1s
            continue
        break
    if flag is False:
        logging.error("google translate is unreachable!")
        return ""
    get_page = response.read()
    text_page = re.search('\[\[.*?\]\]', get_page).group()
    text_list = []
    rex = re.compile(r'\[\".*?\",')
    re_find = re.findall(rex, text_page)
    #去除多余的字符
    if len(re_find) != 0:
        for item in re_find:
            item = item.replace('[', "")
            item = item.replace('",', "")
            item = item.replace('"', "")
            text_list.append(item)
        text_result = "".join(text_list)
    else:
        text_result = ""
    return text_result


def sql():
    """连接到指定数据库，返回connection"""

    for tr in range(3):
        try:
            conn = MySQLdb.connect(host='192.168.1.108', user='mdx', passwd='medeolinx86', db='mydb', port=3306,
                                   charset="utf8")
        except Exception, e:
            logging.error(e)
            sys.exit()
    return conn


def close_sql(cursor, conn):
    """关闭数据库的connection"""

    cursor.close()
    conn.close()


def get_services_description(url, cur, conn, category_id):
    """to get a service-page 's description and insert into database
    request param of url and database connect and category_id
    return the services id for further use
    得到service的描述并插入数据库，成功返回service id，失败返回-1"""

    logging.info(url)
    response = open_url(url)
    if response is False:
        logging.error("can not open url " + url)
        return -1
    page = response.read()
    soup = BeautifulSoup(page)
    services_name = soup.find("h1").text.encode('utf-8')
    services = soup.find("div", id="ware_description")
    services_description = services.find_all("p")
    des = []
    for description in services_description:
        des.append(description.text)
    des_str = "".join(des).encode('utf-8')
    des_str_cn = translate(des_str)
    _sql = 'insert into service(s_name,s_description, s_description_cn, c_id) values(%s,%s,%s,%s)'
    param = (services_name, des_str, des_str_cn, long(category_id))
    try:
        cur.execute(_sql, param)
        conn.commit()
    except:
        logging.error("insert service error")

    _sql = 'select s_id from service where s_name=%s AND c_id=%s'
    param = (services_name, long(category_id))
    try:
        cur.execute(_sql, param)
    except:
        logging.error("get services' id error")
    results = cur.fetchall()
    services_id = -1
    if len(results) != 0:
        for rec in results:
            services_id = rec[0]
    return services_id


def get_provider_description(url, cur, conn):
    """to get one provider page 's description and insert into database
    request param of url and database connect and category_id
    return provider id
    if error return -1
    得到每个provider的描述，并插入数据库。成功则返回p-id，失败返回-1"""

    logging.info(url)
    response = open_url(url)
    if response is False:
        logging.error("can not open url " + url)
        return -1
    page = response.read()
    soup = BeautifulSoup(page)
    provider_name = soup.find("h1").text.encode('utf-8')

    _sql = 'select p_name,p_id from provider where p_name =%s'
    param = provider_name
    is_exist = cur.execute(_sql, param)
    if is_exist == 0:
        #insert description
        provider = soup.find("div", id="provider_description")
        provider_description = provider.find_all("p")
        des = []
        for description in provider_description:
            des.append(description.text)
        des_str = "".join(des).encode('utf-8')

        details = soup.find("div", class_="span3").find("div", class_="well")
        det_str = details.text.encode('utf-8')
        det_str = det_str.replace('\n', ' ')

        _sql = 'insert into provider(p_name,p_description,p_description_cn,p_detail) values(%s,%s,%s,%s)'
        des_str_cn = translate(des_str)
        param = (provider_name, des_str, des_str_cn, det_str)
        try:
            cur.execute(_sql, param)
            conn.commit()
        except:
            logging.info("overlap insert provider" + provider_name)

        #return provider id
    _sql = 'select p_id from provider where p_name=%s'
    param = provider_name
    cur.execute(_sql, param)
    results = cur.fetchall()
    provider_id = -1
    if len(results) != 0:
        for rec in results:
            provider_id = rec[0]
    else:
        logging.error("no such provider ,insert error or select error")
    #print provider_id
    return provider_id


def get_providers(url, cur, conn, id_services):
    """for each services to get the providers
    insert the provider and then link into table provider and link in the database
    以services 为单位，得到所有的providers，并且把link和provider都插入到数据库中"""

    logging.info(url)
    response = open_url(url)
    if response is False:
        logging.error("can not open url " + url)
        return
    page = response.read()
    soup = BeautifulSoup(page)
    span = soup.find("div", class_="span3")
    ul = span.find("ul")
    providers = ul.find_all("li")
    url_list = []
    if len(providers) != 0:
        for p in providers:
            #获得此services的provider列表
            url_list.append('https://www.assaydepot.com' + p.a['href'].encode('utf-8'))

        #插入provider到数据库，并返回id，失败则返回-1
        provider_id = []
        for url_provider in url_list:
            p_id = get_provider_description(url_provider, cur, conn)
            if p_id != -1:
                provider_id.append(p_id)

        #插入link(service-provider)
        _sql = 'insert into link(s_id, p_id) values(%s,%s)'
        for id in provider_id:
            #print "start to insert link"
            logging.info("start to insert link")
            param = (long(id_services), long(id))
            try:
                cur.execute(_sql, param)
                conn.commit()
            except:
                logging.error("insert link error " + str(id_services) + str(id))
                continue


class C2(threading.Thread):
    """二级目录子线程，处理每个二级目录"""

    def __init__(self, t_name, category_1, category_2, category_3):
        threading.Thread.__init__(self)
        self.t_name = t_name
        #这里的三级目录是一个列表，包括此二级目录的所有三级子目录
        self.category_3 = category_3
        self.category_2 = category_2
        self.category_1 = category_1

    def run(self):
        """category 2 thread function,in each second category"""

        conn = sql()
        cur = conn.cursor()
        if len(self.category_3) == 0:
            for c3 in self.category_3:
                #处理所有此二级目录下的三级目录
                _sql = 'insert into category(c_name,c_category_1,c_category_2) values(%s,%s,%s)'
                param = (c3.a.text.encode('utf-8'), self.category_1, self.category_2)
                #插入数据库此三级目录
                try:
                    cur.execute(_sql, param)
                    conn.commit()
                except:
                    logging.error("insert category error " + c3.a.text.encode('utf-8') + ' ' + self.category_1 + ' ' + self.category_2)
                    continue

                _sql = 'select c_id from category where c_name=%s AND c_category_1=%s AND c_category_2=%s'
                param = (c3.a.text.encode('utf-8'), self.category_1, self.category_2)
                cur.execute(_sql, param)
                results = cur.fetchall()
                category_id = 0
                #插入后查找得到的自增长三级目录id
                if len(results) != 0:
                    for rec in results:
                        category_id = rec[0]
                    url_3 = "https://www.assaydepot.com" + c3.a['href'].encode('utf-8')
                    logging.info(url_3)
                    response = open_url(url_3)
                    if response is False:
                        logging.error("can not open url " + url_3)
                        continue
                        #无法打开此目录则继续下一个目录
                    page = response.read()
                    soup = BeautifulSoup(page)
                    url_services = []
                    page_num = 0
                    while True:
                        #每个三级目录下有多页的services，一直翻页直到最后
                        page_num += 1
                        logging.info("in page " + str(page_num))
                        #get the services per page until no page
                        del url_services
                        url_services = []
                        items = soup.find_all("h4", class_="media-headig")
                        if len(items) == 0:
                            logging.info("find no services")
                            break
                        else:
                            logging.info("find services")
                            for item in items:
                                url_services.append("http://www.assaydepot.com" + item.a['href'].encode('utf-8'))
                                #获得本页的所有services

                        if len(url_services) != 0:
                            for url in url_services:
                                logging.info("insert services!")
                                id_services = get_services_description(url, cur, conn, category_id)
                                if id_services == -1:
                                    #service插入失败，继续下一个
                                    continue
                                #取得services的描述并插入数据库中
                                get_providers(url, cur, conn, id_services)
                                #取得service包含的providers

                        next_page = soup.find("li", class_="next next_page ")
                        #翻页
                        if next_page is not None:
                            logging.info("go to next page")
                            url_next = "http://www.assaydepot.com" + next_page.a['href'].encode('utf-8')
                            response = open_url(url_next)
                            if response is False:
                                logging.error("unable to open url " + url_next)
                                break
                            page = response.read()
                            soup = BeautifulSoup(page)
                        else:
                            logging.info("no next page,out")
                            break
                else:
                    logging.error("search category error")
                    continue

        close_sql(cur, conn)
        logging.info(self.t_name + "done!")


class C1(threading.Thread):
    """第一层线程，处理一个一级大目录，一共可有5个这样的目录,如 biology"""

    def __init__(self, t_name, category_1):
        threading.Thread.__init__(self)
        self.t_name = t_name
        self.category_1 = category_1

    def run(self):
        """thread function in category1"""

        url = "https://www.assaydepot.com/better_categories/" + self.category_1
        #print(url)
        logging.info(url)
        response = open_url(url)
        if response is False:
            logging.error("can not open url " + url)
            return
        page = response.read()
        soup = BeautifulSoup(page)
        items = soup.find_all("div", class_="well")
        thread_id = 1
        threads = []
        if len(items) != 0:
            #每个c2表示一个二级目录，每个二级目录一个二级子线程处理
            for c2 in items:
                category_2 = c2.find('h3').text.encode('utf-8')
                category_3 = c2.find_all("li")
                thread_name_1 = "Thread_" + self.category_1 + '_' + category_2 + '_' + str(thread_id)
                thread_id += 1
                try:
                    #处理二级目录的子线程
                    tt = C2(thread_name_1, self.category_1, category_2, category_3)
                except:
                    logging.info("Unable to open thread" + thread_name_1)
                    continue
                tt.start()
                threads.append(tt)

        # 等待所有线程完成
        for t in threads:
            t.join()
        print self.t_name + " done!"


if __name__ == "__main__":

    log()
    category_list = ['chemistry', 'dmpk', 'pharmacology', 'toxicology', 'biology']
    thread_id = 1
    c1 = category_list[0]
    #处理的一级目录,由于biology这个目录处理特别慢，放到最后
    #每个一级目录一个主线程
    thread_name = "Thread" + '_' + c1 + '_' + str(thread_id)
    try:
        t = C1(thread_name, c1)
    except:
        logging.error("Error unable to start thread")
        sys.exit()
    t.start()
    print thread_name
    t.join()