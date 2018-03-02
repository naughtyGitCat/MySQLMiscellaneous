# 第三章：服务器性能剖析

​	本章将针对如下三个问题进行解答：

​		如何确认服务器是否达到了性能最佳的状态

​		找出某条语句为什么执行不够快

​		诊断被用户描述成“停顿”，“堆积”，“卡死”的某些间歇性疑难故障

## 1.性能优化简介：

​		针对性能问题，1000个DBA，有1000个回答。诸如，“QPS”,"CPU Load"，“可扩展性”之类。

##### 		原则一：我们将性能定义为完成某件任务所需要的时间度量。即：“性能就是响应时间” 。

​		通过任务和时间来度量性能而不是资源。数据库的目的是执行SQL语句，上句中的“任务”即是查询或者SQL语句（SELECT UPDATE DELETE等等），综上，数据库服务器的性能用查询的响应时间度量，单位则是每个查询所花费的时间。在这里我们先假设性能优化就是在一定工作负载的情况下尽可能的降低响应时间。

​		CPU使用率只是一种现象，而不是很好的可度量的目标。

​		吞吐量的提升可以看作性能优化的副产品，对查询的优化可以让服务器每秒执行更多的查询。因为每秒查询执行的时间更短了。（吞吐量即是性能的倒数：单位时间内查询的数量，QPS,QPM等等）

##### 		原则二：无法测量就无法有效地优化。第一步应当测量时间花在什么地方。

​		完成一项任务所需要的时间可以分成两部分：执行时间和等待时间。

​		如果要优化任务的执行时间，最好的办法是通过测量定位不同的子任务花费的时间，然后优化去掉一些子任务，降低子任务的执行频率或者提升子任务的执行效率。

​		如果要优化任务的等待时间，则相对复杂一些，等待可能是因为其他系统间接影响所致。

### 1.1.通过性能剖析进行优化。

​		性能剖析（Profiling）分为两个步骤：先测量任务所花费的时间，然后对结果进行统计和排序，讲重要的任务排到前面。

​		性能剖析报告会列出所有任务列表。每行记录一个任务，包括任务名，任务的执行时间，任务的消耗时间，任务的平均时间，以及该任务执行时间占全部时间的百分比。

​		基于执行时间的分析研究的是什么任务的执行时间最长。

​		基于等待的分析则是判断任务在什么阶段被阻塞的时间最长。

​		事实上，当基于执行时间的分析发现一个任务需要花费时间花费太多时间的时候，应该深入去分析一下，可能会发现某些“执行时间”其实是在等待。

### 1.2.理解性能剖析

​	尽管性能剖析输出了排名，总计和平均值，但还是有许多重要的信息是缺失的。

​	值得优化的查询：一些只占总响应时间比重很小的查询是不值得优化的。如果花费了1000美元去优化一个任务，单业务的收入没有任何增加，那么可以说是打水漂了。如果优化的成本大于收益，就应当停止优化。

​	异常情况:某些任务即使没有出现在性能剖析输出的前面也需要优化。比如，某些任务执行次数很少，单每次执行都非常慢，严重影响用户体验。

​	被掩藏的细节：性能剖析无法显示所有响应时间的冯部，只相信平均值是非常危险的。正如医院内所有病人的平均体温一样毫无意义。

## 2.对应用系统进行性能剖析

​	实际上，剖析应用程序一般比剖析数据库服务器更容易，且回报率更高。建议对系统进行自上而下的性能分析，这样可以追踪自用户发起到服务器响应的整个流程，虽然性能问题大多数情况下都和数据库有关，但是应用导致的问题也不少。

```shell
# 应该尽可能地测量一切可以测量的地方，并且接受这些测量带来的额外开销。
# Oracle 的性能优化大师Tom Kyte 曾被问到Oracle中的测量点开销，他的回答是，测量点至少为性能优化共享10%
# 大多数应用并不需要每天都运行详尽的性能测量，所以实际上贡献至少超过10%
```

