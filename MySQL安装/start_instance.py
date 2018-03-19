import subprocess
import os
import urllib.request
#
# 设计用途：
#         快速安装3306实例

# 下载二进制包

# 判断能否上网


def net_status():
    yellow_website = 'http://www.baidu.com'
    conn = urllib.request.urlopen(yellow_website).code
    return conn


if net_status() == 200:
    os.chdir('/usr/local/src/')
    source = 'https://dev.mysql.com/get/Downloads/MySQL-5.7/mysql-5.7.21-linux-glibc2.12-x86_64.tar.gz'
    binary = urllib.request.urlopen(source)
    with open('mysql57_21.tar.gz', 'wb') as file:
        file.write(binary)
