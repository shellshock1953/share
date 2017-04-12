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
        'lines':
            ['aa', 'aa', 'absolute', 1, 1]
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
        self.monitoring_tasks = ['indexer', 'database_compaction', 'view_compaction', 'replication']
        self.order = ORDER
        self.definitions = CHARTS

        self.baseurl = str(self.configuration.get('url'))
        self.all_dbs_url = self.baseurl + '_all_dbs'
        self.active_tasks_url = self.baseurl + '_active_tasks'

        self.untrack_dbs = self.configuration.get('untrack_dbs',['_replicator','_users'])

        self.user = self.configuration.get('user') or None
        self.password = self.configuration.get('pass') or None
        if self.user:
            self.base64string = base64.encodestring('%s:%s' % (self.user, self.password)).replace('\n', '')

        self.data = { 'indexer_task': 0, 'database_compaction_task': 0, 'view_compaction_task': 0, 'replication_task': 0, }


    def _get_all_dbs(self):
        self.url = self.all_dbs_url
        all_dbs = self._get_raw_data()
        return all_dbs

    def _get_active_tasks(self):
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
        pdb.set_trace()
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
            if chart_var not in self.data:
                self.append_new_lines(task, chart_var)

        # pdb.set_trace()
        # zero values EVERY time
        for key in self.data.keys():
            self.data[key] = 0

        # refresh
        all_dbs = self._get_all_dbs()
        active_tasks = self._get_active_tasks()
        if self.ERROR:
            self.error('halting plugin')
            return None

        # calculate running tasks
        for active_task in active_tasks:
            for monitoring_task in self.monitoring_tasks:
                if monitoring_task == active_task['type']:
                    self.data[monitoring_task + '_task'] += 1
                    # pdb.set_trace()
                    if monitoring_task == 'replication':
                        source_host,source_db = get_host_and_db(active_task['source'])
                        target_host,target_db = get_host_and_db(active_task['target'])
                        chart_var = 'replication' + '_' + source_host+"."+ source_db + '_' + target_host+'.'+ target_db
                        check_new_data('replication', chart_var)
                        self.data[chart_var] = active_task['progress']
        return self.data

    def append_new_lines(self, task, chart_var):
        self.definitions[task + '_percentage']['lines'].append(
            [chart_var, chart_var, 'absolute', 1, 1]
        )
        # self._dimensions.append(str(chart_var))
        # self.create()

