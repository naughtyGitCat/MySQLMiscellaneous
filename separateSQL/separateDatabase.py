import json

# 从mysqldump全备文件中分离特定库的SQL语句
filename = 'django.sql'
total = ''
DATABASE = 'django'
KEY_WORD = 'Current Database:'
KEY_WORD_LENGTH = len(KEY_WORD)

with open(filename, 'rt', encoding='utf8') as open_file:
    for line in open_file:
        total += line
print(len(total))
# a = total.index('xxxxxx')
# print(a)
# print(total)
t = []                              # 将匹配到的位置放入这个数组中

pos_start = 0
pos_end = len(total)
while 1:
    a = total.find(KEY_WORD, pos_start, pos_end)
    if a == -1:                     # 如果匹配不到就退出匹配
        break
    t.append(a)
    pos_start = a + KEY_WORD_LENGTH               # 偏移量为匹配词的长度
    print(pos_start)
print(t)

# ###################检验取出坐标的正确性####################
for x in t:
    print(total[x:x+8])
    if x == t[-1]:
        print('over')

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

# ################### 取出第一段内容###########################################
# total[]