## 3.剖析MySQL查询

### 3.1剖析服务器负载

​	MySQL的每一个新版本都增加了更多的可测量点。但是如果只是需要剖析并找出和代价高的查询，慢查询日志应该就能满足我们的需求。可以通过将"long_query_time"设为0来捕获所有的查询，并且查询的响应时间已经可以做到微秒级 。在当前的版本中，慢日志是开销最低，同时精度最高的测量查询时间的工具。如果长期开启慢查询日志，主要要配合logrotate工具一同使用（

[使用logrotate工具切割MySQL日志与慢日志分析发送到邮箱]: http://blog.51cto.com/l0vesql/2047599

）。Percona分支的MySQL比起官方社区版本记录了更多更有价值的信息。如查询计划，锁，I/O活动等。总的来说，慢日志是一种轻量且全面的性能剖析工具。

​	可以使用pt-query-digest分析慢查询日志，如下图：

```shell
pt-query-digest slow.log >slow_log_analyze.log
	/data/mysql/3109/slow.log:  53% 00:25 remain
	/data/mysql/3109/slow.log:  98% 00:00 remain

cat slow_log_analyze.log
# 75.3s user time, 2s system time, 41.28M rss, 235.76M vsz
# Current date: Sun Feb 25 15:43:11 2018
# Hostname: MySQL-Cent7-IP001109
# Files: /data/mysql/3109/slow.log
# Overall: 445.27k total, 59 unique, 0.03 QPS, 0.04x concurrency _________
# Time range: 2017-09-28T16:00:25 to 2018-02-25T07:27:18
# Attribute          total     min     max     avg     95%  stddev  median
# ============     ======= ======= ======= ======= ======= ======= =======
# Exec time        461284s   100ms    150s      1s      3s      1s   740ms
# Lock time          1154s       0     10s     3ms    57us    83ms    21us
# Rows sent        426.70M       0   9.54M 1004.84   97.36  76.26k    0.99
# Rows examine     465.04M       0   9.54M   1.07k  299.03  76.26k    0.99
# Query size         4.55G       6 1022.79k  10.71k   76.28  73.23k   36.69

# Profile
# Rank Query ID           Response time     Calls  R/Call  V/M   Item
# ==== ================== ================= ====== ======= ===== =========
#    1 0x558CAEF5F387E929 238431.3966 51.7% 294383  0.8099  0.62 SELECT sbtest?
#    2 0x84D1DEE77FA8D4C3  53638.8398 11.6%  33446  1.6037  1.14 SELECT sbtest?
#    3 0x3821AE1F716D5205  53362.1845 11.6%  33504  1.5927  1.11 SELECT sbtest?
#    4 0x737F39F04B198EF6  53244.4816 11.5%  33378  1.5952  1.14 SELECT sbtest?
#    5 0x6EEB1BFDCCF4EBCD  53036.2877 11.5%  33539  1.5813  1.10 SELECT sbtest?
#    6 0x67A347A2812914DF   2619.2344  0.6%    200 13.0962 67.98 SELECT tpcc?.order_line
#    7 0x28FC5B5D583E2DA6   2377.9580  0.5%    215 11.0603 11.53 SHOW GLOBAL STATUS
#   10 0xE730A9F41A4AB139    259.9002  0.1%    355  0.7321  0.42 SHOW INNODB STATUS
#   11 0x88901A51719CB50B    131.1035  0.0%     39  3.3616 21.74 SELECT information_schema.tables
#   12 0x16F46891A99F2C89    127.1865  0.0%     88  1.4453  1.15 SELECT performance_schema.events_statements_history
#   14 0x153F1CE7D660AE82     79.2867  0.0%     46  1.7236  1.47 SELECT information_schema.processlist
# MISC 0xMISC               3976.0946  0.9%  16077  0.2473   0.0 <47 ITEMS>

# Query 1: 0.17 QPS, 0.14x concurrency, ID 0x558CAEF5F387E929 at byte 4877477857
# This item is included in the report because it matches --limit.
# Scores: V/M = 0.62
# Time range: 2018-02-03T11:26:24 to 2018-02-23T13:03:23
# Attribute    pct   total     min     max     avg     95%  stddev  median
:

```

