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
i = 0
while total.find('TABLE') > 0:
    a = total.find('TABLE')
    i += 1
    total=total[a:]
print(i)




# try:
#     print(total.index('database'))
# except:
#     print('''does not have this string''')
# else:
#     print('''does have''')
