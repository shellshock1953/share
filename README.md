## CouchDB monitoring plugins
- **Plugin name:** {{ plugin_name }}.chart.py
- **Plugin path:** */usr/libexec/netdata/python.d/*
- **Conf names:** {{ plugin_name }}.conf
- **Conf path:** */etc/netdata/python.d/*

**Plugin would not run without .conf file.**

---
#### couchdb_stats.chart.py
Collect the most useful server info, like requests methods, code statuses, I/O, etc.
##### couchdb_stats.conf
```
{{ graph_name }}:
 couch_url: 'http://{{ ip:port }}/'
```
* **{{ graph_name }}** header name of Netdata graph with no spaces(common db_name).
* **{{ ip:port }}** CouchDB IP and port (0.0.0.0:5984)

---
#### couchdb_active_task_counter.chart.py
Show 5 graph: 1st represents count of all running tasks, other -- databases per task.
**Databases with names starting with '_' are passing.**
##### couchdb_active_task_counter.conf
```
{{ graph_name }}:
 couch_url: 'http://{{ ip:port }}/'
```
* **{{ graph_name }}** header name of Netdata graph with no spaces(common db_name).
* **{{ ip:port }}** CouchDB IP and port (0.0.0.0:5984)

---
#### couchdb_dbstat.chart.py
Show database info, and (if any) replication info, where selected base is a target (can be changed in near future). You can specify as many dbs you need (check conf)
##### couchdb_dbstat.conf
```
{{ first_db_name }}:
 couch_url: 'http://{{ ip:port }}/'
 db: '{{ database_name }}'

{{ second_db_name }}:
 couch_url: 'http://{{ ip:port }}/'
 db: '{{ database_name }}'
```
* **{{ first_db_name }}** first db to be monitored
* **{{ second_db_name }}** second db to be monitored
* **{{ ip:port }}** CouchDB IP and port (0.0.0.0:5984)
* **{{ database_name }}** database name used to be monitored

---
### Installation:

`git clone {{ this_repository }} ~/.netdata_plugins`

`cd ~/.netdata_plugins`

`sudo cp *.chart.py /usr/libexec/netdata/python.d/`

Edit .conf files and place values instead of '**{{ value }}**'

`sudo cp *.conf /etc/netdata/python.d/`

`cd && rm -rf ~/.netdata_plugins`

`sudo systemctl restart netdata`

