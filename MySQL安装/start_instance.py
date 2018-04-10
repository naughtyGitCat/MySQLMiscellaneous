# TODO:根据机器与是否多实例生成my.cnf
import subprocess
import os
import urllib.request  # 下载
import shutil           # 复制文件
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


# 创建MySQL用户和用户组,并返回uid,gid

def add_mysql_user():
    try:
        cmd = 'useradd -d /usr/local/mysql/ -s /sbin/nologin -U -M mysql'
        (status, output) = subprocess.getstatusoutput(cmd)
        if status == 0:
            print('create user mysql success')
        else:
            raise Exception
        cmd_getuid = 'id -u mysql'
        cmd_getgid = 'id -g mysql'
        # os.popen输出的结果并不是char类型，需要read()出来，并截取换行符
        uid = os.popen(cmd_getuid).read().strip('\n')
        gid = os.popen(cmd_getgid).read().strip('\n')
        print('uid:', uid, 'gid:', gid)
    except Exception:
        print('create user mysql across a error,please check')


# 创建MySQL用户和用户组


def del_mysql_user():
    a = os.popen('userdel -r  mysql').read().strip('\n')
    print('userdel complete', a)
    b = os.popen('groupdel  mysql').read().strip('\n')
    print('groupdel executed', b)

# 创建数据文件夹,并归属到mysql用户下


def prepare(port,uid,gid):
    try:
        os.makedirs('/data/mysql/{}/data'.format(port))
        os.mkdir('/data/mysql/{}/logs'.format(port))
        os.mkdir('/data/mysql/{}/tmp'.format(port))
        os.chown('/data/mysql/{}/',uid,gid)
    except OSError:
        print('create dir error,please check')
    return '/data/mysql/{}'

# 接收指定的my.cnf文件，并复制到相关数据文件夹下


def cp_cnf(file_path, data_path):
        if os.path.exists(file_path):
            try:
                shutil.copy(file_path, data_path)
            except OSError:
                print('copy failed,please check it')
        else:
            print('file does`s not exist')


