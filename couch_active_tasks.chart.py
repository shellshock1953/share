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
            ['i_public_production', '', 'absolute', 1, 1],
            ['i_edge', '', 'absolute', 1, 1],
        ]
    },
    'database_compaction': {
        'options': [None, 'Indexer tasks', 'tasks', '', '', 'stacked'],
        'lines': [
            ['d_public_production', '', 'absolute', 1, 1],
            ['d_edge', '', 'absolute', 1, 1],
        ]
    },
    'view_compaction': {
        'options': [None, 'Indexer tasks', 'tasks', '', '', 'stacked'],
        'lines': [
            ['v_public_production', '', 'absolute', 1, 1],
            ['v_edge', '', 'absolute', 1, 1],
        ]
    },
    'replication': {
        'options': [None, 'Indexer tasks', 'tasks', '', '', 'stacked'],
        'lines': [
            ['r_public_production', '', 'absolute', 1, 1],
            ['r_edge', '', 'absolute', 1, 1],
        ]
    }
}


class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        #self.couch_tsk = configuration['couch_tsk']
        self.couch_tsk = open('/data/shellshock/share/active_task.phalanx.json')
        # if len(self.couch_tsk) is 0:
        #     raise Exception('Invalid couch url')
        self.order = ORDER
        self.definitions = CHARTS
        self.data = {
            'indexer_task': 0,
            'database_compaction_task': 0,
            'view_compaction_task': 0,
            'replication_task': 0,

            'i_public_production': 0,
            'i_edge': 0,
            'd_public_production': 0,
            'd_edge': 0,
            'v_public_production': 0,
            'v_edge': 0,
        }


    def _get_data(self):
        try:
            doc = self.couch_tsk.read()
            tsk = json.loads(doc)
            for item in tsk:
                if item['type'] == 'indexer':
                    self.data['indexer_task'] += 1
                    if   item['database'] == 'public_production_db': self.data['i_public_production'] += 1
                    elif item['database'] == 'edge_db': self.data['i_edge'] += 1

                elif item['type'] == 'database_compaction_task':
                    self.data['database_compaction_task'] += 1
                    if   item['database'] == 'public_production_db': self.data['d_public_production'] += 1
                    elif item['database'] == 'edge_db': self.data['d_edge'] += 1

                elif item['type'] == 'view_compaction_task':
                    self.data['view_compaction_task'] += 1
                    if   item['database'] == 'public_production_db': self.data['v_public_production'] += 1
                    elif item['database'] == 'edge_db': self.data['v_edge'] += 1

                elif item['type'] == 'replication':
                    self.data['replication_task'] += 1
                    if   item['source'] == 'public_production_db': self.data['r_public_production'] += 1
                    elif item['souce'] == 'edge_db': self.data['r_edge'] += 1

        except (ValueError, AttributeError):
            return None
        return self.data

s = Service(configuration={'priority':priority,'retries':retries,'update_every':update_every},name=None)
print(s._get_data)
