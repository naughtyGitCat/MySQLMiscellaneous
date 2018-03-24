# MySQL Group Replication: native support in ProxySQL【ProxySQL新版本对MGR的原生支持】

Posted by [lefred](http://lefred.be/content/author/lefred/) on March 23, 2017

作者：[lefred](http://lefred.be/content/author/lefred/) MySQL官方开发组成员

翻译：张锐志，知数堂学员

[ProxySQL](http://www.proxysql.com/) is the leader in proxy and load balancing solution for MySQL. It has great [features](http://www.proxysql.com/#features) like query caching, multiplexing, mirroring, read/write splitting, routing, etc… The latest enhancement in ProxySQL is the **native support** of **MySQL Group Replication**. No more need to use an external script within the scheduler like I explained in [this previous post](http://lefred.be/content/ha-with-mysql-group-replication-and-proxysql/).

ProxySQL在MySQL的代理和负载均衡中一直处于领先地位。其中包含了诸如缓存查询，多路复用，流量镜像，读写分离，路由等等的强力功能。在最新的功能性增强中，包含了对MGR的原生支持，不在需要使用第三方脚本进行适配。

This implementation supports Groups in Single-Primary and in Multi-Primary mode. It is even possible to setup a Multi-Primary Group but dedicate writes on only one member.

最新的增强中，提供了对单写和多写集群组的支持，甚至可以在多写组上指定只由某个成员进行写入操作。

[René](https://twitter.com/rene_cannao), the main developer of ProxySQL, went even further. For example in a 7 nodes clusters (Group of 7 members) where all nodes are writers (Multi-Primary mode), it’s possible to decide to have only 2 writers, 3 readers and 2 backup-writers. This mean that ProxySQL will see all the nodes as possible writers but will only route writes on 2 nodes (add them in the  writer hostgroup, because we decided to limit it to 2 writers for example), then it will add the others in the backup-writers group, this group defines the other writer candidates. An finally add 2 in the readers hostgroup.

ProxySQL的主要开发者René，更进一步的可以（利用ProxySQL）做到例如在一个七个节点的多写集群中，指定2组写节点，2组备用写节点，3个只读节点的操作。即ProxySQL虽然识别出来所有的节点皆为写节点，但只路由写操作到选定的两个写节点（通过Hostgroup的方式），同时将另外两个写节点添加到备用写节点组中，最后三个读节点加入读组。（本段中的组皆为ProxySQL中的hostgroup含义）。

It’s also possible to limit the access to a member that is slower in applying the replicated transactions (applying queue reaching a threshold).

除此之外，还可以限制连接访问集群中超出最大设定落后事务值的慢节点。

It is time to have a look at this new ProxySQL version. The version supporting MySQL Group Replication is 1.4.0 and currently is only available on [github](https://github.com/sysown/proxysql/tree/v1.4.0-GR) (but stay tuned for a new release soon).

ProxySQL从1.4.0版本开始增加对MGR的原生支持，若发行版中没有，可以从GitHub中编译获取。

So let’s have a look at what is new for users. When you connect to the admin interface of ProxySQL, you can see a new table: `mysql_group_replication_hostgroups`

下面我们看下对于用户来说有哪些明显的变化，开始进行admin端口连接后会发现比之前多了一个`mysql_group_replication_hostgroups`表

```
ProxySQL> show tables ;
+--------------------------------------------+
| tables                                     |
+--------------------------------------------+
| global_variables                           |
| mysql_collations                           |
| mysql_group_replication_hostgroups         |
| mysql_query_rules                          |
| mysql_replication_hostgroups               |
| mysql_servers                              |
| mysql_users                                |
...
| scheduler                                  |
+--------------------------------------------+
15 rows in set (0.00 sec)

```

This is the table we will use to setup in which hostgroup a node will belongs.

我们将在这个表中进行节点的归属组（hostgroup）的设置。

To illustrate how ProxySQL supports MySQL Group Replication, I will use a cluster of 3 nodes:

为了阐明ProxySQL 对MGR支持的原理，下面我会用到一个三节点的集群。

| name   | ip           |
| ------ | ------------ |
| mysql1 | 192.168.90.2 |
| mysql2 | 192.168.90.3 |
| mysql3 | 192.168.90.4 |

So first, as usual we need to add our 3 members into the `mysql_servers` table:

首先，我们照旧插入三个节点的信息到`mysql_servers`表中。

```
mysql> insert into mysql_servers (hostgroup_id,hostname,port) values (2,'192.168.90.2',3306);
Query OK, 1 row affected (0.00 sec)

mysql> insert into mysql_servers (hostgroup_id,hostname,port) values (2,'192.168.90.3',3306);
Query OK, 1 row affected (0.00 sec)

mysql> insert into mysql_servers (hostgroup_id,hostname,port) values (2,'192.168.90.4',3306);
Query OK, 1 row affected (0.00 sec)


mysql> select * from mysql_servers;
+--------------+--------------+------+--------+--------+-------------+-----------------+---------------------+---------+----------------+---------+
| hostgroup_id | hostname     | port | status | weight | compression | max_connections | max_replication_lag | use_ssl | max_latency_ms | comment |
+--------------+--------------+------+--------+--------+-------------+-----------------+---------------------+---------+----------------+---------+
| 2            | 192.168.90.2 | 3306 | ONLINE | 1      | 0           | 1000            | 0                   | 0       | 0              |         |
| 2            | 192.168.90.3 | 3306 | ONLINE | 1      | 0           | 1000            | 0                   | 0       | 0              |         |
| 2            | 192.168.90.4 | 3306 | ONLINE | 1      | 0           | 1000            | 0                   | 0       | 0              |         |
+--------------+--------------+------+--------+--------+-------------+-----------------+---------------------+---------+----------------+---------+

```

Now we can setup ProxySQL’s behavior with our Group Replication cluster, but before let’s check the definition of the new `mysql_group_replication_hostgroups` table:

在设置MGR节点在ProxySQL中的行为之前，先查看下新加入的`mysql_group_replication_hostgroups`表的DDL。

```
ProxySQL> show create table mysql_group_replication_hostgroups\G
*************************** 1. row ***************************
       table: mysql_group_replication_hostgroups
Create Table: CREATE TABLE mysql_group_replication_hostgroups (
    writer_hostgroup INT CHECK (writer_hostgroup>=0) NOT NULL PRIMARY KEY,
    backup_writer_hostgroup INT CHECK (backup_writer_hostgroup>=0 AND backup_writer_hostgroup<>writer_hostgroup) NOT NULL,
    reader_hostgroup INT NOT NULL CHECK (reader_hostgroup<>writer_hostgroup AND backup_writer_hostgroup<>reader_hostgroup AND reader_hostgroup>0),
    offline_hostgroup INT NOT NULL CHECK (offline_hostgroup<>writer_hostgroup AND offline_hostgroup<>reader_hostgroup AND backup_writer_hostgroup<>offline_hostgroup AND offline_hostgroup>=0),
    active INT CHECK (active IN (0,1)) NOT NULL DEFAULT 1,
    max_writers INT NOT NULL CHECK (max_writers >= 0) DEFAULT 1,
    writer_is_also_reader INT CHECK (writer_is_also_reader IN (0,1)) NOT NULL DEFAULT 0,
    max_transactions_behind INT CHECK (max_transactions_behind>=0) NOT NULL DEFAULT 0,
    comment VARCHAR,
    UNIQUE (reader_hostgroup),
    UNIQUE (offline_hostgroup),
    UNIQUE (backup_writer_hostgroup))

```

There are many new columns, let’s have a look at their meaning:

看一下之前没有出现过的新列的含义

| Column Name             | Description                                                  |
| ----------------------- | ------------------------------------------------------------ |
| writer_hostgroup        | the id of the hostgroup that will contain all the members that are writer MGR写节点都应被包含在这个组中 |
| backup_writer_hostgroup | if the group is running in multi-primary mode, there are multi writers (read_only=0) but if the amount of these writer is larger than the max_writers, the extra nodes are located in that backup writer group 在MGR多写的模式下，如果可以提供写属性的节点超过实际使用的写节点数，剩下的节点将在这个备用写节点组中存放。 |
| reader_hostgroup        | the id of the hostgroup that will contain all the members in read_only 该组将会包含所有具有只读属性的MGR节点 |
| offline_hostgroup       | the id of the hostgroup that will contain the host not being online or not being part of the Group 改组将会包含所有无法提供服务或者不处于online情况下的节点 |
| active                  | when enabled, ProxySQL monitors the Group and move the server according in the appropriate hostgroups 当该列属性启动时，ProxySQL将会监察整个集权，并根据hostgroup和节点的属性，进行匹配。 |
| max_writers             | limit the amount of nodes in the writer hostgroup in case of group in multi-primary mode 控制MGR多写模式下实际对外提供写服务的节点数量 |
| writer_is_also_reader   | boolean value, 0 or 1, when enabled, a node in the writer hostgroup will also belongs the the reader hostgroup 布尔值0或1，当启动时写节点组中的节点会同时出现在读组中 |
| max_transactions_behind | if the value is greater than 0, it defines how much a node can be lagging in applying the transactions from the Group, [see this post for more info](http://lefred.be/content/mysql-group-replication-synchronous-or-asynchronous-replication/) 定义节点最大落后整个集群的事务数量（ProxySQL内部，非MGR中的） |

Now that we are (or should be) more familiar with that table, we will set it up like this:

熟悉了表的定义后，整个拓补将会如下图所示：

![img](http://lefred.be/wp-content/uploads/2017/03/proxySQL_GR_hostgroup.png)

So let’s add this:

下面我们将MGR集群的分组定义和关键参数写入`mysql_group_replication_hostgroups`表中

```
ProxySQL> insert into mysql_group_replication_hostgroups (writer_hostgroup,backup_writer_hostgroup,
reader_hostgroup, offline_hostgroup,active,max_writers,writer_is_also_reader,max_transactions_behind) 
values (2,4,3,1,1,1,0,100);

```

We should not forget to save our mysql servers to disk and load them on runtime:

然后将新更改的配置保存到磁盘上，并加载到运行环境。

```
ProxySQL> save mysql servers to disk;
Query OK, 0 rows affected (0.01 sec)

ProxySQL> load mysql servers to runtime;
Query OK, 0 rows affected (0.00 sec)

```

It’s also important with the current version of MySQL Group Replication to add a view and its dependencies in sys schema: [addition_to_sys.sql](https://gist.github.com/lefred/77ddbde301c72535381ae7af9f968322):

同时，我们需要在MGR中添加如下的视图，及其依赖的存储过程。

```
# mysql -p < addition_to_sys.sql
```

So now from every members of the group, we can run the following statement. ProxySQL based its internal monitoring this same view:

如此，我们便可以从MGR集群中任意一个节点上执行下面的语句获取MGR成员的基本信息，ProxySQL 也是根据这个办法进行监测节点的健康与落后情况。

```
mysql> select * from gr_member_routing_candidate_status;
+------------------+-----------+---------------------+----------------------+
| viable_candidate | read_only | transactions_behind | transactions_to_cert |
+------------------+-----------+---------------------+----------------------+
| YES              | YES       |                  40 |                    0 |
+------------------+-----------+---------------------+----------------------+

```

We also must not forget to create in our cluster the ** monitor user needed by ProxySQL**:

同时，我们需要讲sys库的读权限赋给ProxySQL配置的监控MySQL的账户：

```
mysql> GRANT SELECT on sys.* to 'monitor'@'%' identified by 'monitor';

```

We can immediately check how ProxySQL has distributed the servers in the hostgroups :

接下来，我们马上检查下ProxySQL是如何将MGR节点分发到ProxySQL各个组中：

```
ProxySQL>  select hostgroup_id, hostname, status  from runtime_mysql_servers;
+--------------+--------------+--------+
| hostgroup_id | hostname     | status |
+--------------+--------------+--------+
| 2            | 192.168.90.2 | ONLINE |
| 3            | 192.168.90.3 | ONLINE |
| 3            | 192.168.90.4 | ONLINE |
+--------------+--------------+--------+

```

The Writer (Primary-Master) is mysql1 (192.168.90.2 in hostgroup 2) and the others are in the read hostgroup (id=3).

写节点被分配到之前定义好的ID为2的写组中，其他所有的节点被分配到ID为3的只读组中。（单写模式）

As you can see, there is no more need to create a scheduler calling an external script with complex rules to move the servers in the right hostgroup.

这样，我们就省掉了通过定时器去调用第三方复杂定义的脚本将MGR节点匹配并分配到对应的ProxySQL组中的操作。

Now to use the proxy, it’s exactly as usual, you need to create users associated to default hostgroup or add routing rules.

接下来，你就可以按照之前的做法对ProxySQL进行配置，例如关联用户到默认ProxySQL组中，或者添加查询路由规则。

An extra table has also been added for monitoring:

另外，ProxySQL比之前多了一个监控MySQL实例的表，具体信息如下面所示：

```
ProxySQL> SHOW TABLES FROM monitor ;
+------------------------------------+
| tables                             |
+------------------------------------+
| mysql_server_connect               |
| mysql_server_connect_log           |
| mysql_server_group_replication_log |
| mysql_server_ping                  |
| mysql_server_ping_log              |
| mysql_server_read_only_log         |
| mysql_server_replication_lag_log   |
+------------------------------------+
7 rows in set (0.00 sec)

ProxySQL> select * from mysql_server_group_replication_log order by time_start_us desc  limit 5 ;
+--------------+------+------------------+-----------------+------------------+-----------+---------------------+-------+
| hostname     | port | time_start_us    | success_time_us | viable_candidate | read_only | transactions_behind | error |
+--------------+------+------------------+-----------------+------------------+-----------+---------------------+-------+
| 192.168.90.4 | 3306 | 1490187314429511 | 1887            | YES              | NO        | 0                   | NULL  |
| 192.168.90.3 | 3306 | 1490187314429141 | 1378            | YES              | YES       | 0                   | NULL  |
| 192.168.90.2 | 3306 | 1490187314428743 | 1478            | NO               | NO        | 0                   | NULL  |
| 192.168.90.4 | 3306 | 1490187309406886 | 3639            | YES              | NO        | 0                   | NULL  |
| 192.168.90.3 | 3306 | 1490187309406486 | 2444            | YES              | YES       | 0                   | NULL  |
+--------------+------+------------------+-----------------+------------------+-----------+---------------------+-------+

```

Enjoy MySQL Group Replication & ProxySQL !

#### follow me

[Follow @lefred](https://twitter.com/intent/follow?screen_name=lefred)

[译者： @naughtyGitCat](https://github.com/naughtyGitCat)