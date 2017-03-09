# -*- coding: utf-8 -*-
# Description: CouchDB DB statistics/replication taks Netdata plugin
# used to monitoring specific database and replication task of this database (if any)
# main feather: dynamic chart and order creation when new replication task available (only need if to refresh dashboard)
#
# specify 'http://IP:PORT/' in conf.file
# specify 'db_name' in conf.file
#
# more info: github.com/shellshock1953/share

import sys
sys.path.append('/data/shellshock/install/netdata/python.d/python_modules/')

# TODO: fix error calc_delta() when specify few databases.

from base import SimpleService
import json

try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

priority = 70030
retries = 60
update_every = 5

# dynamic creation in check() because of few databases
CHARTS = {
    'database_documents_delta': {
        'options': [None, 'Documents', 'documents', 'Documents delta', '', 'line'],
        'lines': [
            [self.couch_db_name + '_docs_delta', 'docs', 'absolute', 1, 1],
            [self.couch_db_name + '_docs_deleted_delta', 'docs_deleted', 'absolute', 1, 1]
        ]
    },
    'database_documents': {
        'options': [None, 'Documents', 'documents', 'Documents', '', 'line'],
        'lines': [
            [self.couch_db_name + '_docs', 'docs', 'absolute', 1, 1],
            [self.couch_db_name + '_docs_deleted', 'docs_deleted', 'absolute', 1, 1]
        ]
    },
    'database_fragmentation': {
        'options': [None, 'Database fragmentation', 'Megabytes', 'Database fragmentation', '', 'line'],
        'lines': [
            [self.couch_db_name + '_disk_size_overhead', 'disk size overhead', 'absolute', 1, 1],
            [self.couch_db_name + '_data_size', 'data size', 'absolute', 1, 1]
        ]
    },
    'database_seq': {
        'options': [None, 'Database seq', 'seq', 'Database seq', '', 'line'],
        'lines': [
            [self.couch_db_name + '_db_seq', 'db seq', 'absolute', 1, 1]
        ]
    }
}
# static part of dynamic order
ORDER = [
    'database_documents_delta',
    'database_documents',
    'database_fragmentation',
    'database_seq'
]


# DELTA contains previous metrics, to calculate difference 'now - previous'
# used to avoid non-integer metric presentation in Netdata dashboard
DELTA = {}


class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.tasks_to_monitor = ['indexer', 'database_compaction', 'view_compaction', 'replication']
        # self.couch_url = configuration['couch_url']
        self.couch_url = 'http://127.0.0.1:5984/'
        self.couch_active_task_url = self.couch_url + '_active_tasks'
        if len(self.couch_url) is 0: raise Exception('Invalid couch url')

        self.couch_db_name = configuration['db']
        # self.couch_db_name = 'tracking'
        self.couch_db_url = self.couch_url + self.couch_db_name

        self.refresh()

        self.new_source_replications = []
        self.order = ORDER
        self.definitions = {}
        # self.definitions = CHARTS
        self.data = {}

    # get fresh data
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

        # calc 'new - previous' values
        # result stored in DELTA{}
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
            self.data[self.couch_db_name + '_data_size'] = self.database_stats['data_size'] / 1000000
            self.data[self.couch_db_name + '_disk_size_overhead'] = \
                (self.database_stats['disk_size'] - self.database_stats['data_size']) / 1000000

            # DB documents
            self.data[self.couch_db_name + '_docs'] = self.database_stats['doc_count']
            self.data[self.couch_db_name + '_docs_deleted'] = self.database_stats['doc_del_count']

            # DB delta documents
            self.data[self.couch_db_name + '_docs_delta'] = self.database_stats['doc_count']
            self.data[self.couch_db_name + '_docs_deleted_delta'] = self.database_stats['doc_del_count']
            calc_delta(self.couch_db_name + '_docs_delta',
                       self.couch_db_name + '_docs_deleted_delta')

            # update_seq
            self.data[self.couch_db_name + '_db_seq'] = self.database_stats['committed_update_seq']
            calc_delta(self.couch_db_name + '_db_seq')

        except (ValueError, AttributeError):
            self.error('error in _get_data()')
            return None
        return self.data




s = Service(configuration={'update_every':update_every,'retries':retries,'priority':priority,'db':'edge_db'},name=None)

s.check()
s.create()
s.update(1)
s