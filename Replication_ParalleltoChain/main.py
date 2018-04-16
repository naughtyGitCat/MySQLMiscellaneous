#!/usr/bin/python3
# TODO:停止从库进程前先判断从库的SQL或IO线程是否已经停止。若有任意一个停止，弹出输入框，是否开启后继续执行脚本
# TODO:增加TRY EXCEPT的错误停止逻辑
# TODO:增加错误回滚到最初的复制拓补的步骤
# TODO:未摘出GTID信息，需要针对GTID进行另外一套流程
import pymysql
import time
from functions import print_slave_status, print_selfbinlog_status, get_newest_file_pos

# 设计目标：三节点ABC，一主两从复制，将从库C切换到从库B上，串联复制
#             A ---> B     A ---> B ---> C
#               ---> C
# 逻辑（需解析binlog.暂废弃）：
#         前提条件：由于是指定C切换到B上，需要C获取A的信息至少不能快于B的进度，所以需要先停止C库的IO进程，让C库不再继续获取A的信息
#         操作步骤：先停止C的复制IO进程，并获取其复制信息：master_log_file,master_log_file_pos等
#                             判断master_log_file=relay_master_pos并master_log_file_pos=exec_maser_log_pos是否满足
#                            （每秒一次判断，并print出来，当相等时，停止检测，进入下一步）
#                   然后获取B的master_log_file,master_log_file_pos并与上一步C的master_log_file,master_log_file_pos进行比较
#                             判断B>=C且master_log_file=relay_master_pos并master_log_file_pos=exec_maser_log_pos
#                             （分别每秒一次判断，并print出来，当不小于时，，停止检测，进入下一步）
#                   最后进行切换，C:change master to master_log_file=B(binlog_file,binlog_file_pos)
# 逻辑（同步停止）：
#         前提条件：使用start slave until命令停止到同一个位置
#         操作步骤：在主库上执行flush logs；
#                   获取当前的位置，在主库业务不断的情况下，当前位置+100
#                   使用start slave until命令停止到当前位置+100
#                   判断master_log_file=relay_master_pos并master_log_file_pos=exec_maser_log_pos是否满足
#                            （每秒一次判断，并print出来，当相等时，停止检测，进入下一步）
#                   获取B的binlog_file,binlog_pos
#                   最后进行切换，C:change master to master_log_file=B(binlog_file,binlog_file_pos)
#         错误回滚：重新切换回原主库（切换到新主之前可以回滚，切换之后无法完美回滚）

# 参数定义：
master_host = '192.168.1.8'
master_port = 3307

new_master_host = '192.168.1.8'
new_master_port = 3308

slave_host = '192.168.1.8'
slave_port = 3309

opreate_user = 'repl'
opreate_password = '123456'  # should have super,replication client/slave,reload privilege

# use_database = 'mysql'

# ########################切割主库的binlog日志，防止接下来的预估位置不准###########################
print('########################切割主库的binlog日志，防止接下来的预估位置不准###########################')
print('host=', master_host, 'port=', master_port, 'user=', opreate_user, 'password=', opreate_password, )
master = pymysql.Connect(host=master_host, port=master_port, user=opreate_user, password=opreate_password
                         )
# 游标
cursor_master = master.cursor()
# 打印出之前的show master status
print_selfbinlog_status(master)
# 切割日志
cursor_master.execute('flush logs')
print('master flush logs ok')

# 打印出之后的show master status
cursor_master.execute('show master status')
print_selfbinlog_status(master)

# #################################连接到两个从库上stop slave###############################
print('# #################################连接到两个从库上stop slave###############################')
# #被挂载的从库：
new_master = pymysql.Connect(host=new_master_host, port=new_master_port, user=opreate_user, password=opreate_password
                             )
# ##游标
cursor_new_master = new_master.cursor()
# ##先输出当前的slave进程状态
print_slave_status(new_master)
# ##停止SLAVE IO进程,但不停止SQL进程，防止SQL线程落后于IO进程
cursor_new_master.execute('stop slave io_thread')
# ##输出执行后的slave进程状态
(new_master_io_file, new_master_io_pos, new_master_sql_file, new_master_sql_pos) = print_slave_status(new_master)

# #被切换的从库
slave = pymysql.Connect(host=slave_host, port=slave_port, user=opreate_user, password=opreate_password
                        )
# ###游标
cursor_slave = slave.cursor()
# ###先输出当前的slave进程状态
print_slave_status(slave)
# ##停止SLAVE IO进程,但不停止SQL进程，防止SQL线程落后于IO进程
cursor_slave.execute('stop slave io_thread')
# ###输出执行后的slave进程状态
(slave_io_file, slave_io_pos, slave_sql_file, slave_sql_pos) = print_slave_status(slave)


# #########################通过比较获得比较大的，然后加上一个预估的偏移量########################################
print('#########################通过比较获得比较大的，然后加上一个预估的偏移量########################################')
(newest_file, newest_pos) = get_newest_file_pos(new_master_io_file, new_master_io_pos, slave_io_file, slave_io_pos)
print(type(newest_pos))
stop_pos = newest_pos+1000
print('chose_file:', newest_file,
      '\nchose_pos:', newest_pos)

# ########################停在同一个位置
print('开始切换')
start_until_sql = '''start slave until MASTER_LOG_FILE = '{}', MASTER_LOG_POS = {}'''\
            .format(newest_file, stop_pos)
reset_slave_sql = 'reset slave all'
print('开始停止到相同位置')
cursor_new_master.execute(start_until_sql)

cursor_slave.execute(start_until_sql)

# 检查新主库和从库是否到达指定位置（SQL线程是否停止）
while 1:
    time.sleep(1)
    (a, b, slave_sql_file, slave_sql_pos) = print_slave_status(slave)
    (a, b, new_master_sql_file, new_master_sql_pos) = print_slave_status(new_master)
    if slave_sql_file == newest_file and new_master_sql_file == newest_file:
        print('已经到达同一个binlog文件')
        if slave_sql_pos >= stop_pos and new_master_sql_pos >= stop_pos:
            print('两个从库已经在统一位置停下')
            cursor_new_master.execute('stop slave')
            cursor_slave.execute('stop slave')
            break
        else:
            print('新主库的位置：', new_master_sql_pos, '\n从库的位置：', slave_sql_pos, '\n停下的位置：', stop_pos)
    else:
        print('新主库的文件：', new_master_sql_file, '\n从库的文件：', slave_sql_file, '\n停下的文件：', newest_file)
# 在从库上reset slave
print('在从库上reset slave')
cursor_slave.execute(reset_slave_sql)

# #########################获取要被切换到的实例的binlog信息
print('获取要被切换到的实例的binlog信息')
(binlog_file, binlog_pos) = print_selfbinlog_status(new_master)
print(type(binlog_file), type(binlog_pos))

# ######################切换
print('now begin change')
change_sql = '''change master to  MASTER_HOST='{}',MASTER_PORT={},MASTER_USER='{}',MASTER_PASSWORD='{}',MASTER_LOG_FILE='{}',MASTER_LOG_POS={}'''\
                .format(new_master_host, new_master_port, opreate_user, opreate_password, binlog_file, binlog_pos)
print(change_sql)
# 此步执行完后需严格检查和回滚
print('开始切换到新主库')
cursor_slave.execute(change_sql)
print_slave_status(slave)

# 检查切换后的情况

# ######################开启复制
print('开启复制')
cursor_slave.execute('start slave')
print_slave_status(slave)

# ##################################收尾
master.close()
slave.close()
new_master.close()




