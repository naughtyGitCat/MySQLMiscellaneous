# GTID consistent reads 基于GTID的一致性读

作者：René Cannaò ProxySQL的作者

翻译：张锐志

小记：原文的标题和部分段落都有些混乱，已经尽量按作者的想法意义。所以没有和英文完全匹配逐句翻译。

[原文链接](http://www.proxysql.com/blog/proxysql-gtid-causal-reads)

# Adaptive query routing based on GTID tracking 基于GTID追踪的自适应路由查询

ProxySQL是一个工作在第七层(应用层)且支持MySQL 协议的的数据库代理，ProxySQL本身自带了高可用和高性能的功能，并且包含了丰富的功能集。在即将到来的2.0版本中的功能将会更加excited！

ProxySQL is a layer 7 database proxy that understands the MySQL Protocol. It provides high availability and high performance out of the box. ProxySQL has a rich set of features, and the upcoming version 2.0 has new exciting features, like the one described in this blog post.

ProxySQL中最常用的功能当属查询的分析统计和基于路由查询做到的读写分离。

One of the most commonly used feature is query analysis and query routing in order to provide read/write split.

当客户端连接到ProxySQL执行查询时，ProxySQL 会先根据预先设定好的路由规则进行路由检查，并分发到这条语句应该被执行的实例上。最简单的例子就是将所有的读查询全部路由到从库，所有的写查询全部路由到主库。当然，由于读查询有可能在从库上读到非最新的数据，这个案例在生产上并不是实用的。因此，我们建议将所有的请求都发到主库上，同时由于ProxySQL 对SQL统计信息的支持，DBA可以针对性的创建更加精准的路由规则，将特定的查询路由到从库。详细信息和其他案例可以参考[之前的文章](http://www.proxysql.com/blog/configure-read-write-split)

When a client connected to ProxySQL executes a query, ProxySQL will first check its rules (configured by a DBA) and determine on which MySQL server the query needs to be executed. A minimalistic example is to send all reads to slaves, and writes to master. Of course, this example is not to be used in production, because sending reads to slaves may return stale data, and while stale data is ok for some queries, it is not ok for other queries. For this reason, we generally suggest to send all traffic to master, and thanks to the statistics that ProxySQL makes available, a DBA can create more precise routing rules in which only specific set of queries are routed to the slaves. More details and examples are available in a previous [blog post](http://www.proxysql.com/blog/configure-read-write-split).

在ProxySQL支持高客制化的路由规则设定，甚至可以通过`next_query_flagIN`参数指定当前查询连接的下一个查询仍然在同一组(hostgroup)实例上执行，比如可以通过这个特性，指定插入数据语句的后面的查询语句仍然在同一个实例上被执行。但只有在DBA对应用逻辑非常清楚的情况下，才能知道哪些功能或者查询是先写后查的，因此这个特性实际应用起来比较复杂。

ProxySQL routing can be customized a lot: it is even possible to use `next_query_flagIN` to specific that after a specific query, the next query (or the next set of queries) should be executed on a determined hostgroup. For example, you can specify that after a specific `INSERT`, the following `SELECT` should be executed on the same server. Although this solution is advanced, it is also complex to configure because the DBA should know the application logic to determine which are the read-after-write queries.

# Causal consistency reads 上下文一致性读

虽然某些应用对数据实时性要求极高，但其对上下文一致性读还是兼容的，即客户端可以读到同一个ProxySQL连接中被自己修改后的数据。这个特性在MySQL默认的异步复制结构是无法保证的，异步复制情况下，在主上提交写后，从库上有可能因为传输时间占用或者执行速度的差异导致客户端并不能同时读到刚刚修改的最新数据。

Some application cannot work properly with stale data, but they can operate properly with causal consistency reads: this happens when a client is able to read the data that has written. Standard MySQL asynchronous replication cannot guarantee that. In fact, if a client writes on master, and immediately tries to read it from a slave, it is possible that the data is yet not replicated to slave.

那么我们如何保证只有当写事件被完全同步到从库后，查询才会由ProxySQL路由到从库呢？

How can we guarantee that a query is executed on slave only if a certain write event was already replicated?

基于GTID

GTID helps in this.

在MySQL 5.7.5更新后，客户端可以知道其最后写入事务的GTID，而且可以在任何当前GTID代表的事务已经被执行的从库上进行读操作。Lefred 在博客中举例描述了这个过程，如下：MySQL实例服务端开启session_track_gtids参数（这是个覆盖全局和线程级的参数，用于返回当前事务成功执行的标记和GTID编号）后，客户端就可以在从库上使用`SELECT WAIT_FOR_EXECUTED_GTID_SET('3E11FA47-71CA-11E1-9E33-C80AA9429562:1-5')`的函数来判断刚刚在主库执行的写事务是否在从库上已经被执行。

Since MySQL 5.7.5 , a client can know (in the OK packet returned by MySQL Server) which is the GTID of its last write, and can execute a read on any slave where that GTID is already executed. Lefred described the process in a [blog post](http://lefred.be/content/mysql-group-replication-read-your-own-write-across-the-group/) with an example: the server needs to have [session_track_gtids](https://dev.mysql.com/doc/refman/5.7/en/server-system-variables.html#sysvar_session_track_gtids) enabled, and the client can execute [WAIT_FOR_EXECUTED_GTID_SET](https://dev.mysql.com/doc/refman/5.7/en/gtid-functions.html#function_wait-for-executed-gtid-set) on a slave and wait for the replication to apply the event on slave.

虽然可以通过这种操作来保证上下文一致性读，但由于以下原因，这个方法对生产环境来说还是比较麻烦和不实用的：

Although this solution works, it is very trivial and not usable in production, mostly for the following reasons/drawbacks:

​	在从库上执行业务查询时每次都要加上WAIT_FOR_EXECUTED_GTID_SET的话，会增加单个查询的响应时间

- executing a query with WAIT_FOR_EXECUTED_GTID_SET before the real query will add latency before any real query

  出于效率，若想从若干个从实例中找到已经执行完指定GTID的实例，可能需要在所有的从库上都执行一遍

- the client doesn’t know which slave will be in sync first, so it needs to check many/all slaves

  很可能所有的从库在可接受的延迟等待时间内都没有完成该GTID的同步

- it is possible that none of the slaves will be in sync in an acceptable amount of time (will you wait few seconds before running the query?)

也就是说上述的操作在生产环境中并不实用

That being said, the above solution is not usable in production and is mostly a POC.

# Can ProxySQL tracks GTID? ProxySQL 可以追踪GTID吗?

由于ProxySQL饰演着MySQL客户端的角色，当`session_track_gtids` 开启后，ProxySQL 也可以跟踪所有前端发来的所有请求的GTID，而且可以准确的获知每个前端连接最后的GTID值。这样就可以使用这些信息去路由读请求到正确的从实例（指已经执行完某个线程指定的GTID事务的从实例）上。那么，ProxySQL 怎么追踪指定的GTID是否在从库上已经被执行呢？

ProxySQL acts as client for MySQL . Therefore, if `session_track_gtids` is enabled, ProxySQL can track the GTID of all the clients’ requests, and know exactly the last GTID for each client’s connection. ProxySQL can then use this information to send a read to the right slave where the GTID was already executed. How can ProxySQL track GTID executed on slaves?

大概分为两种办法：

There are mostly two approaches:

​       主动问询：ProxySQL 定期的查询所有实例的GTID执行情况

- Pull : at regular interval, ProxySQL queries all the MySQL servers to retrieve the GTID executed set

  聆听告知，每当一个新的写事件产生且GTID编号被生成后，ProxySQL 会立刻接到告知

- Push : every time a new write event is executed on a MySQL server (master or slave) and a new GTID is generated, ProxySQL is immediately notified

需要注意的是，由于每次问询之间总是有一定的间隔，导致主动问询方式总是不可避免的存在着基于问询间隔的延迟，问询的越频繁，获取的信息就越准确，但会增加MySQL实例的负载，且当ProxySQL实例过多时会占用查询带宽和流量。总而言之，理论上来说，这种办法效率又低，架构可扩展性又差。

No need to say, the pull method is not very efficient because it will almost surely introduce latency based on how frequently ProxySQL will query the MySQL servers to retrieve the GTID executed set. The less frequent the check, the less accurate it will be. The more frequent the check, the more precise, yet it will cause load on MySQL servers and inefficiently use a lot of bandwidth if there are hundreds of ProxySQL instances. In other words, this solution is not efficient neither scalable.

那么聆听告知的情况

What about pull method?

# Real time retrieval of GTID executed set 实时获取已经执行过的GTID值

从技术上来说获取当前已经执行过的GTID 值很简单，只要实时消费（分析）binlog即可。但是这种方法需要把ProxySQL实例所在的机器模拟成一个从库，如若单个ProxySQL负载了很多个MySQL实例，那么势必会对提升CPU的消耗。更进一步，如果一个机柜或者交换机上部署了很多ProxySQL 实例，那么传输binlog也会对整个网络的带宽带来考验。举个例子，现有4个集群，每个集群中的主库每天产生40GB的binlog并且挂了5个从库，附加30个ProxySQL实例，那么，每个ProxySQL实例需要把自己模拟成24个主从实例的从库。总计每天要消耗30TB的网络带宽。对自建机房的话或许可以直接纵向或者横向加硬件解决，但对云主机来说，每天将会无法避免巨额的流量费用。

Real time retrieval of GTID executed set is technically simple: consume and parse binlog in real time! Although, if ProxySQL becomes a slave of every MySQL server, it is easy to conclude that this solution will consume CPU resources on ProxySQL instance. To make things worse, in a setup with a lot of ProxySQL instances, if each ProxySQL instance needs to get replication events via replication from every MySQL server, network bandwidth will soon become a bottleneck. For example, think what will happen if you have 4 clusters, and each cluster has 1 master generating 40GB of binlog per day and 5 slaves, and a total of 30 proxysql instances. If each proxysql instance needs to become a slave of the 24 MySQL servers, this solution will consume nearly 30TB of network bandwidth in 1 day (and you don’t want this if you pay for bandwidth usage).

# ProxySQL Binlog Reader 

主动问询GTID执行情况在上个段落中被认为是没有扩展性，且消耗较大的资源的方法。ProxySQL Binlog Reader工具应运而生：

The pull method described above doesn’t scale and it consumes too many resources. For this reason, a new tool was implemented: ProxySQL Binlog Reader.

​	ProxySQL Binlog Reader是一个轻型，运行在MySQL实例机器上，且通过把自己模拟成一个从实例连接到MySQL实例的跟踪所有GTID事件的进程。

- ProxySQL Binlog Reader is a lightweight process that run on the MySQL server, it connects to the MySQL server as a slave, and tracks all the GTID events.

  ProxySQL Binlog Reader 本身就是一个服务器，每当前端连接进入时，就会开始以一个高效节省带宽的方式进行Binlog的流传输。

- ProxySQL Binlog Reader is itself a server: when a client connects to it, it will start streaming GTID in a very efficient format to reduce bandwidth.

说到这里，我想聪明的您应该猜到了ProxySQL实例饰演着ProxySQL Binlog Reader服务的客户端的角色。

By now you can easily guess who will be the clients of ProxySQL Binlog Reader: all the ProxySQL instances.

![ProxySQL Binlog Reader](http://www.proxysql.com/content/2-blog/34-proxysql-gtid-causal-reads/proxysql-binlog-reader.png)

# Real time routing 实时路由

ProxySQL Binlog Reader 让ProxySQL 可以知道每个MySQL实例当前GTID 的执行情况。那么，当客户端执行一条读写分离查询时，ProxySQL就会马上知道这个请求该被路由到哪台从服务器上。退一步说，即使当前所有的从实例都没有完成该GTID的执行，那么ProxySQL 也会明白这是个主写，从读的查询。

ProxySQL Binlog Reader allows ProxySQL to know in real time which GTID was been executed on every MySQL server, slaves and master itself. Thanks to this, when a client executes a reads that needs to provide causal consistency reads, ProxySQL immediately knows on which server the query can be executed. If for whatever reason the writes was not executed on any slave yet, ProxySQL will know that the write was executed on master and send the read there.

![ProxySQL GTID Consistency](http://www.proxysql.com/content/2-blog/34-proxysql-gtid-causal-reads/proxysql-gtid.png)

# Advanced configuration, and support for many clusters 细致的设置项，支持多集群

ProxySQL是高客制化的，本文所介绍的功能同样如此。最重要的就是可以设置读请求是否支持上下文一致性（以ProxySQL中的组为对象）。不能设置完上下文一致性就完事大吉，例如，针对一个读请求，需要指定B组对A组满足上下文一致性（这里的组指的是ProxySQL中的Hostgroup，A组应该是写组，B组则可写，可读，只要保证同一连接如果在A上写，但读被路由到B的时候，能够读到刚刚写入的操作即可）。不仅支持主从之间上下文一致性读，还支持切片集群A+切片集群B构成的A-B高可用架构中，上下文一致性读查询（被路由到A或B中），

ProxySQL is extremely configurable, and this is true also for this feature. The most important tuning is that you can configure if a read should provide causal consistency or not, and if causal consistency is required you need to specify to which hostgroup should be consistent. This last detail is very important: you don’t simply enable causal consistency, but you need to specify that a read to hostgroup B should be causal consistent to hostgroup A. This allows ProxySQL to implement the algorithm on any number of hostgroups and clusters, and also allows a single client to execute queries on multiple clusters (sharding) knowing that the causal consistency read will be executed on the right cluster.

# Requirements 要求

基于GTID的上下文一致性读需满足如下条件：

Casual reads using GTID is only possible if:

​	ProxySQL 2.0 以后的版本

- ProxySQL 2.0 is used (older versions do not support it)

  后端使用MySQL 5.7.5以上的版本，老版本不支持`session_track_gtids`

- the backend is MySQL version 5.7.5 or newer. Older versions of MySQL do not have capability to use this functionality.

  binlog格式为行格式

- replication binlog format is ROW

  开启GTID

- GTID is enabled (that sounds almost obvious).

  后端仅限于Oracle或者Percona分支的MySQL，MariaDB不支持`session_track_gtids`

- backends are either Oracle’s or Percona’s MySQL Server: MariaDB Server does not support `session_track_gtids`, but I hope it will be available soon.

# Conclusion 结论

马上就要发布的ProxySQL 2.0版本可以实时追踪复制架构中中各个实例当前的GTID执行情况。基于GITD的自适应查询路由可以满足上下文一致性读，ProxySQL 可以路由查询请求到指定的GTID已经被执行的从实例。本解决方案扩展性极佳，网络资源占用低，且已经在实际环境中进行验证。

The upcoming release of ProxySQL 2.0 is able to track executed GTID in real-time from all the MySQL servers in a replication topology. Adaptive query routing based on GTID tracking allows to provide causal reads, and ProxySQL can route reads to the slave where the needed GTID event was already executed. This solutions scales very well with limited network usage, and is being already tested in production environments.