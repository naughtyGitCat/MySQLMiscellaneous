#!/usr/bin/python3
import pymysql

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

# 参数定义：
master_host = '192.168.1.8'
master_port = 3307

new_master_host = '192.168.1.8'
new_master_port = '3308'

slave_host = '192.168.1.8'
slave_port = '3309'

opreate_user = 'repl'
opreate_password = '123456'  # should have super,replication client/slave,reload privilege

use_database = 'mysql'

# 切割主库的binlog日志，防止接下来的预估位置不准
print('host=', master_host, 'port=', master_port, 'user=', opreate_user, 'password=', opreate_password, )
master = pymysql.Connect(host=master_host, port=master_port, user=opreate_user, password=opreate_password
                         )
# 游标
cursor_master = master.cursor()
# 打印出之前的show master status
cursor_master.execute('show master status')
a = cursor_master.fetchall()
print(a)
# 切割日志
cursor_master.execute('flush logs')
print('master flush logs ok')

# 打印出之后的show master status
cursor_master.execute('show master status')
a = cursor_master.fetchall()
print(a)

# 连接到两个从库上stop slave，
# 被挂载的从库：
new_master = pymysql.Connect(host=new_master_host, port=new_master_port, user=opreate_user, password=opreate_password,
                             )
# 游标
cursor_new_master = new_master.cursor()
# 先输出当前的slave进程状态
cursor_master.execute('show slave status\G')
print(cursor_master.fetchall())
# 停止SLAVE进程
cursor_new_master.execute('stop slave')
# 输出执行后的slave进程状态
cursor_master.execute('show slave status\G')
print(cursor_master.fetchall())

# 被切换的从库
slave = pymysql.Connect(host=slave_host, port=slave_port, user=opreate_user, password=opreate_password,
                        )
# 游标
cursor_slave = slave.cursor()
# 先输出当前的slave进程状态
cursor_slave.execute('show slave status\G')
print(cursor_slave.fetchall())
# 停止SLAVE进程
cursor_slave.execute('stop slave')
# 输出执行后的slave进程状态
cursor_slave.execute('show slave status\G')
print(cursor_slave.fetchall())

# 读取两个slave的show master status 信息，
cursor_new_master.execute('show slave status')
cursor_slave.execute('show slave status')
# 通过比较获得比较大的，然后加上一个预估的偏移量
# start slave until这个值加上预估的偏移量
# 获取new_master的show master status信息
# 在从库上reset slave
# 在从库上切换到new master的show master status信息
# 在从库上start slave
