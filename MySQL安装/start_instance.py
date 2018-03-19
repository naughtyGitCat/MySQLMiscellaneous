import subprocess
import os
import urllib.request
import sys,getopt
#
# 设计用途：
#         快速安装3306实例

# 下载二进制包


# 请求输入端口


def input_port():
    port = input('请输入实例端口：')
    return port


# 判断能否上网


def net_status():
    yellow_website = 'http://www.baidu.com'
    conn = urllib.request.urlopen(yellow_website).code
    return conn

# 调用wget下载


def download():

    if net_status() == 200:
        source_dir = '/usr/local/src/'
        source = 'https://dev.mysql.com/get/Downloads/MySQL-5.7/mysql-5.7.21-linux-glibc2.12-x86_64.tar.gz'
        # binary = urllib.request.urlopen(source)
        # with open('mysql57_21.tar.gz', 'wb') as file:
        #     file.write(binary)
        download_cmd = 'wget {} -P {}'.format(source, source_dir)
        get_binary = subprocess.getstatusoutput(download_cmd)

    else:
        print('请使用-f命令指定二进制安装包位置')


# 解压下载的二进制安装包

def untar():
    try:
        tar_path = '/usr/local/src/mysql-5.7.21-linux-glibc2.12-x86_64.tar.gz'
        bin_path = '/usr/local/'
        untar_cmd = 'tar -zxf {} -C {}'.format(tar_path, bin_path)
        (status, output) = subprocess.getstatusoutput(untar_cmd)
        if status == 0:
            print('untar finished')
        else:
            raise Exception
    except Exception:
        print('exec untar across a error')


# 创建相关文件夹


def prepare(port):
    try:
        os.makedirs('/data/mysql/{}/data'.format(port))
        os.mkdir('/data/mysql/{}/logs'.format(port))
        os.mkdir('/data/mysql/{}/tmp'.format(port))
    except OSError:
        print('create dir error,please check')


# 创建MySQL用户和用户组

def mysql_user():




