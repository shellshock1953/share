# DEBUG
# import sys
# sys.path.append('/data/shellshock/install/netdata/python.d/python_modules')

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
        'options': [None, 'Active tasks', 'tasks', '', '', 'line'],
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
        'options': [None, 'Indexer tasks', 'tasks', '', '', 'line'],
        'lines': []
    },
    'database_compaction': {
        'options': [None, 'Indexer tasks', 'tasks', '', '', 'line'],
        'lines': []
    },
    'view_compaction': {
        'options': [None, 'Indexer tasks', 'tasks', '', '', 'line'],
        'lines': []
    },
    'replication': {
        'options': [None, 'Indexer tasks', 'tasks', '', '', 'line'],
        'lines': []
    }
}


class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.couch_dbs = configuration['couch_dbs']
        # self.couch_tsk = configuration['couch_tsk']
        self.couch_tsk = 'http://127.0.0.1:5984/_active_tasks'
        # self.couch_dbs = 'http://127.0.0.1:5984/_all_dbs'
        if len(self.couch_tsk) is 0:
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
            # zero values EVERY time
            for key in self.data.keys():
                self.data[key] = 0

            # TODO get all dbs
            # set dbs in .conf like a list
            open_db = urllib2.urlopen(self.couch_dbs).read()
            all_dbs = json.loads(open_db)
            # DEBUG
            # all_dbs = self.couch_dbs

            # TODO make dynamic types defined in .conf ???
            tasks_to_monitor = [
                'indexer',
                'database_compaction',
                'view_compaction',
                'replication'
            ]

            # inialize db tasks
            for available_db in all_dbs:
                for available_task in tasks_to_monitor:
                    self.data[available_task + '_' + available_db] = 0

            doc = urllib2.urlopen(self.couch_tsk).read()
            # DEBUG
            # doc = self.couch_tsk.read()
            running_tasks = json.loads(doc)
            for available_db in all_dbs:
                for current_running_task in running_tasks:
                    # try:
                    #     db = current_running_task['database']
                    # except KeyError:
                    #     if '/' in current_running_task['target']:
                    #         db_str = current_running_task['target']
                    #         db = db_str.split('/')[3]
                    #     else:
                    #         db = current_running_task['target']

                    task_name = current_running_task['type']
                    chart_name = task_name + '_' + available_db
                    CHARTS[task_name]['lines'].append([chart_name, available_db, 'absolute', 1, 1])

            for available_task in tasks_to_monitor:
                if task_name == available_task:
                    self.data[available_task + '_' + db] += 1
                    self.data[task_name+'_task'] += 1

        except (ValueError, AttributeError):
            return None
        return self.data

# s = Service(configuration={'priority': priority, 'retries': retries, 'update_every': update_every}, name=None)
# d = s._get_data()
# print CHARTS
