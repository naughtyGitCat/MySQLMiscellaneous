#
import operator
# 输出show slave status信息


def print_slave_status(conn):
    print('print_slave_status start')
    cursor = conn.cursor()
    # ###获取主机名
    cursor.execute(
        '''select * FROM performance_schema.global_variables where variable_name in ('hostname','port')''')
    print('现主从状况：', cursor.fetchall())
    cursor.execute('show slave status')
    raw_output = cursor.fetchall()
    miscellaneous_status = raw_output[0]
    print(miscellaneous_status)
    print('主库IP：', miscellaneous_status[1],
          '\n主库端口：', miscellaneous_status[3],
          '\nIO线程获取的主库binlog文件名称：', miscellaneous_status[5],
          '\nIO线程获取的主库binlog文件位置', miscellaneous_status[6],
          '\nSQL线程执行的主库binlog文件名称', miscellaneous_status[9],
          '\nSQL线程执行的主库binlog文件位置', miscellaneous_status[21],)
    # 返回IO线程获取的主库binlog文件名称，IO线程获取的主库binlog文件位置
    return miscellaneous_status[5], miscellaneous_status[6], miscellaneous_status[9], miscellaneous_status[21]


# 读取两个slave的show master status 信息，
def print_selfbinlog_status(conn):
    print('print_selfbinlog_status start')
    cursor = conn.cursor()
    # ###获取主机名
    cursor.execute(
        '''select * FROM performance_schema.global_variables where variable_name in ('hostname','port')''')
    print('本机binlog状况：', cursor.fetchall())
    cursor.execute('show master status')
    raw_output = cursor.fetchall()
    miscellaneous_status = raw_output[0]
    print('binlog文件名称：', miscellaneous_status[0],
          '\nbinlog文件位置：', miscellaneous_status[1])
    # 返回binlog文件名称，binlog文件位置
    return miscellaneous_status[0], miscellaneous_status[1]


# 输入两个从库的file,pos值，输出较新的一对
def get_newest_file_pos(new_master_file, new_master_pos, slave_file, slave_pos):
    print('get_newest_file_pos start')
    print(new_master_file, new_master_pos, slave_file, slave_pos)
    print(type(new_master_file), type(new_master_file))
    if operator.gt(new_master_file, slave_file) is True:
        newest_file = new_master_file
        newest_pos = new_master_pos
    elif operator.lt(new_master_file, slave_file) is True:
        newest_file = slave_file
        newest_pos = slave_pos
    elif operator.eq(new_master_file, slave_file) is True:
        newest_file = new_master_file
        newest_pos = max(int(new_master_pos), int(slave_pos))
    return newest_file, newest_pos


if __name__ == '__main__':
    import pymysql
    new_master_host = '192.168.1.8'
    new_master_port = 3308
    opreate_user = 'repl'
    opreate_password = '123456'  # should have super,replication client/slave,reload privilege
    new_master = pymysql.Connect(host=new_master_host, port=new_master_port, user=opreate_user,
                                 password=opreate_password
                                 )
    print_slave_status(new_master)
