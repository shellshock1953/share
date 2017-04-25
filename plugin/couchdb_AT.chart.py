# import sys
# sys.path.append('/data/shellshock/install/netdata/python.d/python_modules/')

from base import UrlService
import pdb
import base64
import json

try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

ORDER = [
    'active_tasks',
    'indexer_percentage',
    'replication_percentage',
    'database_compaction_percentage',
    'view_compaction_percentage'
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
    # show percentage per dbs
    'indexer_percentage': {
        'options': [None, 'Indexer task', 'percentage', 'Indexer task percentage', '', 'line'],
        'lines': []
    },
    'database_compaction_percentage': {
        'options': [None, 'DB compaction task', 'percentage', 'DB compaction task percentage', '', 'line'],
        'lines': []
    },
    'view_compaction_percentage': {
        'options': [None, 'View compaction task', 'percentage', 'View compaction task percentage', '', 'line'],
        'lines': []
    },
    'replication_percentage': {
        'options': [None, 'Replication task', 'percentage', 'Replication task percentage', '', 'line'],
        'lines': []
    }
}


class Service(UrlService):
    def __init__(self, configuration=None, name=None):
        self.ERROR = False
        UrlService.__init__(self, configuration=configuration, name=name)
        # self.monitoring_tasks = ['indexer', 'database_compaction', 'view_compaction', 'replication']
        self.monitoring_tasks = self.configuration.get('monitoring_tasks')
        self.order = ORDER
        self.definitions = CHARTS

        self.baseurl = str(self.configuration.get('url'))
        # self.all_dbs_url = str(self.baseurl + '_all_dbs/')
        self.active_tasks_url = str(self.baseurl + '_active_tasks/')

        self.untrack_dbs = self.configuration.get('untrack_dbs', ['_replicator', '_users'])

        self.user = self.configuration.get('user') or None
        self.password = self.configuration.get('pass') or None
        if self.user:
            self.base64string = base64.encodestring('%s:%s' % (self.user, self.password)).replace('\n', '')

        self.data = {}
        for task in self.monitoring_tasks:
            self.data[task + '_task'] = 0

    # def _get_all_dbs(self):
    #     self.url = self.all_dbs_url
    #     all_dbs = self._get_raw_data()
    #     return all_dbs

    def _get_active_tasks(self):
        # pdb.set_trace()
        self.ERROR = False
        self.url = self.active_tasks_url
        try:
            request = urllib2.Request(self.url)
            if self.user:
                request.add_header("Authorization", "Basic %s" % self.base64string)
            active_tasks_url = urllib2.urlopen(request).read()
            active_tasks = json.loads(active_tasks_url)
        except IOError:
            self.error('Cant connect to couchdb. Check db is running and auth data is correct')
            self.ERROR = True
        return active_tasks

    def _get_data(self):
        def get_host_and_db(url):
            import re
            if 'http' in url:
                if '@' in url:
                    # http://chronograph:*****@localhost:5984/openprocurement_chronograph/
                    source = re.split('/|:|@', url)[5]
                    db = re.split('/|:|@', url)[7]
                else:
                    # http://localhost:5984/openprocurement_chronograph/
                    source = re.split('/|:|@', url)[3]
                    db = re.split('/|:|@', url)[5]
            else:
                source = 'localhost'
                db = url
            return source, db

        def check_new_data(task, chart_var):
            if chart_var not in self._dimensions:
                self.append_new_lines(task, chart_var)

        # zero values EVERY time
        for key in self.data.keys():
            self.data[key] = 0

        # refresh
        # all_dbs = self._get_all_dbs()
        active_tasks = self._get_active_tasks()
        if self.ERROR:
            self.error('Error in getting new data. Halting plugin')
            return None

        for active_task in active_tasks:
            if active_task['type'] in self.monitoring_tasks:
                task_name = active_task['type']

                # calculate running tasks
                self.data[task_name + '_task'] += 1

                # Percentage:
                # indexer & view_compaction
                if task_name == 'indexer' or task_name == 'view_compaction':
                    design_document = active_task['design_document'].replace('/', '_')
                    chart_var = task_name + "_" + active_task['database'] + design_document
                    check_new_data(task_name, chart_var)
                    self.data[chart_var] = active_task['progress']

                # database_compaction
                if task_name == 'database_compaction':
                    chart_var = task_name + "_" + active_task['database']
                    check_new_data(task_name, chart_var)
                    self.data[chart_var] = active_task['progress']

                # replication
                if task_name == 'replication':
                    source_host, source_db = get_host_and_db(active_task['source'])
                    target_host, target_db = get_host_and_db(active_task['target'])
                    chart_var = task_name + '_' + source_host + "." + source_db + '_' + target_host + '.' + target_db
                    check_new_data(task_name, chart_var)
                    self.data[chart_var] = active_task['progress']
        return self.data

    def append_new_lines(self, task, chart_var):
        # pdb.set_trace()
        self._dimensions.append(str(chart_var))
        self.info('adding new lines: task: %s - chart_var: %s' % (task, chart_var))
        self.definitions[task + '_percentage']['lines'].append(
            [chart_var, chart_var, 'absolute', 1, 1]
        )
        # cant find other solutions
        self.check() # if not: wrong dimension id: replication_localhost.first_localhost.second Available dimensions are: indexer_task
        self.create() # if not: Cannot find dimension with id 'replication_localhost.first_localhost.second'
