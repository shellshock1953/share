## CouchDB monitoring plugins
- **Plugin name:** {{ plugin_name }}.chart.py
- **Plugin path:** */usr/libexec/netdata/python.d/*
- **Conf names:** {{ plugin_name }}.conf
- **Conf path:** */etc/netdata/python.d/*

**Plugin would not run without .conf file.**

---
#### CouchDB_server_stats.chart.py
Collect the most useful server info, like requests methods, code statuses, I/O, etc.
##### CouchDB_server_stats.conf
```
{{ server_name }}:
 url: '{{ ip:port }}'
 priority: 70010
 retries: 60
 update_every: 1
```
* **{{ server_name }}** header name of Netdata graph with no spaces(common db_name or server_name).
* **{{ ip:port }}** CouchDB IP and port (0.0.0.0:5984)

---
#### CouchDB_active_task_counter.chart.py
1st graph represents count of all running tasks, other -- percentage per task.
##### CouchDB_active_task_counter.conf
```
{{ server_name }}:
 url: '{{ ip:port }}'
 priority: 70020
 retries: 60
 update_every: 2

 monitoring_tasks:
 - indexer
 - database_compaction
 - view_compaction
 - replication

 user: '{{ user }}'
 pass: '{{ pass }}'
```
* **{{ user / pass }}** CouchDB auth credentials

---
#### CouchDB_dbstat.chart.py
Show database info, and (if any) replication task available with those db, will show pull/push replication graph.
##### CouchDB_dbstat.conf
```
{{ server_name }}:
 url: '{{ ip:port }}'
 priority: 70030
 retries: 60
 update_every: 2

 monitoring_dbs:
 - {{ firs_db }}
 - {{ second_db }}

 monitoring_tasks:
 - indexer
 - database_compaction
 - view_compaction
 - replication

 user: '{{ user }}'
 pass: '{{ pass }}'
```
* **{{ firs_db / second_db }}** libs of databases to be monitored

---
### Installation:

`git clone {{ this_repository }} ~/.netdata_plugins`

`cd ~/.netdata_plugins`

`sudo cp *.chart.py /usr/libexec/netdata/python.d/`

Edit .conf files and place values instead of '**{{ value }}**'

`sudo cp *.conf /etc/netdata/python.d/`

`cd && rm -rf ~/.netdata_plugins`

`sudo systemctl restart netdata`

