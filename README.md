## CouchDB monitoring plugins
- **Plugin name:** {{ plugin_name }}.chart.py
- **Plugin path:** */usr/libexec/netdata/python.d/*
- **Conf names:** {{ plugin_name }}.conf
- **Conf path:** */etc/netdata/python.d/*

**Plugin would not run without .conf file.**

---
#### couchdb.chart.py
Collect the most useful info, like requests methods, code statuses, I/O, etc.
##### couchdb.conf
```
{{ graph_name }}:
 couch_url: 'http://0.0.0.0:5984/'
 couch_db: '{{ db_name }}'
```
* **{{ graph_name }}** header name of Netdata graph (common db_name).
* **{{ db_name }}** database name for collecting database fragmentation and documents statistics.

---
#### couchdb_active_tasks.chart.py
Show 5 graph: 1st represents count of all running tasks, other -- databases per task.
**Databases with names starting with '_' are passing.**
##### couchdb.conf
```
{{ graph_name }}:
 couch_url: 'http://0.0.0.0:5984/'
```
* **{{ graph_name }}** header name of Netdata graph (common db_name).

---
### Installation:

`git clone {{ this_repository }} ~/.netdata_plugins`

`cd ~/.netdata_plugins`

`sudo cp *.chart.py /usr/libexec/netdata/python.d/`

`sudo cp *.conf /etc/netdata/python.d/`

`cd && rm -rf ~/.netdata_plugins`

`sudo systemctl restart netdata`

