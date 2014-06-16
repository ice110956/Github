#!usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Patrick'

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
    """translate English to Chinese"""

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
    """create a new connection to database
    return the connection"""
    for tr in range(3):
        try:
            conn = MySQLdb.connect(host='192.168.1.108', user='mdx', passwd='medeolinx86', db='mydb', port=3306,
                                   charset="utf8")
        except Exception, e:
            logging.error(e)
            sys.exit()
    return conn


def close_sql(cursor, conn):
    """close the connection and cursor of a database"""

    cursor.close()
    conn.close()


def get_services_description(url, cur, conn, category_id):
    """to get a service-page 's description and insert into database
    request param of url and database connect and category_id
    return the services id for further use"""

    logging.info(url)
    response = open_url(url)
    if response is False:
        logging.error("can not open url " + url)
        return 0
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
    services_id = 0
    if len(results) != 0:
        for rec in results:
            services_id = rec[0]
    return services_id


def get_provider_description(url, cur, conn, thread_name):
    """to get one provider page 's description and insert into database
    request param of url and database connect and category_id
    return provider id
    if error return -1"""

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
    #print provider_id
    return provider_id


def get_provider(url, cur, conn, id_services, thread_name):
    """for each services to get the providers
    insert the provider and then link into table provider and link in the database"""

    #print(url)
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
            url_list.append('https://www.assaydepot.com' + p.a['href'].encode('utf-8'))

        #insert to provider and get its id
        provider_id = []
        for url_provider in url_list:
            p_id = get_provider_description(url_provider, cur, conn, thread_name)
            if p_id != -1:
                provider_id.append(p_id)
        #still need un overlap process

        #insert link
        _sql = 'insert into link(s_id, p_id) values(%s,%s)'
        for id in provider_id:
            #print "start to insert link"
            logging.info("start to insert link")
            param = (long(id_services), long(id))
            try:
                cur.execute(_sql, param)
                conn.commit()
            except:
                #print 'insert link error'
                logging.error("insert link error " + str(id_services) + str(id))
                continue


class C2(threading.Thread):
    def __init__(self, t_name, category_1, category_2, category_3):
        threading.Thread.__init__(self)
        self.t_name = t_name
        self.category_3 = category_3
        self.category_2 = category_2
        self.category_1 = category_1

    def run(self):
        """category 2 thread function,in each second category"""

        conn = sql()
        cur = conn.cursor()
        if self.category_3 is not None:
            for c3 in self.category_3:
                #for each second category
                _sql = 'insert into category(c_name,c_category_1,c_category_2) values(%s,%s,%s)'
                param = (c3.a.text.encode('utf-8'), self.category_1, self.category_2)
                try:
                    cur.execute(_sql, param)
                    conn.commit()
                except:
                    #print 'insert category error'
                    logging.error("insert category error " + c3.a.text.encode('utf-8') + ' ' + self.category_1 + ' ' + self.category_2)
                    continue
                    #error
                _sql = 'select c_id from category where c_name=%s AND c_category_1=%s AND c_category_2=%s'
                param = (c3.a.text.encode('utf-8'), self.category_1, self.category_2)
                #get each third category and insert into database
                cur.execute(_sql, param)
                results = cur.fetchall()
                category_id = 0
                if len(results) != 0:
                    for rec in results:
                        category_id = rec[0]
                    url_3 = "https://www.assaydepot.com" + c3.a['href'].encode('utf-8')
                    logging.info(url_3)
                    response = open_url(url_3)
                    if response is False:
                        logging.error("can not open url " + url_3)
                        continue
                    page = response.read()
                    soup = BeautifulSoup(page)
                    #get the third category page soup
                    url_services = []
                    page_num = 0
                    while True:
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
                                #print "serivices url is " + "http://www.assaydepot.com" + item.a['href']

                        if len(url_services) != 0:
                            for url in url_services:
                                logging.info("insert services!")
                                id_services = get_services_description(url, cur, conn, category_id)
                                get_provider(url, cur, conn, id_services, self.t_name)

                        next_page = soup.find("li", class_="next next_page ")
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
                    continue

        close_sql(cur, conn)
        #print(t_name + " done!")
        logging.info(self.t_name + "done!")


class C1(threading.Thread):

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
            for c2 in items:
                category_2 = c2.find('h3').text.encode('utf-8')
                category_3 = c2.find_all("li")
                thread_name_1 = "Thread_" + self.category_1 + '_' + category_2 + '_' + str(thread_id)
                thread_id += 1
                try:
                    tt = C2(thread_name_1, self.category_1, category_2, category_3)
                    #thread.start_new_thread(c_2, (thread_name_1, category_3, category_2, self.category_1))
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
    threadLock = threading.Lock()
    log()
    category_list = ['biology', 'chemistry', 'dmpk', 'pharmacology', 'toxicology']
    thread_id = 1
    for c1 in category_list:
        thread_name = "Thread" + '_' + c1 + '_' + str(thread_id)
        try:
            t = C1(thread_name, c1)
        except:
            logging.error("Error unable to start thread")
            continue
        t.start()
        print thread_name
        t.join()