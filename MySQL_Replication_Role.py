import pymysql
import sys


def initialize_conn():
    host = sys.argv[1]
    port = sys.argv[2]
    user = sys.argv[3]
    password = sys.argv[4]
    database = sys.argv[5]
    db = pymysql.connect(host, int(port), user, password,
                         database, cursorclass=pymysql.cursors.DictCursor)
    return db

# 简化打印函数


def p(arg):
    print(arg)


# 打印字典内容


def p_dict(arg):
    for x in arg.items():
        print(x)


# 判断实例是否为双线程正常且没有严重落后主库的从库
# 获取slave status


def getSlaveInfo():
    sql = "show slave status"
    cursor = initialize_conn().cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    result = result[0]  # 将字典从字典列表中取出来
    return result


# 检查slave status


def isNiceSlave(Info):
    if Info['Slave_IO_Running'] == 'Yes' and Info['Slave_SQL_Running'] == 'Yes':
        return 0
    else:
        p('Slave_IO_Running', Info['Slave_IO_Running'])
        p('Slave_SQL_Running', Info['Slave_SQL_Running'])
        return 1


Info = getSlaveInfo()
if len(Info) > 2:
    a = isNiceSlave(Info)
