import re

# 函数，按行读出sql文件所有内容，省内存


def read_sql(filename):
    total = ''
    with open(filename, 'rt', encoding='utf8') as open_file:
        for line in open_file:
            total += line
    return total

# 函数，取出最后数据相关语句的最后位置


def get_tail(total):
    a = re.compile('''SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;''')
    b = a.search(total)
    start = b.end()-1
    return start

# 函数，掐头去尾，移除末尾杂项语句，输出前面的复制信息


def get_context(total):
    a = re.compile('''Current Database:''')
    b = a.search(total)
    start = b.end()-1
    m = re.compile('''Current Database:''')
    n = m.search(total)
    end = n.start()-1
    a = total[start:end]
    return a

# 函数，输入文本与关键字，取出关键字在文本中的的每个起始位置，以数组的形式输出


def get_pos(KEY_WORD, total):
    KEY_WORD_LENGTH = len(KEY_WORD)
    t = []                                # 将匹配到的位置放入这个数组中
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
    return t


# 函数，输入文本与关键字位置数组，取出关键字
def check_keyword(t, total):
    for x in t:
        print(total[x:x+8])
        if x == t[-1]:
            print('over')

# 函数，输入文本与关键字位置数组，取出关键字之间的文本


def save_paragraph(t, total):
    x = 0
    while 1:
        if x == len(t)-1:
            with open('db'+str(x), 'wt', encoding='utf-8') as fout:
                fout.write(total[t[x]:])
            print('over')
            break
        print('x:', x)
        print('len_t', len(t))
        print('check', t[x], t[x+1])
        print(total[t[x]:t[x+1]])       # 取出第一段内容
        with open('db'+str(x), 'wt', encoding='utf-8') as fout:
            fout.write(total[t[x]:t[x+1]])

        x += 1