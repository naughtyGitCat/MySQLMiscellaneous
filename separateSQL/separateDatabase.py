from functions import *

# 从mysqldump全备文件中分离特定库的SQL语句
filename = 'django.sql'

DATABASE = 'django'
KEY_WORD = 'Current Database:'


total = read_sql(filename)
t = get_pos(KEY_WORD, total)
check_keyword(t, total)


# ###################保存每段关键字之后的内容到单独的SQL文本中####################

save_paragraph(t, total)

