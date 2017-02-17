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
        'options': [None, 'Active tasks', 'tasks', 'Active tasks', '', 'line'],
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
        'options': [None, 'Indexer task', 'tasks', 'Indexer task', '', 'line'],
        'lines': []
    },
    'database_compaction': {
        'options': [None, 'DB compaction task', 'tasks', 'DB compaction task', '', 'line'],
        'lines': []
    },
    'view_compaction': {
        'options': [None, 'View compaction task', 'tasks', 'View compaction task', '', 'line'],
        'lines': []
    },
    'replication': {
        'options': [None, 'Replication task', 'tasks', 'Replication task', '', 'line'],
        'lines': []
    }
}


class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.couch_url = configuration['couch_url']
        self.couch_tsk = self.couch_url + '_active_tasks'
        self.couch_dbs = self.couch_url + '_all_dbs'
        if len(self.couch_url) is 0:
            raise Exception('Invalid couch url')
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
            tasks_to_monitor = ['indexer', 'database_compaction', 'view_compaction', 'replication']

            # zero values EVERY time
            for key in self.data.keys():
                self.data[key] = 0

            # open active tasks urls
            active_tasks_url = urllib2.urlopen(self.couch_tsk).read()
            active_tasks = json.loads(active_tasks_url)
            #  open dbs urls
            all_dbs_url = urllib2.urlopen(self.couch_dbs).read()
            all_dbs = json.loads(all_dbs_url)

            # init task and DBs per task presentation
            for monitoring_task in tasks_to_monitor:
                self.data[monitoring_task + '_task'] = 0
                for db in all_dbs:
                    if db[0] == '_': continue
                    self.data[monitoring_task + '_' + db] = 0
                    CHARTS[monitoring_task]['lines'].append([monitoring_task + '_' + db, db, 'absolute', 1, 1])

            # calculate running tasks
            for active_task in active_tasks:
                for monitoring_task in tasks_to_monitor:
                    if monitoring_task == active_task['type']:
                        self.data[monitoring_task + '_task'] += 1

            # calculate dbs per task
            for db in all_dbs:
                if db[0] == '_': continue
                for active_task in active_tasks:
                    try:
                        active_task_database = active_task['database']
                    except KeyError:
                        if '/' in active_task['target']:
                            active_task_database_str = active_task['target']
                            active_task_database = active_task_database_str.split('/')[3]
                        else:
                            active_task_database = active_task['target']
                    if active_task_database == db:
                        self.data[active_task['type'] + '_' + db] += 1


        except (ValueError, AttributeError):
            return None
        return self.data

# s = Service(configuration={'update_every':1,'retries':60,'priority':6000},name=None)
# s._get_data()