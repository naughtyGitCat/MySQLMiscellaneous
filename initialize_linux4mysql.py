#!/usr/bin/python3
#coding=utf-8
import subprocess
def suggest(a, b, c):
    (status,output) = subprocess.getstatusoutput(a)
    print("######{}#######".format(b))
    print(output)
    print("*******{}*******".format(c))
suggest("df -Th|awk '{print $1,$2}'|grep -v 'tmpfs'","1.查看文件系统","建议data分区为xfs")
suggest("cat /sys/block/sda/queue/scheduler","2.查看IO调度算法","建议采用deadline算法，不要用cfg算法")
suggest("ulimit -a|grep 'open files'","3.查看文件打开数","建议设置为系统最大65535")
suggest("grep -i numa /var/log/dmesg","4.NUMA是否开启","强烈建议关闭NUMA")
suggest("sysctl -a | grep swappiness","5.swap占用比","建议值设置为1-10")
suggest("sysctl -a | grep dirty_ratio","6.dirty刷新脏页比1","设置为10比较好")
suggest("sysctl -a | grep dirty_background_ratio","7.dirty刷新脏页比2","设置为5比较好")

# (命令正常执行返回0，报错则返回1)
def IO_scheduler():
    x=input('输入yes进行IO调度算法的优化：')
    if x == 'yes':
        try:
            with open('/sys/block/sda/queue/scheduler','wt') as a:
                a.write('''noop [deadline] cfq''')
        except:
            print('fail,please check manually')


def open_files():
    x = input('输入yes优化文件打开数量：')
    command1 = '''echo '* soft nofile 65536' >>/etc/security/limits.conf'''
    command2 = '''echo '* hard nofile 65536' >>/etc/security/limits.conf'''
    if x == 'yes':
        print('now do:', command1)
        (status, output)=subprocess.getstatusoutput(command1)
        if status == 0:
            print('done')
        if status != 0:
            print('fail,please check manually')
        print('now do:', command2)
        (status, output)=subprocess.getstatusoutput(command2)
        if status == 0:
            print('done')
        if status != 0:
            print('fail,please check manually')

def disable_NUMA():
    x = input('输入yes关闭NUMA(需联网)：')
    command1 = '''yum -y install numactl'''
    command2 = '''numactl --interleave=all'''
    if x == 'yes':
        print('now do:', command1)
        (status, output)=subprocess.getstatusoutput(command1)
        if status == 0:
            print('done')
        if status != 0:
            print('fail,please check manually')
    if x == 'yes':
        print('now do:', command2)
        (status, output)=subprocess.getstatusoutput(command2)
        if status == 0:
            print('done')
        if status != 0:
            print('please restart system,check again')

def swappiness_ratio():
    x=input('输入yes更改swap阙值：')
    command = '''echo 'vm.swappiness = 10'>>/etc/sysctl.conf'''
    if x == 'yes':
        print('now do:', command)
        (status, output)=subprocess.getstatusoutput(command)
        if status == 0:
            print('done')
        if status != 0:
            print('fail,please check manually')


def dirty_ratio():
    x = input('输入yes更改脏页比：')
    command1 = '''echo 'm.dirty_background_ratio = 10' >>/etc/sysctl.conf'''
    command2 = '''echo 'm.dirty_ratio = 10' >>/etc/sysctl.conf'''
    command3 = '''systcl -p'''
    if x == 'yes':
        print('now do:', command1)
        (status, output)=subprocess.getstatusoutput(command1)
        if status == 0:
            print('done')
        if status != 0:
            print('fail,please check manually')

    if x == 'yes':
        print('now do:', command2)
        (status, output)=subprocess.getstatusoutput(command2)
        if status == 0:
            print('done')
        if status != 0:
            print('fail,please check manually')
    if x == 'yes':
        print('now do:', command3)
        (status, output)=subprocess.getstatusoutput(command2)
        if status == 0:
            print('done')
        if status != 0:
            print('fail,please check manually')

IO_scheduler()
open_files()
disable_NUMA()
swappiness_ratio()
dirty_ratio()
print('请重启后复查')