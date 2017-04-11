# -*- coding: utf-8 -*-
# Description: CouchDB ACTIVE TASKS counter Netdata plugin
# specify 'http://IP:PORT/' in conf.file
#
# more info: github.com/shellshock1953/share


# from python_modules.base import SimpleService
#from base import SimpleService
# import sys
# sys.path.append('/data/shellshock/install/netdata/python.d/python_modules/')
from base import SimpleService

import json
import base64
import sys

try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

priority = 70010
retries = 60
update_every = 10

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


class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)

        self.tasks_to_monitor = ['indexer', 'database_compaction', 'view_compaction', 'replication']
        self.couch_url = configuration['couch_url']
        # self.couch_url = 'http://10.0.0.50:5984/'
        if len(self.couch_url) is 0: raise Exception('Invalid couch url')

        self.couch_active_task_url = self.couch_url + '_active_tasks'
        self.couch_all_dbs_url = self.couch_url + '_all_dbs'

        # AUTH
        try:
            self.couch_username = configuration['couch_username']
            self.couch_password = configuration['couch_password']
        except:
            # no username specified in conf file.
            self.couch_username = ''
            self.couch_password = ''
        self.base64string = base64.encodestring('%s:%s' % (self.couch_username, self.couch_password)).replace('\n', '')

        self.error_handler = False
        try:
            self.refresh()
        except IOError, e:
            self.error('cant connect to couchdb. Check couchdn is running and correct auth present')
            self.error_handler = True


        self.new_chart_vars = []
        self.order = ORDER
        self.definitions = CHARTS
        self.data = {
            'indexer_task': 0,
            'database_compaction_task': 0,
            'view_compaction_task': 0,
            'replication_task': 0,
        }

    def refresh(self):
        """ get fresh data """
        # open active tasks urls
        try:
            active_tasks_url = urllib2.urlopen(self.couch_active_task_url).read()
            self.active_tasks = json.loads(active_tasks_url)
        except IOError:
            # server is pass protected
            request = urllib2.Request(self.couch_active_task_url)
            request.add_header("Authorization", "Basic %s" % self.base64string)
            active_tasks_url = urllib2.urlopen(request).read()
            self.active_tasks = json.loads(active_tasks_url)

        #  open dbs urls
        try:
            all_dbs_url = urllib2.urlopen(self.couch_all_dbs_url).read()
            self.all_dbs = json.loads(all_dbs_url)
        except IOError:
            # server is pass protected
            request = urllib2.Request(self.couch_all_dbs_url)
            request.add_header("Authorization", "Basic %s" % self.base64string)
            all_dbs_url = urllib2.urlopen(request).read()
            self.all_dbs = json.loads(all_dbs_url)

    def _get_data(self):
        if self.error_handler:
            return None

        def fix_database_name(database_name):
            """ unification db name
            :arg http://ip:port/db
            :return ip.db
            """
            if '/' in database_name:
                fixed_database_name = database_name.split('/')[3]
                return fixed_database_name
            else:
                return database_name

        def get_source_hostname(database_name):
            if 'http' in database_name:
                # http://chronograph:*****@localhost:5984/openprocurement_chronograph/
                source_hostname = database_name.split('/')[2]
                if '@' in source_hostname:
                    # chronograph:*****@localhost:5984/
                    source_hostname = source_hostname.split('@')[1]
                # localhost:5984/
                source_hostname = source_hostname.split(':')[0]
                return source_hostname
            elif 'localhost' in database_name:
                return 'localhost'
            else:
                return 'localhost'

        def new_data_item(task_type, chart_var):
            if self.data.has_key(chart_var):
                pass
            else:
               self.new_chart_vars.append([task_type,chart_var])

        try:
            # get fresh data
            self.refresh()

            # zero values EVERY time
            for key in self.data.keys():
                self.data[key] = 0

            # calculate running tasks
            for active_task in self.active_tasks:
                for monitoring_task in self.tasks_to_monitor:
                    if monitoring_task == active_task['type']:
                        self.data[monitoring_task + '_task'] += 1

            # calculate tasks percentage
            for db in self.all_dbs:
                if db[0] == '_': continue
                for task in self.active_tasks:
                    try:
                        if db in task['database']:
                            task_db = fix_database_name(task['database'])
                    except:
                        if db in task['target']:
                            task_db = fix_database_name(task['target'])
                        else:
                            continue

                    if db == task_db:
                        task_type = task['type']
                        progress = task['progress']

                        # indexer / view_compaction
                        if task_type == 'indexer' or task_type == 'view_compaction':
                            design_document = task['design_document'].replace('/', '_')
                            chart_var = task_type + "_" + db + design_document
                            new_data_item(task_type, chart_var)
                            self.data[chart_var] = progress

                        # database_compaction
                        if task_type == 'database_compaction':
                            chart_var = task_type + "_" + db
                            new_data_item(task_type, chart_var)
                            self.data[chart_var] = progress

                        # replication
                        if task_type == 'replication':
                            source_db = fix_database_name(task['source'])
                            source_hostname = get_source_hostname(task['source'])
                            target_db = fix_database_name(task['target'])
                            target_hostname = get_source_hostname(task['target'])
                            chart_var = task_type + "_" + target_hostname + '.' + target_db + "_" + \
                                source_hostname + "." + source_db
                            new_data_item(task_type, chart_var)
                            self.data[chart_var] = progress

        except (ValueError, AttributeError):
            self.error('error in _get_data()')
            return None
        return self.data

    def update(self, interval):
        """
        Update charts
        :param interval: int
        :return: boolean
        """
        data = self._get_data()
        if data is None:
            self.debug("failed to receive data during update().")
            return False

        if self.new_chart_vars:
           self.append_new_lines()

        updated = False
        for chart in self.order:
            if self.begin(self.chart_name + "." + chart, interval):
                updated = True
                for dim in self.definitions[chart]['lines']:
                    try:
                        self.set(dim[0], data[dim[0]])
                    except KeyError:
                        pass
                self.end()

        self.commit()
        if not updated:
            self.error("no charts to update")

        return updated

    def append_new_lines(self):
        for chart_task_and_var in self.new_chart_vars:
            chart_task = chart_task_and_var[0]
            chart_var = chart_task_and_var[1]
            for chart_id in self.order:
                if chart_task + '_percentage' == chart_id:
                    self.definitions[chart_id]['lines'].append(
                        [chart_var, chart_var, 'absolute', 1, 1]
                    )
                    self.new_chart_vars.remove([chart_task, chart_var])

        # TODO: dont use create()
        # instead use self.dimension(*line)
        self.create()

# s = Service(configuration={'priority':50000,'update_every':2,'retries':12})
# s.check()
# s.create()
# s.update(1)
# s.run()
