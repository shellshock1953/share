# -*- coding: utf-8 -*-
# Description: CouchDB ACTIVE TASKS counter Netdata plugin
# specify 'http://IP:PORT/' in conf.file
#
# more info: github.com/shellshock1953/share


# import sys
# sys.path.append('/data/shellshock/install/netdata/python.d/python_modules')

from base import SimpleService
import json

try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

priority = 70010
retries = 60
update_every = 10

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

        self.tasks_to_monitor = ['indexer', 'database_compaction', 'view_compaction', 'replication']
        # self.couch_url = configuration['couch_url']
        self.couch_url = 'http://127.0.0.1:5984/'
        if len(self.couch_url) is 0: raise Exception('Invalid couch url')

        self.couch_active_task_url = self.couch_url + '_active_tasks'
        self.couch_all_dbs_url = self.couch_url + '_all_dbs'

        self.refresh()

        self.new_source_replications = []
        self.order = ORDER
        self.definitions = CHARTS
        self.new_tasks = []
        self.data = {
            'indexer_task': 0,
            'database_compaction_task': 0,
            'view_compaction_task': 0,
            'replication_task': 0,
        }

    # get fresh data
    def refresh(self):
        # open active tasks urls
        active_tasks_url = urllib2.urlopen(self.couch_active_task_url).read()
        # active_tasks_url = open('active_task.phalanx.json').read()
        self.active_tasks = json.loads(active_tasks_url)
        #  open dbs urls
        all_dbs_url = urllib2.urlopen(self.couch_all_dbs_url).read()
        self.all_dbs = json.loads(all_dbs_url)

    # from 'http://ip:port/db' cut 'db' only
    def fix_database_name(self, database_name):
        if '/' in database_name:
            fixed_database_name = database_name.split('/')[3]
            return fixed_database_name
        else:
            return database_name

    # check() calls once -- before run()
    def check(self):
        # no need to refresh() -- first start
        try:
            # init task and DBs per task presentation
            """ creating dynamic counter charts """
            for monitoring_task in self.tasks_to_monitor:
                self.data[monitoring_task + '_task'] = 0
                for db in self.all_dbs:
                    if db[0] == '_': continue
                    self.data[monitoring_task + '_' + db] = 0
                    self.definitions[monitoring_task]['lines'].append(
                        [monitoring_task + '_' + db, db, 'absolute', 1, 1])

                    """ creating defacto-dynamic task percentage charts """
                    percentage_chart_name = monitoring_task + '_percentage'
                    if percentage_chart_name not in self.order:
                        self.order.append(percentage_chart_name)
                    self.definitions.update({
                        percentage_chart_name: {
                            'options': [None, 'Task progress', 'percentage', 'Task progress', '', 'line'],
                            'lines': []
                        }
                    })

            return True
        except:
            self.error("err in check()")
            return False

    def add_lines_to_percentage_charts(self, task_type, chart_var):
        self.definitions[task_type + '_percentage']['lines'].append(
            [chart_var, chart_var, 'absolute', 1, 1]
        )
        # TODO: don`t iterate like this
        self.create()
        # for line in self.definitions[task_type + '_percentage']['lines']:
        #     self.dimension(*line)
        # self.commit()

    def _get_data(self):

        try:
            # get fresh data
            self.refresh()

            # zero values EVERY time
            for key in self.data.keys():
                self.data[key] = 0

            """ calculate running active tasks """
            for active_task in self.active_tasks:
                for monitoring_task in self.tasks_to_monitor:
                    if monitoring_task == active_task['type']:
                        self.data[monitoring_task + '_task'] += 1

            """ calculate dbs per task """
            for db in self.all_dbs:
                if db[0] == '_': continue
                for active_task in self.active_tasks:
                    try:
                        active_task_database = active_task['database']
                    except KeyError:
                        active_task_database = self.fix_database_name(active_task['target'])

                    try:
                        if active_task_database == db:
                            self.data[active_task['type'] + '_' + db] += 1
                    except IndexError:  # it`s percentage data
                        pass

                    """ calculate task percentage """
                    task_type = active_task['type']

                    #  indexer / view_compaction
                    if task_type == 'indexer' or task_type == 'view_compaction':
                        if db == active_task_database:
                            progress = active_task['progress']
                            design_document = active_task['design_document']
                            if design_document[0] == '_':
                                design_document = design_document[1:]
                            design_document = design_document.replace('/', '.')
                            chart_var = db + '_' + task_type + '_' + design_document
                            if not self.data.has_key(chart_var): self.new_tasks.append()
                            self.data[chart_var] = progress

                    # database_compaction
                    elif task_type == 'database_compaction':
                        if db == active_task_database:
                            progress = active_task['progress']
                            chart_var = db + '_' + task_type
                            if not self.data.has_key(chart_var): self.add_lines_to_percentage_charts(task_type,
                                                                                                     chart_var)
                            self.data[chart_var] = progress

                    # replication
                    elif task_type == 'replication':
                        if db == active_task_database:
                            progress = active_task['progress']
                            source_raw = active_task['source']
                            source = self.fix_database_name(source_raw)
                            chart_var = db + '_' + task_type + '_' + source
                            if not self.data.has_key(chart_var): self.add_lines_to_percentage_charts(task_type,
                                                                                                     chart_var)
                            self.data[chart_var] = progress

        except (ValueError, AttributeError):
            self.error('error in _get_data()')
            return None
        return self.data


# s = Service(configuration={'priority': 60000, 'retries': 60, 'update_every': 1}, name=None)
# s.check()
# s.create()
# s.update(1)
# s.run()
# print s.definitions
