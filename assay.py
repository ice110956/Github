#!usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Patrick'

import MySQLdb
import thread
import sys
import urllib2
import re
import urllib
import logging
from bs4 import BeautifulSoup
import os


def log():
    logging.basicConfig(filename=os.path.join(os.getcwd(), 'log.txt'), level=logging.INFO, filemode='w')


def translate(text):
    """translate English to Chinese"""

    values = {'client': 't', 'sl': 'en', 'tl': 'zh-CN', 'hl': 'zh-CN', 'ie': 'UTF-8', 'oe': 'UTF-8', 'prev': 'btn',
              'ssel': '0', 'tsel': '0', 'q': text}
    url = "http://translate.google.cn/translate_a/t"
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    browser = "Mozilla/5.0 (Windows NT 6.1; WOW64)"
    req.add_header('User-Agent', browser)
    response = urllib2.urlopen(req)
    get_page = response.read()
    text_page = re.search('\[\[.*?\]\]', get_page).group()
    text_list = []
    rex = re.compile(r'\[\".*?\",')
    for item in re.findall(rex, text_page):
        item = item.replace('[', "")
        item = item.replace('",', "")
        item = item.replace('"', "")
        text_list.append(item)
    text_result = "".join(text_list)
    return text_result


def sql():
    """create a new connection to database
    return the connection"""

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

    #print(url)
    logging.info(url)
    try:
        response = urllib2.urlopen(url)
    except:
        #print("unable to open url " + url)
        logging.error("unable to open url " + url)
        return
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
        #print "insert service error"
        logging.error("insert service error")

    _sql = 'select s_id from service where s_name=%s'
    param = services_name
    try:
        cur.execute(_sql, param)
    except:
        #print "get services' id error"
        logging.error("get services' id error")
    results = cur.fetchall()
    services_id = 0
    if results is not None:
        for rec in results:
            services_id = rec[0]
    return services_id


def get_services_url(soup):
    """to get the services' url in a second category in multi-page
    return a list contain which all urls"""

    url_services = []
    while True:
        items = soup.find_all("h4", class_="media-headig")
        if items is None:
            #print "find no services"
            logging.info("find no services")
        else:
            #print "find services"
            logging.info("find services")
            for item in items:
                url_services.append("http://www.assaydepot.com" + item.a['href'].encode('utf-8'))
                #print "serivices url is " + "http://www.assaydepot.com" + item.a['href']
        next_page = soup.find("li", class_="next next_page ")
        if next_page is not None:
            #print "goto next page"
            logging.info("go to next page")
            url_next = "http://www.assaydepot.com" + next_page.a['href'].encode('utf-8')
            try:
                response = urllib2.urlopen(url_next)
            except:
                #print("unable to open url " + url_next)
                logging.error("unable to open url " + url_next)
                break
            page = response.read()
            soup = BeautifulSoup(page)
        else:
            #print "no next page,out"
            logging.info("no next page,out")
            break
    return url_services


def get_provider_description(url, cur, conn, thread_name):
    """to get one service page 's description and insert into database
    request param of url and database connect and category_id
    return provider id
    if provider is overlap return -1"""

    #print url
    logging.info(url)
    try:
        response = urllib2.urlopen(url)
    except:
        #print("unable to open url " + url)
        logging.error("unable to open url " + url)
        return
    page = response.read()
    soup = BeautifulSoup(page)
    provider_name = soup.find("h1").text.encode('utf-8')

    _sql = 'select p_name,p_id from provider where p_name =%s'
    param = provider_name
    is_exist = cur.execute(_sql, param)
    if is_exist == 0:
        #print provider_name + 'ready to insert'
        provider = soup.find("div", id="provider_description")
        provider_description = provider.find_all("p")
        des = []
        for description in provider_description:
            des.append(description.text)
        des_str = "".join(des).encode('utf-8')
        #print des_str
        _sql = 'insert into provider(p_name,p_description,p_description_cn) values(%s,%s,%s)'
        des_str_cn = translate(des_str)
        param = (provider_name, des_str, des_str_cn)
        try:
            cur.execute(_sql, param)
            conn.commit()
        except:
            return -1

        #return provider id
        _sql = 'select p_id from provider where p_name=%s'
        param = provider_name
        cur.execute(_sql, param)
        results = cur.fetchall()
        provider_id = 0
        if results is not None:
            for rec in results:
                provider_id = rec[0]
        #print provider_id
        return provider_id
    else:
        #print provider_name + 'is overlap'
        #logging.info(provider_name + ' is old in thread ' + thread_name)
        return -1


