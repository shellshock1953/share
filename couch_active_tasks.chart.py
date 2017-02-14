# DEBUG
# import sys
# sys.path.append('/data/shellshock/install/netdata/python.d/python_modules/')

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
    # show number of each running tasks
    'active_tasks': {
        'options': [None, 'Active tasks', 'tasks', '', '', 'stacked'],
        'lines': [
            # available tasks
            ['indexer_task', 'indexer', 'absolute', 1, 1],
            ['replication_task', 'replication', 'absolute', 1, 1],
            ['database_compaction_task', 'database_compaction', 'absolute', 1, 1],
            ['view_compaction_task', 'view_compaction', 'absolute', 1, 1]
        ]
    },
    # show number of bases per each task
    # empty lines because of dynamic chart creation
    # we dont know what dbs we will use
    'indexer': {
        'options': [None, 'Indexer tasks', 'tasks', '', '', 'stacked'],
        'lines': [ ]
    },
    'database_compaction': {
        'options': [None, 'Indexer tasks', 'tasks', '', '', 'stacked'],
        'lines': [ ]
    },
    'view_compaction': {
        'options': [None, 'Indexer tasks', 'tasks', '', '', 'stacked'],
        'lines': [ ]
    },
    'replication': {
        'options': [None, 'Indexer tasks', 'tasks', '', '', 'stacked'],
        'lines': [ ]
    }
}


class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        # self.couch_tsk = configuration['couch_tsk']
        # DEBUG
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

        }

    def _get_data(self):
        try:
            # zero values EVERY time
            self.data['indexer_task'] =0
            self.data['database_compaction_task'] =0
            self.data['view_compaction_task'] =0
            self.data['replication_task'] =0

            #TODO get all dbs
            # set dbs in .conf like a list
            all_dbs = ["edge_db","logs_db","public_sandbox","shellshock","public_production_db"]

            # inialize db tasks
            for db in all_dbs:
                self.data['indexer_'+db] = 0
                self.data['database_compaction_'+db] = 0
                self.data['view_compaction_'+db] = 0
                self.data['replication_'+db] = 0


            # DEBUG
            #doc = urllib2.urlopen(self.couch_tsk).read()
            doc = self.couch_tsk.read()
            tasks = json.loads(doc)
            for task in tasks:
                type = task['type']
                chart_name = type + '_' + db

                #TODO check db name
                # task replication has no 'database' item -- use 'target' instead
                try:
                    db = task['database']
                except KeyError:
                    db = task['target']

                #TODO make dynamic types defined in .conf ???
                if type == 'indexer':
                    self.data['indexer_task'] += 1
                    CHARTS[type]['lines'].append([chart_name, db, 'absolute', 1, 1])

                elif type == 'database_compaction':
                    self.data['database_compaction_task'] += 1
                    CHARTS[type]['lines'].append([chart_name, db, 'absolute', 1, 1])

                elif type == 'view_compaction':
                    self.data['view_compaction_task'] += 1
                    CHARTS[type]['lines'].append([chart_name, db, 'absolute', 1, 1])

                elif type == 'replication':
                    self.data['replication_task'] += 1
                    CHARTS[type]['lines'].append([chart_name, db, 'absolute', 1, 1])

        except (ValueError, AttributeError):
            return None
        return self.data


# DEBUG
# s = Service(configuration={'priority': priority, 'retries': retries, 'update_every': update_every}, name=None)
# s._get_data()
