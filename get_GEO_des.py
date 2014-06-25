#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Patrick'
#下载"http://www.ncbi.nlm.nih.gov/sites/GDSbrowser?acc="中的指定内容
#包括download中的文件，压缩文件解压，描述写入txt中（中英文）
#全部放入同名文件夹里


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


def un_gz(file_name):
    """解压 gz file"""
    f_name = file_name.replace(".gz", "")
    try:
        g_file = gzip.GzipFile(file_name)
        open(f_name, "w+").write(g_file.read())
    except:
        print 'ungz error'
        return
    g_file.close()
    os.remove(file_name)


def un_zip(file_name):
    """解压 zip file"""
    zip_file = zipfile.ZipFile(file_name)
    if os.path.isdir(file_name + "_files"):
        pass
    else:
        os.mkdir(file_name + "_files")
    for names in zip_file.namelist():
        try:
            zip_file.extract(names, file_name + "_files/")
        except:
            print 'unzip file ' + file_name + ' error'
            return
    zip_file.close()
    os.remove(file_name)


def un_tar(file_name):
    """解压 tar file"""
    tar = tarfile.open(file_name)
    names = tar.getnames()
    if os.path.isdir(file_name + "_files"):
        pass
    else:
        os.mkdir(file_name + "_files")
    for name in names:
        try:
            tar.extract(name, file_name + "_files/")
        except:
            print 'untar file ' + file_name + ' error'
            return
    tar.close()
    os.remove(file_name)


def un_rar(file_name):
    """解压 rar file"""
    rar = rarfile.RarFile(file_name)
    if os.path.isdir(file_name + "_files"):
        pass
    else:
        os.mkdir(file_name + "_files")
    os.chdir(file_name + "files")
    try:
        rar.extractall()
    except:
        print 'unrar file ' + file_name + ' error'
        return
    os.chdir("../")
    rar.close()


def extract_file(file_name):
    """extract all kind of file"""
    if file_name.find(".zip") >= 0:
        un_zip(file_name)
    if file_name.find(".gz") >= 0:
        un_gz(file_name)
    if file_name.find(".tar") >= 0:
        un_tar(file_name)
    if file_name.find(".tgz") >= 0:
        un_tar(file_name)
    print('done!')


class HtmlModel(object):
    """download the description and files
    下载http://www.ncbi.nlm.nih.gov/sites/GDSbrowser中指定的内容，描述写入name_description.txt文件
    压缩文件夹解压，全部放入同名文件夹"""

    def __init__(self):
        self.page = ""

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
        """main method"""
        self.page = page
        my_url = "http://www.ncbi.nlm.nih.gov/sites/GDSbrowser?acc=" + self.page
        try:
            my_response = urllib2.urlopen(my_url)
        except:
            print("wrong name!")
            return 
        my_page = my_response.read()
        soup = BeautifulSoup(my_page)

        #get description
        #in English
        des_name = []
        des_value = []
        details = soup.find("div", id="details")
        if details is None:
            print("Wrong name!")
            return
        for item in details.findAll('th', class_="not_caption"):
            text_name = ""
            for string in item.stripped_strings:
                tt = repr(string).encode('utf-8')
                tt = tt.replace("u", "")
                tt = tt.replace("\n", "")
                tt = tt.replace("\'", "")
                text_name += tt
            print(text_name)
            des_name.append(text_name)
            text_value = ""
            for string in item.next_sibling.stripped_strings:
                tt = repr(string).encode('utf-8')
                tt = tt.replace("u", "")
                tt = tt.replace("\n", "")
                tt = tt.replace("\'", "")
                text_value += tt
            print(text_value)
            des_value.append(text_value)
        f = file(self.page + '_description' + '.txt', 'w+')
        print('down description')
        for i in range(0, len(des_name)):
            text_name = des_name[i]
            text_value = des_value[i]
            text = "<"+text_name + text_value+">" + "\n\r"
            #print(text)
            f.write(text)
        f.close()

        #in Chinese
        f = file(self.page + '_description_cn' + '.txt', 'w+')
        for i in range(0, len(des_name)):
            text_name = self.translate(des_name[i].encode('utf-8'))
            text_value = self.translate(des_value[i].encode('utf-8'))
            text = "<" + text_name + text_value + ">" + "\n\r"
            f.write(text)
        f.close()
        print('done!')
        
        #download
        def cbk(a, b, c):
            per = 100.0 * a * b / c
            if per > 100:
                per = 100
            print 'completed %.2f%%' % per
        for item in soup.findAll('a', href=re.compile("ftp.*")):
            print "find ftp"
            url = item.get('href')
            replace_char = re.compile('/.*/')
            local = replace_char.sub("", url)
            print('download ' + local + '...')
            print url, local
            urllib.urlretrieve(url, local, cbk)

            #解压
            extract_file(local)

if __name__ == "__main__":

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