def get_provider(url, cur, conn, id_services, thread_name):
    """for each services to get the providers
    insert the provider and then link into table provider and link in the database"""

    #print(url)
    logging.info(url)
    try:
        response = urllib2.urlopen(url)
    except:
        logging.error("unable to open url " + url)
        #print("unable to open url " + url)
        return
    page = response.read()
    soup = BeautifulSoup(page)
    span = soup.find("div", class_="span3")
    ul = span.find("ul")
    providers = ul.find_all("li")
    url_list = []
    if providers is not None:
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
                logging.error("insert link error")
                continue


def c_2(t_name, category_3, category_2, category_1):
    """category 2 thread function,in each second category"""

    conn = sql()
    cur = conn.cursor()
    if category_3 is not None:
        for c3 in category_3:
            #for each second category
            _sql = 'insert into category(c_name,c_category_1,c_category_2) values(%s,%s,%s)'
            param = (c3.a.text.encode('utf-8'), category_1, category_2)
            try:
                cur.execute(_sql, param)
                conn.commit()
            except:
                #print 'insert category error'
                logging.error("insert category error")
                continue
                #error
            _sql = 'select c_id from category where c_name=%s'
            param = (c3.a.text.encode('utf-8'))
            #get each third category and insert into database
            cur.execute(_sql, param)
            results = cur.fetchall()
            if results is not None:
                for rec in results:
                    category_id = rec[0]
                #print category_id
                url_3 = "https://www.assaydepot.com" + c3.a['href'].encode('utf-8')
                #print(url_3)
                logging.info(url_3)
                try:
                    response = urllib2.urlopen(url_3)
                except:
                    #print("unable to open url " + url_3)
                    logging.error("unable to open url " + url_3)
                    continue
                page = response.read()
                soup = BeautifulSoup(page)
                #get the third category page soup
                url_services = get_services_url(soup)

                if url_services is not None:
                    for url in url_services:
                        #print("insert services!")
                        logging.info("insert services!")
                        id_services = get_services_description(url, cur, conn, category_id)
                        get_provider(url, cur, conn, id_services, t_name)
            else:
                continue

    close_sql(cur, conn)
    #print(t_name + " done!")
    logging.info(t_name + "done!")
    thread.exit_thread()


def c_1(t_name, category_1):
    """thread function in category1"""

    url = "https://www.assaydepot.com/better_categories/" + category_1
    #print(url)
    logging.info(url)
    try:
        response = urllib2.urlopen(url)
    except:
        #print("unable to open url " + url)
        logging.error("unable to open url " + url)
        return
    page = response.read()
    soup = BeautifulSoup(page)
    items = soup.find_all("div", class_="well")
    thread_id = 1
    if items is not None:
        for c2 in items:
            category_2 = c2.find('h3').text.encode('utf-8')
            category_3 = c2.find_all("li")
            thread_name_1 = "Thread_" + category_1 + '_' + category_2 + '_' + str(thread_id)
            thread_id += 1
            try:
                thread.start_new_thread(c_2, (thread_name_1, category_3, category_2, category_1))
            except:
                #print ("Unable to open thread" + thread_name_1)
                logging.info("Unable to open thread" + thread_name_1)
    #print t_name + " done!"
    logging.info(t_name + " done!")
    thread.exit_thread()


if __name__ == "__main__":
    log()
    category_list = ['biology', 'chemistry', 'dmpk', 'pharmacology', 'toxicology']
    thread_id = 1
    for c1 in category_list:
        #c1 = category_list[0]
        thread_name = "Thread" + '_' + c1 + '_' + str(thread_id)
        try:
            thread.start_new_thread(c_1, (thread_name, c1))
        except:
            #print "ErrorL unable to start thread"
            logging.error("ErrorL unable to start thread")
    while 1:
        pass
