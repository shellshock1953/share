# -*- coding: utf-8 -*-
# Description: CouchDB DB statistics/replication taks Netdata plugin
# specify 'http://IP:PORT/' in conf.file
# specify 'db_name' in conf.file
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

priority = 70000
retries = 60
update_every = 1

ORDER = [
    'database_documents_delta',
    'database_documents',
    'database_fragmentation'
]

CHARTS = {
    'database_documents_delta': {
        'options': [None, 'Documents', 'documents', 'Documents delta', '', 'line'],
        'lines': [
            ['docs_delta', 'docs', 'absolute', 1, 1],
            ['docs_deleted_delta', 'docs_deleted', 'absolute', 1, 1]
        ]
    },
    'database_documents': {
        'options': [None, 'Documents', 'documents', 'Documents', '', 'line'],
        'lines': [
            ['docs', 'docs', 'absolute', 1, 1],
            ['docs_deleted', 'docs_deleted', 'absolute', 1, 1]
        ]
    },
    'database_fragmentation': {
        'options': [None, 'Database fragmentation', 'Megabytes', 'Database fragmentation', '', 'line'],
        'lines': [
            ['disk_size_overhead', 'disk size overhead', 'absolute', 1, 1],
            ['data_size', 'data size', 'absolute', 1, 1]
        ]
    }
}

DELTA = {}


class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.tasks_to_monitor = ['indexer', 'database_compaction', 'view_compaction', 'replication']
        # self.couch_url = configuration['couch_url']
        self.couch_url = 'http://127.0.0.1:5984/'
        self.couch_active_task_url = self.couch_url + '_active_tasks'
        if len(self.couch_url) is 0: raise Exception('Invalid couch url')

        # self.couch_db_name = configuration['db']
        self.couch_db_name = 'public_sandbox'
        self.couch_db_url = self.couch_url + self.couch_db_name

        self.refresh()

        self.new_source_replications = []
        self.order = ORDER
        self.definitions = CHARTS
        self.data = {
            'data_size': 0,
            'disk_size_overhead': 0,
            'docs': 0,
            'docs_deleted': 0,
            'docs_delta': 0,
            'docs_deleted_delta': 0
        }

    def refresh(self):
        # open active tasks urls
        active_tasks_url = urllib2.urlopen(self.couch_active_task_url).read()
        self.active_tasks = json.loads(active_tasks_url)
        try:
            # open monitoring database
            database_open = urllib2.urlopen(self.couch_db_url).read()
            self.database_stats = json.loads(database_open)
        except urllib2.HTTPError:
            self.error('Cant open database. Check conf to correct db-name')
            return False

    def _get_data(self):

        def calc_delta(*args):
            for metric in args:
                if self.data[metric] is None: self.data[metric] = 0
                if metric in DELTA:
                    # prevent negative values
                    if self.data[metric] < DELTA[metric]:
                        DELTA[metric] = 0
                        return None
                    previous = self.data[metric]
                    self.data[metric] = self.data[metric] - DELTA[metric]
                    DELTA[metric] = previous
                else:
                    DELTA[metric] = self.data[metric]
        try:
            # get new data
            self.refresh()

            # zero values EVERY time
            for key in self.data.keys():
                self.data[key] = 0

            """ Get general /db stats """
            # DB fragmentation
            self.data['data_size'] = self.database_stats['data_size'] / 1000000
            self.data['disk_size_overhead'] = \
                (self.database_stats['disk_size'] - self.database_stats['data_size']) / 1000000

            # DB documents
            self.data['docs'] = self.database_stats['doc_count']
            self.data['docs_deleted'] = self.database_stats['doc_del_count']

            # DB delta documents
            self.data['docs_delta'] = self.database_stats['doc_count']
            calc_delta('docs_delta')
            self.data['docs_deleted_delta'] = self.database_stats['doc_del_count']
            calc_delta('docs_delta', 'docs_deleted_delta')

            """ Get db stats from /_active_task """
            for active_task in self.active_tasks:
                if active_task['type'] == 'replication':
                    source = self.fix_database_name(active_task['source'])
                    target = self.fix_database_name(active_task['target'])

                    # TODO: chart name be like: source + "_source_replication"
                    if source not in self.order:
                        self.new_source_replications.append(source)

                    db_seq = self.database_stats['committed_update_seq']

                    source_seq = active_task['source_seq']
                    # TODO: IS checkpoined_source correct value???
                    local_seq = active_task['checkpointed_source_seq']
                    self.data[source + '_source_seq'] = source_seq
                    self.data[source + '_local_seq'] = local_seq
                    self.data[source + '_db_seq'] = db_seq

        except (ValueError, AttributeError):
            return None
        return self.data

    # if false -- exit
    # used for dynamic chart creation
    # because check() runs once before run()
    def check(self):
        # no need to refresh() -- first start
        try:
            # init replication charts
            status = self.create_replication_charts()
            return status
        except:
            self.error("err in check()")
            return False

    def fix_database_name(self, database_name):
        if '/' in database_name:
            fixed_database_name = database_name.split('/')[3]
            return fixed_database_name
        else:
            return database_name

    def create_replication_charts(self):
        # TODO: chart name be like: source + "_source_replication"
        def create(source):
            # fix name
            source = self.fix_database_name(source)

            if source not in self.order:
                # ORDER
                self.order.append(source)
                source_seq_var = source + '_source_seq'
                local_seq_var = source + '_local_seq'
                update_seq_var = source + '_update_seq'

                # CHARTS
                self.definitions.update({
                    source: {
                        'options': [None, 'Replications', 'seq', 'Replication seq', '', 'line'],
                        'lines': [
                            [source_seq_var, 'source_seq', 'absolute', 1, 1],
                            [local_seq_var, 'local_seq', 'absolute', 1, 1],
                            [update_seq_var, 'update_seq', 'absolute', 1, 1]
                        ]
                    }
                })
                self.create()

        try:
            # self.new_replication contains newi source replications only
            # with fixed names (no http://)
            for source in self.new_source_replications:
                create(source)
                self.new_charts.remove(source)
            else:
                # only for replications
                for task in self.active_tasks:
                    if task['type'] == 'replication':
                        source = task['source']
                        create(source)

            return True
        except:
            self.error("err in chart creation")
            return False

    # modified update() to check for a new replication tasks
    def update(self, interval):
        data = self._get_data()
        if data is None:
            self.debug("failed to receive data during update().")
            return False

        updated = False
        # do we have new replication charts to be created?
        if self.new_source_replications:
            self.create_replication_charts()

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

# s = Service(configuration={'priority': 60000, 'retries': 60, 'update_every': 1}, name=None)
# d = s._get_data()
# print d
