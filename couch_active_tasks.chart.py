# DEBUG
import sys
sys.path.append('/data/shellshock/install/netdata/python.d/python_modules/')

from base import SimpleService

import json
try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

priority = 70000
retries = 60
update_every = 1

ORDER = [
    'active_tasks',
    'indexer',
    'replication',
    'database_compaction',
    'view_compaction'
]

CHARTS = {
    'active_tasks': {
        'options': [None, 'Active tasks', 'tasks', '', '', 'stacked'],
        'lines': [
            ['indexer_task', 'indexer', 'absolute', 1, 1],
            ['replication_task', 'replication', 'absolute', 1, 1],
            ['database_compaction_task', 'database_compaction', 'absolute', 1, 1],
            ['view_compaction_task', 'view_compaction', 'absolute', 1, 1]
        ]
    },
    'indexer': {
        'options': [None, 'Indexer tasks', 'tasks', '', '', 'stacked'],
        'lines': [
            ['db1', 'base name', 'absolute', 1, 1],
            ['db2', 'base name', 'absolute', 1, 1],
        ]
    },

    'replication': {
        'options': [None, 'Indexer tasks', 'tasks', '', '', 'stacked'],
        'lines': [
            ['db1', 'base name', 'absolute', 1, 1],
            ['db2', 'base name', 'absolute', 1, 1],
        ]
   },
    'database_compaction': {
        'options': [None, 'Indexer tasks', 'tasks', '', '', 'stacked'],
        'lines': [
            ['db1', 'base name', 'absolute', 1, 1],
            ['db2', 'base name', 'absolute', 1, 1],
        ]
    },
    'view_compaction': {
        'options': [None, 'Indexer tasks', 'tasks', '', '', 'stacked'],
        'lines': [
            ['db1', 'base name', 'absolute', 1, 1],
            ['db2', 'base name', 'absolute', 1, 1],
        ]
    }
}

class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        #self.couch_tsk = configuration['couch_tsk']
        self.couch_tsk = open('/data/shellshock/share/act_tks.json')
        # if len(self.couch_tsk) is 0:
        #     raise Exception('Invalid couch url')
        self.order = ORDER
        self.definitions = CHARTS

    def _get_data(self):
        try:
            doc = self.couch_tsk.readlines()
            doc_tsk = json.loads(doc)
        except (ValueError, AttributeError):
            return None
        return doc_tsk

s = Service(configuration={'priority':priority,'retries':retries,'update_every':update_every},name=None)
print(s._get_data)
