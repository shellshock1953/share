# -*- coding: utf-8 -*-
# Description: CouchDB SERVER statistics Netdata plugin
# specify 'http://IP:PORT/' in conf.file
#
# more info: github.com/shellshock1953/share

from base import SimpleService

import json

try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

priority = 70000
retries = 60
update_every = 1

# static order
ORDER = [
    'authenthentication_cache',
    'continuous_changes_listeners',
    'database_io_statistics_delta',
    'database_io_statistics',
    'httpd_methods',
    'httpd_requests',
    'status_codes',
    'open_databases',
    'open_files'
]

# static charts
CHARTS = {
    'authenthentication_cache': {
        'options': [None, 'Authentification cache', 'ratio', 'Authentification cache', '', 'line'],
        'lines': [
            ['cache_hits', 'cache hits', 'absolute', 1, 1],
            ['cache_misses', 'cache misses', 'absolute', 1, 1]
        ]
    },
    'continuous_changes_listeners': {
        'options': [None, 'Continuous changes listeners', 'clients', 'Continuous changes listeners', '', 'line'],
        'lines': [
            ['clients', 'clients for continuous changes', 'absolute', 1, 1]
        ]
    },
    'database_io_statistics_delta': {
        'options': [None, 'I/O statistics', 'reads/writes', 'I/O statistics delta', '', 'line'],
        'lines': [
            ['db_reads_delta', 'db reads', 'absolute', 1, 1],
            ['db_writes_delta', 'db writes', 'absolute', 1, 1]
        ]
    },
    'database_io_statistics': {
        'options': [None, 'I/O statistics', 'reads/writes', 'I/O statistics', '', 'line'],
        'lines': [
            ['db_reads', 'db reads', 'absolute', 1, 1],
            ['db_writes', 'db writes', 'absolute', 1, 1]
        ]
    },
    'httpd_methods': {
        'options': [None, 'Http request methods', 'requests', 'Http request methods', '', 'line'],
        'lines': [
            ['COPY', 'COPY', 'absolute', 1, 1],
            ['DELETE', 'DELETE', 'absolute', 1, 1],
            ['GET', 'GET', 'absolute', 1, 1],
            ['HEAD', 'HEAD', 'absolute', 1, 1],
            ['POST', 'POST', 'absolute', 1, 1],
            ['PUT', 'PUT', 'absolute', 1, 1]
        ]
    },
    'httpd_requests': {
        'options': [None, 'Httpd requests', 'documents', 'Httpd requests', '', 'line'],
        'lines': [
            ['requests', 'requests', 'absolute', 1, 1],
            ['bulk_requests', 'bulk_requests', 'absolute', 1, 1],
            ['view_reads', 'view_reads', 'absolute', 1, 1],
            ['temporary_view_reads', 'temporary_view_reads', 'absolute', 1, 1]
        ]
    },
    'status_codes': {
        'options': [None, 'Status codes', 'requests', 'Status codes', '', 'line'],
        'lines': [
            ['200', '200 queries', 'absolute', 1, 1],
            ['201', '201 queries', 'absolute', 1, 1],
            ['202', '202 queries', 'absolute', 1, 1],
            ['301', '301 queries', 'absolute', 1, 1],
            ['304', '304 queries', 'absolute', 1, 1],
            ['400', '400 queries', 'absolute', 1, 1],
            ['401', '401 queries', 'absolute', 1, 1],
            ['403', '403 queries', 'absolute', 1, 1],
            ['404', '404 queries', 'absolute', 1, 1],
            ['405', '405 queries', 'absolute', 1, 1],
            ['409', '409 queries', 'absolute', 1, 1],
            ['412', '412 queries', 'absolute', 1, 1],
            ['500', '500 queries', 'absolute', 1, 1]
        ]
    },
    'open_databases': {
        'options': [None, 'Open databases', 'databases', 'Open databases', '', 'line'],
        'lines': [
            ['dbs', 'databases', 'absolute', 1, 1],
        ]
    },
    'open_files': {
        'options': [None, 'Open files', 'files', 'Open files', '', 'line'],
        'lines': [
            ['files', 'files', 'absolute', 1, 1],
        ]
    }
}

# DELTA contains previous metrics, to calculate difference 'now - previous'
# used to avoid non-integer metric presentation in Netdata dashboard
DELTA = {}


