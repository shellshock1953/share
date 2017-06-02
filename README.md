### couchdb_active_tasks.conf

		ansible:
		 priority: 60002
		 retries: 60
		 update_every: 1
		 url: http://10.0.0.10:5984
		 monitoring_tasks:
		 - indexer
		 - database_compaction
		 - view_compaction
		 - replication

### couchdb_server_stats.conf

		ansible:
		 priority: 60001
		 retries: 60
		 update_every: 1
		 url: http://10.0.0.10:5984

### couchdb_dbstats.conf

		ansible:
		 url: http://10.0.0.10:5984

		 priority: 60003
		 retries: 60
		 update_every: 1

		 monitoring_tasks:
		 - indexer
		 - database_compaction
		 - view_compaction
		 - replication

		 monitoring_dbs:
		 - one
		 - two
		 - three
		 - four

