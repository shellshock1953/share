###Place all plugins into /usr/libexec/netdata/python.d/
---
##CouchDB.chart.py
/etc/netdata/python.d/couch.conf
```
lite-public:
 couch_db: 'http://0.0.0.0:5984/edge_db'
 couch_stats: 'http://0.0.0.0:5984/_stats'
```
---
##CouchDB_active_tasks.chart.py
/etc/netdata/python.d/couch_active_tasks.conf
```
lite-public:
 couch_tsk: 'http://0.0.0.0:5984/_active_tasks'
```
