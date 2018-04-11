# TODO:根据机器与是否多实例生成my.cnf
# TODO:根据指定的MySQL版本下载二进制包
import subprocess
import os
import urllib.request  # 下载
import shutil  # 复制文件
import sys, getopt

#
# 设计用途：
#         快速安装3306实例


# ########参数定义段############
mysql_ver = 'mysql-5.7.21-linux-glibc2.12-x86_64'  # 暂未替换到各个函数中
miscellaneous_path = '/data/mysql/{}/'.format(port)  # 暂未替换到各个函数中
data_path = '{}/data'.format(miscellaneous_path)  # 暂未替换到各个函数中
binlog_path = '{}/logs'.format(miscellaneous_path)  # 暂未替换到各个函数中
base_path =

# ################


# 判断能否上网


def net_status():
    yellow_website = 'http://www.baidu.com'
    conn = urllib.request.urlopen(yellow_website).code
    return conn


# 调用wget下载
# TODO:需要对wget命令是否存在进行判断

def download():
    if net_status() == 200:
        print('network is ok,start download')
        subprocess.getoutput('yum -y install wget')
        source_dir = '/usr/local/src/'
        source = 'https://dev.mysql.com/get/Downloads/MySQL-5.7/mysql-5.7.21-linux-glibc2.12-x86_64.tar.gz'
        # binary = urllib.request.urlopen(source)
        # with open('mysql57_21.tar.gz', 'wb') as file:
        #     file.write(binary)
        print('set download command')
        download_cmd = 'wget {} -P {}'.format(source, source_dir)

        (status, output) = subprocess.getstatusoutput(download_cmd)
        print('status:', status, 'output:', output)
    else:
        print('请使用-f命令指定二进制安装包位置')


# 解压下载的二进制安装包
# TODO:询问是否创建超链接为mysql
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


def prepare(port, uid, gid):
    try:
        os.makedirs('/data/mysql/{}/data'.format(port))
        os.mkdir('/data/mysql/{}/logs'.format(port))
        os.mkdir('/data/mysql/{}/tmp'.format(port))
        os.chown('/data/mysql/{}/', uid, gid)
    except OSError:
        print('create dir error,please check')
    return '/data/mysql/{}'


# 接收指定的my.cnf文件，并复制到相关数据文件夹下
# TODO:自动询问关键参数，并生成my_$port.cnf


def cp_cnf(file_path, data_path):
    if os.path.exists(file_path):
        try:
            shutil.copy(file_path, data_path)
        except OSError:
            print('copy failed,please check it')
    else:
        print('file does`s not exist')


# 生成start_$port.sh启动文件
# TODO:把参数带进来，缩短cmd长度

def pre_start(port):
    cmd = 'echo /usr/local/{}/bin/mysqld --defaults-file=/data/mysql/{}/my_{}.cnf &'
    os.popen('echo')
