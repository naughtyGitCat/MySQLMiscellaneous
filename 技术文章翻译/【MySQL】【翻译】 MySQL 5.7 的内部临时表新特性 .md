# 【MySQL】【翻译】MySQL Internal Temporary Tables in MySQL 5.7（MySQL 5.7 内部临时表）

[Alexander Rubin](https://www.percona.com/blog/author/alexanderrubin/)  | December 4, 2017 |  Posted In: [Insight for DBAs](https://www.percona.com/blog/category/dba-insight/), [MySQL](https://www.percona.com/blog/category/mysql/), [Percona Monitoring and Management](https://www.percona.com/blog/category/percona-monitoring-and-management/)

翻译:A529 张锐志 [博文地址](http://blog.51cto.com/l0vesql)

In this blog post, I investigate a case of spiking InnoDB Rows inserted in the absence of a write query, and find internal temporary tables to be the culprit.

本文中研究了在没有写查询的情况下，InnoDB行插入却因内部临时表的问题发生性能尖刺的情形。

Recently I was investigating an interesting case for a customer. We could see the regular spikes on a graph depicting “InnoDB rows inserted” metric (jumping from 1K/sec to 6K/sec), however we were not able to correlate those spikes with other activity. The innodb_row_inserted graph (picture from [PMM demo](http://pmmdemo.percona.com/)) looked similar to this (but on a much larger scale):

事情发生在我研究一个客户的案例时，在”InnoDB行插入“指标图上，发现了从1k行每秒激增到6K行每秒的尖刺，但却无法和其他活动或者现象连接起来，PMM监控图形上也有同样的反映。

![InnoDB row operations graph from PMM](https://www.percona.com/blog/wp-content/uploads/2017/08/Screen-Shot-2017-08-28-at-3.09.12-PM-1024x376.png)

Other graphs (Com_*, Handler_*) did not show any spikes like that. I’ve examined the logs (we were not able to enable general log or change the threshold of the slow log), performance_schema, triggers, stored procedures, prepared statements and even reviewed the binary logs. However, I was not able to find any single **\*write*** query which could have caused the spike to 6K rows inserted.

其他例如句柄和接口的图形都没有显示同样的尖刺，在无法开启general log的情况下，我们尝试检查了所有的日志，performance_schema，触发器，存储过程，预编译语句，甚至包括binlog后发现没有任何单个的写查询语句可以导致每秒插入飙升到6K行。

Finally, I figured out that I was focusing on the wrong queries. I was trying to correlate the spikes on the InnoDB Rows inserted graph to the DML queries (writes). However, the spike was caused by SELECT queries! But why would SELECT queries cause the massive InnoDB insert operation? How is this even possible?

在最后才发现，行插入飙升一定和DML有关的这种想法是错误的，出乎意料的是，尖刺是由于SELECT查询导致的，但为何SELECT查询会导致大量的InnoDB行插入操作呢？

It turned out that this is related to temporary tables on disk. In MySQL 5.7 the default setting for [internal_tmp_disk_storage_engine](http://dev.mysql.com/doc/refman/5.7/en/server-system-variables.html#sysvar_internal_tmp_disk_storage_engine) is set for InnoDB. That means that if the SELECT needs to create a temporary table on disk (e.g., for GROUP BY) it will use the InnoDB storage engine.

原来是与磁盘临时表有关。在MySQL 5.7版本中，内部磁盘临时表的默认引擎是InnoDB引擎，这就意味着当SELECT操作需要在磁盘上创建临时表时（例如GROUP BY操作），就会使用到InnoDB引擎。

Is that bad? Not necessarily. Krunal Bauskar published a blog post originally about the [InnoDB Intrinsic Tables performance](http://mysqlserverteam.com/mysql-5-7-innodb-intrinsic-tables/) in MySQL 5.7. The InnoDB internal temporary tables are not redo/undo logged. So in general performance is better. However, here is what we need to watch out for:

但这种尖刺就一定意味着性能的下降吗？Krunal Bauskar曾经写过一篇关于[5.7 InnoDB原生表性能](http://mysqlserverteam.com/mysql-5-7-innodb-intrinsic-tables/)的文章,InnoDB的内部临时表的操作并不会记录在redo和undo中，一般情况下相比原本MyISAM引擎的临时表性能更好点，但是仍需注意一下几点：

1. Change of the place where MySQL stores temporary tables. InnoDB temporary tables are stored in ibtmp1 tablespace file. There are a number of challenges with that:

   更改MySQL存储临时表的位置，原本InnoDB临时表被存储在ibtmp1表空间中，可能遇到以下的问题：

   - Location of the ibtmp1 file. By default it is located[ inside the innodb datadir](https://dev.mysql.com/doc/refman/5.7/en/innodb-parameters.html#sysvar_innodb_temp_data_file_path). Originally MyISAM temporary tables were stored in  tmpdir. We can configure the size of the file, but the location is always relative to InnoDB datadir, so to move it to tmpdir we need something like this: innodb_temp_data_file_path=../../../tmp/ibtmp1:12M:autoextend

     ibtmp1文件默认保存在InnoDB的数据目录，原本MyISAM临时表被放在MySQL的tmp目录，如若像MyISAM一样把临时表文件存储在MySQL的tmp目录，需要更改为`innodb_temp_data_file_path=../../../tmp/ibtmp1:12M:autoextend`

   - Like other tablespaces it never shrinks back (though it is truncated on restart). The huge temporary table can fill the disk and hang MySQL ([bug opened](https://bugs.mysql.com/bug.php?id=82556)). One way to fix that is to set the maximum size of ibtmp1 file:  innodb_temp_data_file_path=ibtmp1:12M:autoextend:max:1G

     临时表空间和其他的表空间一样都不会自动缩小其占用容量，可能会发生临时表空间容量占满磁盘，MySQL挂掉的情况，可以通过控制其最大的容量来解决：` innodb_temp_data_file_path=ibtmp1:12M:autoextend:max:1G`

   - Like other InnoDB tables it has all the InnoDB limitations, i.e., InnoDB row or column limits. If it exceeds these, it will return [“Row size too large” or “Too many columns” errors](https://dev.mysql.com/doc/refman/5.7/en/server-system-variables.html#sysvar_internal_tmp_disk_storage_engine). The workaround is to set internal_tmp_disk_storage_engine to MYISAM.

     内部临时InnoDB表同样共享常规的InnoDB表的限制，如行或列的最大数量限制，超过最大值后，会返回Row size too large” or “Too many columns”的错误，遇到此种情况，可以将默认临时表引擎改回MyISAM

2. When all temp tables go to InnoDB, it may increase the total engine load as well as affect other queries. For example, if originally all datasets fit into buffer_pool and temporary tables were created outside of the InnoDB, it will not affect the**\* InnoDB*** memory footprint. Now, if a huge temporary table is created as an InnoDB table it will use innodb_buffer_pool and may “evict” the existing pages so that other queries may perform slower.

   当所有的临时表都改成InnoDB引擎后，会增加引擎的负载，影响到其他的查询。例如：当所有的表都放入buffer_pool中，且临时表都不是InnoDB引擎，那么不会对InnoDB的内存占用造成任何影响，但是临时表改成InnoDB引擎后，会和普通InnoDB表一样占用InnoDB_buffer_pool的空间，而且可能因为临时表空间占用过大挤出真正的热数据，让某些高频查询变慢

#### Conclusion 结论

Beware of the new change in MySQL 5.7, the internal temporary tables (those that are created for selects when a temporary table is needed) are stored in InnoDB ibtmp file. In most cases this is faster. However, it can change the original behavior. If needed, you can switch the creation of internal temp tables back to MyISAM:  set globalinternal_tmp_disk_storage_engine=MYISAM

内部InnoDB临时表（可能仅仅因为是SELECT查询导致）被保存在InnoDB的ibtmp文件中，在大部分情况下，会加速临时表或者查询的速度，但是会影响到原本InnoDB内存的占用情况和原本临时表处理的逻辑，如果在某种情况确实需要规避的话，可以尝试将临时表的引擎改回MyISAM。`set global internal_tmp_disk_storage_engine=MYISAM` 。这个案例要求我们要对MySQL 5.7的特性要有所注意和了解。