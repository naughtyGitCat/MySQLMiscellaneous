# 批量插入MySQL
import pymysql

import json
user = 'python'
password = '123456'
host = '192.168.1.8'
port = 3307
conn = pymysql.Connect(host=host, port=port, user=user, password=password
                         )
cursor_conn = conn.cursor()
for i in range(200):
    insert_sql = '''insert into d20180416.hash_on_all_node_instance1(fid,c2,c3,c4) 
                    values ('{}','c2','c3','c4')'''\
                .format(i+1)
    print(insert_sql)
    cursor_conn.execute('select 1 from mysql.user')
    cursor_conn.execute(insert_sql)
    conn.commit()
    print(cursor_conn.fetchall())

conn.close()