​		

​	除了慢日志之外Percona Toolkit工具包中的pt-query-digest工具也可以进行剖析，使用--processlist参数可以不断的分析"show processlist"的输出。但是“show processlist”的输出瞬息万变。即使每秒收集一次仍会遗漏很多有用的信息，因此并不十分推荐这种方式。另一种方式是使用--type=tcpdump选项对网络抓包数据进行分析。

### 3.2 剖析单条查询

#### 	使用SHOW PROFILE

​	默认禁用，但它是会话级别的参数。`set profiling=1` ，然后在服务器上直送所有的语句，都会测量其耗费的时间和其他一些查询执行状态变更相关的数据。

​	当一条查询提交给服务器时，此工具会记录剖析信息到一张临时表，并给查询赋一个从1开始的整数标识符。

​	如：

```mysql
set profiling=1
select * from t_Order;
select * from t_Product
show profiles
+----------+------------+-------------------------+
| Query_ID | Duration   | Query                   |
+----------+------------+-------------------------+
| 1        | 9.75e-05   | SHOW WARNINGS           |
| 2        | 0.00052075 | select * from t_order   |
| 3        | 0.000511   | select * from t_product |
| 4        | 5.3e-05    | SHOW WARNINGS           |
+----------+------------+-------------------------+
show profile for query 3
+----------------------+----------+
| Status               | Duration |
+----------------------+----------+
| starting             | 0.000065 |
| checking permissions | 0.000009 |
| Opening tables       | 0.000142 |
| init                 | 0.000022 |
| System lock          | 0.000010 |
| optimizing           | 0.000008 |
| statistics           | 0.000013 |
| preparing            | 0.000012 |
| executing            | 0.000007 |
| Sending data         | 0.000154 |
| end                  | 0.000010 |
| query end            | 0.000011 |
| closing tables       | 0.000010 |
| freeing items        | 0.000016 |
| cleaning up          | 0.000012 |
+----------------------+----------+
```

​	剖析报告给出了查询执行的每个步骤及其花费的时间，看结果很难快速地确定哪个步骤花费的时间最多。输出是按照执行顺序进行排序，而不是按照花费的时间排序的。下面给出使用INFORMATION_SHCEMA来查询剖析报告的办法：

```mysql
set @query_id=1
SELECT STATE,SUM(DURATION) AS  Total_R,
	ROUND(
    100*SUM(DURATION)/(SELECT SUM(DURATION) FROM INFORMATION_SCHEMA.PROFILING WHERE QUERY_ID = @query_id),2		
    ) AS Pct_R,COUNT(*) AS Calls,SUM(DURATION)/COUNT(*) AS "R/Call"
FROM INFORMATION_SCHEMA.PROFILING
WHERE QUERY_ID=@query_id
GROUP BY STATE
ORDER BY Total_R DESC
# 输出如下：
+----------------------+----------+-------+-------+--------------+
| STATE                | Total_R  | Pct_R | Calls | R/Call       |
+----------------------+----------+-------+-------+--------------+
| starting             | 0.000072 | 20.45 | 1     | 0.0000720000 |
| Sending data         | 0.000047 | 13.35 | 1     | 0.0000470000 |
| init                 | 0.000030 | 8.52  | 1     | 0.0000300000 |
| Opening tables       | 0.000026 | 7.39  | 1     | 0.0000260000 |
| checking permissions | 0.000025 | 7.10  | 1     | 0.0000250000 |
| cleaning up          | 0.000023 | 6.53  | 1     | 0.0000230000 |
| System lock          | 0.000019 | 5.40  | 1     | 0.0000190000 |
| statistics           | 0.000018 | 5.11  | 1     | 0.0000180000 |
| preparing            | 0.000016 | 4.55  | 1     | 0.0000160000 |
| optimizing           | 0.000015 | 4.26  | 1     | 0.0000150000 |
| freeing items        | 0.000014 | 3.98  | 1     | 0.0000140000 |
| query end            | 0.000013 | 3.69  | 1     | 0.0000130000 |
| closing tables       | 0.000012 | 3.41  | 1     | 0.0000120000 |
| executing            | 0.000011 | 3.13  | 1     | 0.0000110000 |
| end                  | 0.000011 | 3.13  | 1     | 0.0000110000 |
+----------------------+----------+-------+-------+--------------+
#通过这个结果可以很容易看到查询时间长主要是因为花了很大时间在sending data上
#这个状态 代表的原因非常多，可能是各种不同的服务器活动，包括在关联时搜索匹配的行记录等，这部分很难说能优化节省多少消耗的时间。
#若Sorting result花费的时间比较多，则可以考虑增大sort buffer size
```

