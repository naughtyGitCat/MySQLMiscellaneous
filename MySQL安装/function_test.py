#!/usr/bin/python3
import os
from start_instance import add_mysql_user, del_mysql_user, download, untar


# 用户模块测试
# del_mysql_user()
# add_mysql_user()
#
# cmd_getuid = 'id -u mysql'
# cmd_getgid = 'id -g mysql'
# uid = os.popen(cmd_getuid).read().strip('\n')
# gid = os.popen(cmd_getgid).read().strip('\n')
# print('uid:', uid, 'gid:', gid)

# OK

# 下载模块测试
# download()

# OK，但是不能实时显示下载进度条


# 解压模块测试

untar()
