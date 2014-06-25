#!usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Patrick'

import urllib2
import urllib
import re
import gzip
import zipfile
import tarfile
import os.path
import sys
import rarfile
from bs4 import BeautifulSoup
import time


class HtmlModel(object):
    """download the description and files
    下载 https://www.ebi.ac.uk/arrayexpress/experiments/browse.html 中的指定数据
    包括描述以及文件，描述写入txt中，下载的文件解压后放入当前文件夹"""

    def __init__(self):
        self.page = ""

    @staticmethod
    def un_gz(file_name):
        """解压 gz file"""
        f_name = file_name.replace(".gz", "")
        g_file = gzip.GzipFile(file_name)
        open(f_name, "w+").write(g_file.read())
        g_file.close()
        os.remove(file_name)

    @staticmethod
    def un_zip(file_name):
        """解压 zip file"""
        zip_file = zipfile.ZipFile(file_name)
        if os.path.isdir(file_name + "_files"):
            pass
        else:
            os.mkdir(file_name + "_files")
        for names in zip_file.namelist():
            zip_file.extract(names, file_name + "_files/")
        zip_file.close()
        os.remove(file_name)

    @staticmethod
    def un_tar(file_name):
        """解压 tar file"""
        tar = tarfile.open(file_name)
        names = tar.getnames()
        if os.path.isdir(file_name + "_files"):
            pass
        else:
            os.mkdir(file_name + "_files")
        for name in names:
            tar.extract(name, file_name + "_files/")
        tar.close()
        os.remove(file_name)

    @staticmethod
    def un_rar(file_name):
        """解压 rar file"""
        rar = rarfile.RarFile(file_name)
        if os.path.isdir(file_name + "_files"):
            pass
        else:
            os.mkdir(file_name + "_files")
        os.chdir(file_name + "files")
        rar.extractall()
        os.chdir("../")
        rar.close()

    #translate
    @staticmethod
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
                print "google translate is unreachable and try again"
                time.sleep(1)
                #等待一秒继续尝试连接
                flag = False
                #get url error and wait 1s
                continue
            break
        if flag is False:
            print "google translate is unreachable!"
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

    def get_page(self, page):
        """主方法"""

        self.page = page
        my_url = "https://www.ebi.ac.uk/arrayexpress/experiments/" + self.page
        try:
            my_response = urllib2.urlopen(my_url)
        except:
            print("wrong name!")
            return 
        my_page = my_response.read()
        soup = BeautifulSoup(my_page)

        #获得描述
        #in English
        des_name = []
        des_value = []
        for item in soup.findAll('td', class_='name'):
            des_name.append(item.text)
        for item in soup.findAll('td', class_='value'):
            des_value.append(item.text)
        f = file(self.page + '_description' + '.txt', 'w+')
        print('down description')
        for i in range(0, len(des_name)):
            text_name = des_name[i].encode('utf-8')
            text_value = des_value[i].encode('utf-8')
            text = "<"+text_name+","+text_value+">" + "\n\r"
            #print(Item)
            f.write(text)
        f.close()

        #in Chinese
        f = file(self.page + '_description_cn' + '.txt', 'w+')
        for i in range(0, len(des_name)):
            text_name = self.translate(des_name[i].encode('utf-8'))
            text_value = self.translate(des_value[i].encode('utf-8'))
            text = "<" + text_name + "," + text_value + ">" + "\n\r"
            #print(Item)
            f.write(text)
        f.close()
        print('done!')
        
        #download
        def cbk(a, b, c):
            per = 100.0 * a * b / c
            if per > 100:
                per = 100
            print 'completed %.2f%%' % per

        for item in soup.findAll('a', attrs={'class': 'icon icon-functional', 'data-icon': '='}):
            sub_url = item.get('href')
            replace_char = re.compile("/.*/")
            url = "https://www.ebi.ac.uk" + sub_url
            local = replace_char.sub("", sub_url)
            print('download '+local + '...')
            urllib.urlretrieve(url, local, cbk)
            #根据不同的后缀名，解压不同压缩文件
            if url.find(".zip") >= 0:
                self.un_zip(local)
            if url.find(".gz") >= 0:
                self.un_gz(local)
            if url.find(".tar") >= 0:
                self.un_tar(local)
            if url.find(".tgz") >= 0:
                self.un_tar(local)
            print('done!')

if __name__ == "__main__":
    #通过命令行读取多个要下载的页面名
    #在当前目录下新建同名文件夹，把下载的内容放入
    myModel = HtmlModel()
    arg_len = len(sys.argv)
    if arg_len <= 1:
        print "Not file name"
    for i in range(1, arg_len):
        if os.path.isdir(sys.argv[i]):
            pass
        else:
            os.mkdir(sys.argv[i])
            os.chdir(sys.argv[i])
        myModel.get_page(sys.argv[i])
        os.chdir('../')
