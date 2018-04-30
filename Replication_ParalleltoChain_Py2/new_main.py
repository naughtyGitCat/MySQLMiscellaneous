#!/usr/bin/python2
# coding=utf-8
# TODO:多样本检测
# TODO:增加错误回滚步骤异常的提醒
# TODO:未摘出GTID信息，需要针对GTID进行另外一套流程
# TODO:将print改为记录日志
# TODO:将创建实例连接，执行SQL，检查自身Binlog和slave信息做成一个class

# import pymysql
import time
from functions import print_slave_status, print_selfbinlog_status, get_newest_file_pos, read_args, print_rep_info
import MySQLdb as pymysql

# 全局参数：从库切换用
middle_master_file = ''
middle_master_pos = ''
orgin_file = ''
origin_pos = ''
error_code = ''
# 读入连接参数
(master_host, master_port, new_master_host, new_master_port, slave_host, slave_port, opreate_user,
 opreate_password) = read_args()

new_master = pymysql.Connect(host=new_master_host, port=new_master_port, user=opreate_user, passwd=opreate_password
                             )
slave = pymysql.Connect(host=slave_host, port=slave_port, user=opreate_user, passwd=opreate_password
                        )
master = pymysql.Connect(host=master_host, port=master_port, user=opreate_user, passwd=opreate_password
                         )


(master_host_N, master_port_N, new_master_io_file, new_master_io_pos, new_master_sql_file,
 new_master_sql_pos) = print_slave_status(new_master)
(master_host_S, master_port_S, slave_io_file, slave_io_pos, slave_sql_file, slave_sql_pos) = print_slave_status(slave)
(io_thread_running_n, sql_thread_running_n) = print_rep_info(new_master)
(io_thread_running_s, sql_thread_running_s) = print_rep_info(slave)


# 预检模块


def pre_check():
    global error_code
    # ##################先预检，判断当前复制拓补是否为一主两从，两个从库是否存在slave线程（SQL,IO任一）停止的情况###########
    (master_host_N, master_port_N, new_master_io_file, new_master_io_pos, new_master_sql_file,
     new_master_sql_pos) = print_slave_status(new_master)
    (master_host_S, master_port_S, slave_io_file, slave_io_pos, slave_sql_file, slave_sql_pos) = print_slave_status(
        slave)
    (io_thread_running_n, sql_thread_running_n) = print_rep_info(new_master)
    (io_thread_running_s, sql_thread_running_s) = print_rep_info(slave)
    print('########################预检模块开始###########################')
    if master_host_N == master_host_S and master_port_N == master_port_S \
            and io_thread_running_n == 'Yes' and io_thread_running_n == 'Yes' \
            and io_thread_running_s == 'Yes' and io_thread_running_s == 'Yes':
        print('复制链路正确，slave线程全部running')
        print('master_port_N:', master_port_N, 'master_port_S:', master_port_S)
    else:
        error_code = 'pre_check'
        raise Exception


# 连到从库，停止IO进程


def stop_slave_io_thread():
    # #################################连接到从库上停止IO进程###############################
    try:
        global error_code
        print('# #################################连接到从库上停止IO进程###############################')
        # #被切换的从库
        slave = pymysql.Connect(host=slave_host, port=slave_port, user=opreate_user, passwd=opreate_password
                                )
        # ###游标
        cursor_slave = slave.cursor()
        # ##停止SLAVE IO进程,但不停止SQL进程，防止SQL线程落后于IO进程
        cursor_slave.execute('stop slave io_thread')
        time.sleep(3) # 等待3秒，让中间库的IO进度快于自己的IO
        # ###输出执行后的slave进程状态
        (a, b, slave_io_file, slave_io_pos, slave_sql_file, slave_sql_pos) = print_slave_status(slave)
    except Exception:
        error_code = 'stop_slave_io_thread'
        raise Exception

# 停止中间库的IO进程，待执行完毕后，show slave status获取其pos,file，然后show master status 获取其pos，file用于从库切换
def stop_the_middle():
    print('# #################################连接到中间库上停止IO进程获取其pos,file,start###############################')
    try:
        global middle_master_file
        global middle_master_pos
        global orgin_file
        global origin_pos
        global error_code
        middle_master = pymysql.Connect(host=slave_host, port=slave_port, user=opreate_user, passwd=opreate_password
                                )
        # ###游标
        cursor_middle_master = middle_master.cursor()
        # ##停止IO进程，等待SQL线程完成复制
        cursor_middle_master.execute('stop slave io_thread')
        # ##检查SQL线程是否完成复制
        while 1:
            print('checking replication process')
            time.sleep(5)     # 循环检查的间隔5s
            (a, b, slave_io_file, slave_io_pos, slave_sql_file, slave_sql_pos) = print_slave_status(slave)
            if slave_io_file == slave_sql_file and slave_io_pos == slave_sql_pos:
                print('sql thread finished replicate')
                break
        (orgin_file, origin_pos) = (slave_io_file, slave_io_pos)
        (middle_master_file, middle_master_pos) = print_selfbinlog_status(middle_master)
        cursor_middle_master.execute('start slave')
    except Exception:
        error_code = 'stop_the_middle'
        raise Exception


