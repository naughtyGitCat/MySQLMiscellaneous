#!/bin/sh

INTERVAL=5
PREFIX=$INTERVAL-sec-status
RUNFILE=/root/running
mysql -e 'show global variables'>>mysql-variables
while  test -e $RUNFILE; do
	file=$(date +%F_%H)
	sleep=$(date +%s.%N |awk "{print $INTERVAL -(\$1 % $INTERVAL)}")
	sleep $sleep
	ts="$(date +"TS %s.%N %F %T")"
	loadavg="$(uptime)"
	echo "$ts $loadavg">> $PREFIX-${file}-status
	mysql -e "show global status" >> $PREFIX-${file}-status &
	echo "$ts $loadavg">> $PREFIX-${file}-innodbstatus
	mysql -e "show engine innodb status\G" >> $PREFIX-${file}-innodbstatus &
	echo "$ts $loadavg">> $PREFIX-${file}-processlist
	mysql -e "show full processlist\G" >>$PREFIX-${file}-processlist &
	echo $ts
done
echo Exiting because $RUNFILE not exist
	
