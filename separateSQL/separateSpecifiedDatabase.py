#先取出所有
from functions import *
import json,re

# 从mysqldump全备文件中分离特定库的SQL语句
filename = 'django.sql'

# TODO: '这儿要改成接收输入的方式传入数据库名'
DATABASE = input('请再次输入数据库名（部分也可以，但只能输出一个，\n所以：请输入部分但唯一的名称）：')
PREFIX = 'Current Database:'
KEY_WORD = PREFIX+'.*'+DATABASE
total = read_sql(filename)


def get_head(total):
    a = re.compile(KEY_WORD)
    b = a.search(total)
    start = b.start()
    return start


start = get_head(total)


def get_tail(total):                # 取下次create database语句前面一个字母的位置
    a = re.compile(PREFIX)
    b = a.search(total, start+len(KEY_WORD))  # 错开开头
    while b is not None:
        end = b.start() - 1
        print('{} is not last db'.format(DATABASE))
        break
    if b is None:
        print('{} is the last db'.format(DATABASE))
        end = get_data_tail(total)+1  #原本已经减掉了1个，不能再减，先加上一个

    return end

end = get_tail(total)

# print(start,end)  检查检出的位置的正确性用

def get_db_sql(total, start, end):
    with open('output/'+DATABASE+'.sql', 'wt',  encoding= 'utf-8') as fout:
        fout.write(total[start-3:end])


get_db_sql(total,start,end)