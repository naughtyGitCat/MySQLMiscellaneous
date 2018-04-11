#!/usr/bin/env bash
mysqladmin ext -i1 |awk '
/Queries/{q=$4-qp;qp=$4}
/Threads_connected/{tc=$4}
/Threads_running/{printf "%5d %5d %5d\n",q, tc, $4}'
#输出如下：
#   19     7     2
#   15     7     2
#   21     7     2
#   19     7     2
#   32     7     2
#   18     7     2
#   19     7     2
#   20     7     2
#   15     7     2
#   30     7     2
#   21     7     2
#   18     7     2
#这个命令每秒捕获一次show global status的数据，输出给awk计算并输出每秒的查询数，连接线程，活跃线程。
#这三个数据的趋势对于数据库级别偶尔停顿的敏感性很高。
