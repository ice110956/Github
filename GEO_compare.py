#!usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Patrick'
#根据GEO数据库的比较，得到的两个文件（-1.txt,1.txt）获取其中的前n个有用的信息，写入文件中
#输入：GEO_compare文件夹下的两个文件：-1.txt(小于)，1.txt(大于)
#输出：result.txt文件，得到2*n个关键字及值

import os
import re
import sys


def compare(num):
    """read the -1.txt and 1.txt files
    and get the info into the result.txt
    在vs文件加下，加载-1.txt,1.txt两个文件
    其中1表示正表达，-1为负表达
    得到指定数量的gen name,一起放入result.txt中"""

    file_list = ['-1.txt', '1.txt']
    r = re.compile(r'^\d+\. .*? ')
    res = re.compile('\s$')
    gen_list = []
    for f in file_list:
        try:
            fi = open(f)
            fi_t = fi.read().splitlines()
        except:
            print 'open file' + f + 'error'
            sys.exit()
        count = 1
        for text in fi_t:
            if r.match(text):
                s = r.match(text).group(0).split('. ')
                #取特定的串
                s[1] = res.sub('', s[1])
                #去除前后多余空格
                if s[1] == 'Co-expression':
                    #忽略Miss value
                    continue
                print s
                if s[1] not in gen_list:
                    #如果没有重复，加入list
                    count += 1
                    #计数+1
                    gen_list.append(s[1])
            if count > num:
                #得到数量，退出
                break
        fi.close()

    #把得到的结果写入文件中
    fi = open('result.txt', 'w+')
    count = 1
    tt = '\t-1\n\r'
    for gen in gen_list:
        st = gen + tt
        fi.writelines(st)
        count += 1
        if count > num:
            count = 1
            fi.writelines('\n\r')
            tt = '\t1\n\r'
    fi.close()

if __name__ == '__main__':
    os.chdir('GEO_compare')
    #文件放在vs文件夹下
    n = 100
    #这里为提取前n个词条
    compare(n)