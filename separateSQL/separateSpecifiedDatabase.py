#先取出所有

import json,re

# 从mysqldump全备文件中分离特定库的SQL语句
filename = 'django.sql'
total = ''
# TODO: '这儿要改成接收输入的方式传入数据库名'
DATABASE = 'django'
PREFIX = 'Current Database:'
KEY_WORD = PREFIX+'.*'+DATABASE


with open(filename, 'rt', encoding='utf8') as open_file:
    for line in open_file:
        total += line
print(len(total))
# a = total.index('xxxxxx')
# print(a)
# print(total)
t = []                              # 将匹配到的位置放入这个数组中
pattern = re.compile(KEY_WORD)
x = pattern.search(total)
pos_start = 0
pos_end = len(total)
while 1:
    a = pattern.search(total, pos_start, -1)
    if a is None:                     # 如果匹配不到就退出匹配
        break
    t.append(a.start())
    pos_start = a.end()+1+1               # 偏移量为匹配词的长度,加上一个反引号，其实加1也没毛病
    print(pos_start)
print(t)


# ###################检验取出坐标的正确性####################
# for x in t:
#     print(total[x:x+8])
#     if x == t[-1]:
#         print('over')

# ###################检验取出复数个坐标####################
x = 0
while 1:
    if x == len(t)-1:
        print('over')
        break
    print('x:', x)
    print('len_t', len(t))
    print('check', t[x], t[x+1])
    print(total[t[x]:t[x+1]])       # 取出第一段内容
    with open('db'+str(x), 'wt', encoding='utf-8') as fout:
        fout.write(total[t[x]:t[x+1]])

    x += 1


# ################### try,catch,else 实验########################
# try:
#     print(total.index('database'))
# except:
#     print('''does not have this string''')
# else:
#     print('''does have''')
# ##############################################################

# # ################### 取出第一段内容###########################################
# # total[]