class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)

        self.couch_url = configuration['url']
        # self.couch_url = 'http://127.0.0.1:5984/'
        self.couch_stats_url = self.couch_url + '_stats'
        if len(self.couch_stats_url) == 0: raise Exception('Invalid couch')
        self.couch_stats = 0

        self.order = ORDER
        self.definitions = CHARTS

        self.data = {
            '200': 0,
            '201': 0,
            '202': 0,
            '301': 0,
            '304': 0,
            '400': 0,
            '401': 0,
            '403': 0,
            '404': 0,
            '405': 0,
            '409': 0,
            '412': 0,
            '500': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'COPY': 0,
            'DELETE': 0,
            'GET': 0,
            'HEAD': 0,
            'POST': 0,
            'PUT': 0,
            'db_reads_delta': 0,
            'db_writes_delta': 0,
            'db_reads': 0,
            'db_writes': 0,
            'clients': 0,
            'requests': 0,
            'bulk_requests': 0,
            'view_reads': 0,
            'temporary_view_reads': 0,
            'files': 0,
            'dbs': 0
        }

    # get fresh data
    def refresh(self):
        # open /_stats url
        couch_stats_open = urllib2.urlopen(self.couch_stats_url).read()
        self.couch_stats = json.loads(couch_stats_open)

    def _get_data(self):
        # zero values
        for key in self.data.keys():
            self.data[key] = 0

        # calc 'new - previous' values
        # result stored in DELTA{}
        def calc_delta(*args):
            for metric in args:
                if self.data[metric] is None:
                    self.data[metric] = 0

                # if no such metric in DELTA (first run) -- store it!
                if metric not in DELTA:
                    DELTA[metric] = self.data[metric]

                # save current untouched value
                current = self.data[metric]

                # current - previous
                difference = self.data[metric] - DELTA[metric]

                # prevent negative values (example -- doc deleting)
                self.data[metric] = difference
                # save current for future use
                DELTA[metric] = current

        try:
            # get fresh data
            self.refresh()

            # httpd methods
            httpd_methods = self.couch_stats['httpd_request_methods']
            self.data['COPY'] = httpd_methods['COPY']['current']
            self.data['DELETE'] = httpd_methods['DELETE']['current']
            self.data['GET'] = httpd_methods['GET']['current']
            self.data['HEAD'] = httpd_methods['HEAD']['current']
            self.data['POST'] = httpd_methods['POST']['current']
            self.data['PUT'] = httpd_methods['PUT']['current']
            calc_delta('COPY', 'DELETE', 'GET', 'HEAD', 'POST', 'PUT')

            # httpd status codes
            status = self.couch_stats['httpd_status_codes']
            self.data['200'] = status['200']['current']
            self.data['201'] = status['201']['current']
            self.data['202'] = status['202']['current']
            self.data['301'] = status['301']['current']
            self.data['304'] = status['304']['current']
            self.data['400'] = status['400']['current']
            self.data['401'] = status['401']['current']
            self.data['403'] = status['403']['current']
            self.data['404'] = status['404']['current']
            self.data['405'] = status['405']['current']
            self.data['409'] = status['409']['current']
            self.data['412'] = status['412']['current']
            self.data['500'] = status['500']['current']
            calc_delta(
                '200', '201', '202', '301', '304', '400',
                '401', '403', '404', '405', '409', '412', '500'
            )

            # DB I/O
            couchdb = self.couch_stats['couchdb']
            self.data['db_reads'] = couchdb['database_reads']['current']
            self.data['db_writes'] = couchdb['database_writes']['current']
            self.data['db_reads_delta'] = couchdb['database_reads']['current']
            self.data['db_writes_delta'] = couchdb['database_writes']['current']
            calc_delta('db_reads_delta', 'db_writes_delta')

            # open DBs
            self.data['dbs'] = couchdb['open_databases']['current']

            # open files
            self.data['files'] = couchdb['open_os_files']['current']

            # Auth cache
            self.data['cache_hits'] = couchdb['auth_cache_hits']['current']
            self.data['cache_misses'] = couchdb['auth_cache_misses']['current']

            # Requests
            httpd_requests = self.couch_stats['httpd']
            self.data['requests'] = httpd_requests['requests']['current']
            self.data['bulk_requests'] = httpd_requests[
                'bulk_requests']['current']
            self.data['view_reads'] = httpd_requests['view_reads']['current']
            self.data['temporary_view_reads'] = httpd_requests[
                'temporary_view_reads']['current']
            calc_delta('requests', 'bulk_requests', 'view_reads', 'temporary_view_reads')

            # Clients requesting changes
            self.data['clients'] = httpd_requests[
                'clients_requesting_changes']['current']

            # zero 'None' values for backend purposes
            for item in self.data:
                if self.data[item] is None:
                    self.data[item] = 0

        except (ValueError, AttributeError):
            return self.data
        return self.data
