#!/usr/bin/env bash
PLUGIN_PATH=/usr/libexec/netdata/python.d/
CONF_PATH=/etc/netdata/python.d/
scp couchdb_*.conf root@10.0.0.50:$CONF_PATH
scp couchdb_*.py root@10.0.0.50:$PLUGIN_PATH
