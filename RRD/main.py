# coding=utf-8
# !/usr/bin/python
import rrdtool
import time
import psutil
# ##创建rrd
def create_rrdb():
    rrdb = rrdtool.create('rest.rrd', '--step', '60', '--start', '1369982786',
                          'DS:input:GAUGE:120:U:U',
                          'DS:output:GAUGE:120:U:U',
                          'RRA:LAST:0.5:1:600',
                          'RRA:AVERAGE:0.5:5:600',
                          'RRA:MAX:0.5:5:600',
                          'RRA:MIN:0.5:5:600')
    if rrdb:
        print rrdtool.error()

# ##rrd插入数据

def insert_data()
    for keys in psutil.network_io_counters(pernic=True):
        if keys == 'em1':
            sent = psutil.network_io_counters(pernic=True)[keys][0]
            recv = psutil.network_io_counters(pernic=True)[keys][1]
            up = rrdtool.updatev('rest.rrd', 'N:%d:%d' % (sent, recv))
            print up

# ##根据rrd绘图

def draw_graph():
    rrdtool.graph('rest.png', '--start', '1369983960',
                  '--title', 'my rrd graph test',
                  '--vertical-label', 'bits',
                  'DEF:input=rest.rrd:input:LAST',
                  'DEF:output=rest.rrd:output:LAST',
                  'LINE1:input#0000FF:In traffic',
                  'LINE1:output#00FF00:Out traffic\\r',
                  'CDEF:bytes_in=input,8,*',
                  'CDEF:bytes_out=output,8,*',
                  'COMMENT:\\n',
                  'GPRINT:bytes_in:LAST:LAST in traffic\: %6.2lf %Sbps',
                  'COMMENT: ',
                  'GPRINT:bytes_out:LAST:LAST out traffic\: %6.2lf %Sbps')