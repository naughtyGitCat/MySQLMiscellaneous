import json

# 从mysqldump全备文件中分离特定库的SQL语句
filename = 'django.sql'
total = ''

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
    a = total.find('TABLE', pos_start, pos_end)
    t.append(a)
    if a == -1:
        break
    pos_start = a + 5
    print(pos_start)
print(t)

# ###################检验取出坐标的正确性



# ################### try,catch,else 实验########################
# try:
#     print(total.index('database'))
# except:
#     print('''does not have this string''')
# else:
#     print('''does have''')
# ##############################################################
