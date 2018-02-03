#!/usr/bin/python3
#coding=utf-8
import commands
def suggest(a, b, c):
    (status,output) = commands.getstatusoutput(a)
    print("######{}#######".format(b))
    print(output)
    print("*******{}*******".format(c))
suggest("df -Th|awk '{print $1,$2}'|grep -v 'tmpfs'","查看文件系统","建议data分区为xfs")
suggest("cat /sys/block/sda/queue/scheduler","查看IO调度算法","建议采用deadline算法，不要用cfg算法")
suggest("ulimit -a|grep 'open files'","查看文件打开数","建议设置为系统最大65535")
suggest("grep -i numa /var/log/dmesg","NUMA是否开启","强烈建议关闭NUMA")
suggest("sysctl -a | grep swappiness","swap占用比","建议值设置为1-10")
suggest("sysctl -a | grep dirty_ratio","dirty刷新脏页比1","设置为10比较好")
suggest("sysctl -a | grep dirty_background_ratio","dirty刷新脏页比2","设置为5比较好")