# 停在上面选定的位置上
def stop_at_chose_pos():
    global orgin_file
    global origin_pos
    global error_code
    # ########################停在同一个位置
    try:
        print('停止SQL线程')
        start_until_sql = '''start slave until MASTER_LOG_FILE = '{}', MASTER_LOG_POS = {}''' \
            .format(orgin_file, int(origin_pos))
        print(start_until_sql)
        print('开始停止到中间库的指定位置')
        # #被切换的从库
        slave = pymysql.Connect(host=slave_host, port=slave_port, user=opreate_user, passwd=opreate_password
                                )
        # ###游标
        cursor_slave = slave.cursor()
        cursor_slave.execute(start_until_sql)
        # ###检查是否到达指定位置
        while 1:
            print('checking replication process')
            time.sleep(5)  # 循环检查的间隔5s
            (a, b, slave_io_file, slave_io_pos, slave_sql_file, slave_sql_pos) = print_slave_status(slave)
            if slave_io_file == slave_sql_file and slave_io_pos == slave_sql_pos:
                print('sql thread finished replicate')
                break

    except Exception:
        error_code = 'stop_at_same_pos'
        raise Exception




 # 切换GO！！！
def change_to_new_master():
    global middle_master_file
    global middle_master_pos
    global error_code
    try:
        # ######################切换
        slave = pymysql.Connect(host=slave_host, port=slave_port, user=opreate_user, passwd=opreate_password)
        # ###游标
        cursor_slave = slave.cursor()
        # 在从库上reset slave
        print('在从库上reset slave')
        # 因为start slave until到达指定位置后只会停止SQL_THREAD,而reset slave需要全部停止，所以需要再次全部停止
        cursor_slave.execute('stop slave')
        cursor_slave.execute('reset slave all')
        print('now begin change')
        change_sql = '''change master to  MASTER_HOST='{}',MASTER_PORT={},MASTER_USER='{}',MASTER_PASSWORD='{}',MASTER_LOG_FILE='{}',MASTER_LOG_POS={}''' \
            .format(new_master_host, new_master_port, opreate_user, opreate_password, middle_master_file, int(middle_master_pos))
        print(change_sql)
        print('开始切换到新主库')
        cursor_slave.execute(change_sql)
        cursor_slave.execute('start slave')
        print_slave_status(slave)
    except Exception:
        error_code = 'change_to_new_master'
        raise Exception



# 检查切换后的sql与slave线程情况
def after_change():
    global error_code
    try:
        time.sleep(3)
        slave = pymysql.Connect(host=slave_host, port=slave_port, user=opreate_user, passwd=opreate_password)
        # ###游标
        cursor_slave = slave.cursor()
        (master_host_S, master_port_S, a, b, c, d) = print_slave_status(slave)
        (io_thread_running_s, sql_thread_running_s) = print_rep_info(slave)
        if master_port_S == new_master_host and master_port_S == new_master_port \
              and io_thread_running_s == 'Yes' and io_thread_running_s == 'Yes':
            print('change OK,slave running!!!')
    except Exception:
        error_code = 'after_change'
        raise Exception

def change_back():
    global orgin_file
    global origin_pos
    print('切换回去')
    slave = pymysql.Connect(host=slave_host, port=slave_port, user=opreate_user, passwd=opreate_password)
    # ###游标
    cursor_slave = slave.cursor()
    cursor_slave.execute('stop slave')
    cursor_slave.execute('reset slave all')
    change_sql = '''change master to  MASTER_HOST='{}',MASTER_PORT={},MASTER_USER='{}',MASTER_PASSWORD='{}',MASTER_LOG_FILE='{}',MASTER_LOG_POS={}''' \
        .format(master_host, master_port, opreate_user, opreate_password, orgin_file,
                int(origin_pos))
    cursor_slave.execute('start slave')

def start_all_slave():
    slave = pymysql.Connect(host=slave_host, port=slave_port, user=opreate_user, passwd=opreate_password)
    middle_master = pymysql.Connect(host=slave_host, port=slave_port, user=opreate_user, passwd=opreate_password
                                    )
    # ###游标
    cursor_slave = slave.cursor()
    cursor_middle_master = middle_master.cursor()
    cursor_slave.execute('start slave')
    cursor_middle_master.execute('start slave')

### main
try:
    pre_check()
    stop_slave_io_thread()
    stop_the_middle()
    stop_at_chose_pos()
    change_to_new_master()
    after_change()
except Exception:
    if error_code == 'change_to_new_master':
        print('已经发生切换，尝试切换回去')
        change_back()
    elif error_code == 'after_change':
        print('切换成功，但SLAVE线程有问题，请手工检查show slave status')
    else:
        print('尚未切换，尝试重新启动两个从库的slave进程')
        start_all_slave()
