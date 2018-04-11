#!/usr/bin/python3
import os
from start_instance import add_mysql_user, del_mysql_user, download


# 用户模块测试
# del_mysql_user()
# add_mysql_user()
#
# cmd_getuid = 'id -u mysql'
# cmd_getgid = 'id -g mysql'
# uid = os.popen(cmd_getuid).read().strip('\n')
# gid = os.popen(cmd_getgid).read().strip('\n')
# print('uid:', uid, 'gid:', gid)


# 下载模块测试47
download()