#### 	使用show status

​	MySQL的`show status` 命令返回了一些计数器，既有服务器级别的全局技术去，也有基于某个连接的会话级别的计数器。MySQL官方手册对与所有的变量是全局还是会话级别的做了详细的说明。

​	`show status`的大部分结果都是一个计数器，可以显示某些活动如读索引的频繁程度，但无法给出消耗了多少时间。`show status`的结果中只有一条Innodb_row_lock_time指的是操作时间，而且这个是全局性的，还是无法测量会话级别的工作。最有用的计数器包括句柄计数器，临时文件和表计数器等。将会话级别的计数器重置为0，然后查询前面提到的视图，再检查计数器的结果：

```mysql
flush status;
select * from sakila.nicer_but_slower_film_list;
#...............
show status where variable_name like "Handler%" or Variable_name like "Created%";
+----------------------------+-------+
| Variable_name              | Value |
+----------------------------+-------+
| Created_tmp_disk_tables    | 2     |
| Created_tmp_files          | 2     |
| Created_tmp_tables         | 3     |
| Handler_commit             | 1     |
| Handler_delete             | 0     |
| Handler_discover           | 0     |
| Handler_external_lock      | 10    |
| Handler_mrr_init           | 0     |
| Handler_prepare            | 0     |
| Handler_read_first         | 3     |
| Handler_read_key           | 12942 |
| Handler_read_last          | 0     |
| Handler_read_next          | 6462  |
| Handler_read_prev          | 0     |
| Handler_read_rnd           | 5462  |
| Handler_read_rnd_next      | 6478  |
| Handler_rollback           | 0     |
| Handler_savepoint          | 0     |
| Handler_savepoint_rollback | 0     |
| Handler_update             | 0     |
| Handler_write              | 0     |
+----------------------------+-------+
```

从结果可以看到该查询使用了三个临时表，其中两个是磁盘临时表，并且有很多的没有用到索引的读操作（Handler_read_rnd_next）。假设我们不知道这个视图的具体定义，仅从结果来推测，这个查询可能做了多表关联查询，且没有合适的索引，可能是其中一个子查询创建了临时表，然后和其他表做联合查询，而用于保存子查询结果的临时表没有索引。

​	但是，请注意，使用`show status`本身也会创建一个临时表，而且也会通过句柄操作访问此临时表，也会影响到`show status`结果中对应的数字，而且不同的版本可能行为也不尽相同，比较前面通过`show profiles`获得的查询的的执行计划结果来看，至少临时表的计数器多加了2。
​	通过`explain`看到的查询执行计划也可以获得和`show status`大部分相同的信息，但是通过`explain`是估计得到的结果，而通过`show status`则是实际测量的结果。比如，`explain`无法告诉你临时表是否是磁盘表。

#### 	使用performance_schema和sys视图库

​	在5.6中，引入了成熟的performance_schema视图库，在5.7时为了方便performance_schema的使用，引入了建立在performance_schema上面的sys库。通过sys库，我们可以方便的观测很多基础数据，同时，可以使用MySQL WorkBench来方便的查看。如图：



