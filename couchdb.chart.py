# -*- coding: utf-8 -*-
# Description: CouchDB statistics netdata python.d module

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
    # 'active_tasks',
    'authenthentication_cache',
    'continuous_changes_listeners',
    'database_io_statistics',
    'database_documents_delta',
    'database_documents',
    'database_fragmentation',
    'httpd_methods',
    'httpd_requests',
    'status_codes',
    'open_databases',
    'open_files'
]
CHARTS = {
    'authenthentication_cache': {
        'options': [None, 'Authentification cache', 'ratio', '', '', 'stacked'],
        'lines': [
            ['cache_hits', 'cache hits', 'absolute', 1, 1],
            ['cache_misses', 'cache misses', 'absolute', 1, 1]
        ]
    },
    'continuous_changes_listeners': {
        'options': [None, 'CouchDB continuous changes listeners', 'clients', '', '', 'stacked'],
        'lines': [
            ['clients', 'clients for continuous changes', 'absolute', 1, 1]
        ]
    },
    'database_io_statistics': {
        'options': [None, 'I/O statistics', 'reads/writes', '', '', 'stacked'],
        'lines': [
            ['db_reads', 'db reads', 'absolute', 1, 1],
            ['db_writes', 'db writes', 'absolute', 1, 1]
        ]
    },
    'database_documents_delta': {
        'options': [None, 'CouchDB documents', 'documents', '', '', 'stacked'],
        'lines': [
            ['docs_delta', 'docs', 'absolute', 1, 1],
            ['docs_deleted_delta', 'docs_deleted', 'absolute', 1, 1]
        ]
    },
    'database_documents': {
        'options': [None, 'CouchDB documents', 'documents', '', '', 'stacked'],
        'lines': [
            ['docs', 'docs', 'absolute', 1, 1],
            ['docs_deleted', 'docs_deleted', 'absolute', 1, 1]
        ]
    },
    'database_fragmentation': {
        'options': [None, 'Database fragmentation', 'Megabytes', '', '', 'stacked'],
        'lines': [
            ['disk_size_overhead', 'disk size overhead', 'absolute', 1, 1],
            ['data_size', 'data size', 'absolute', 1, 1]
        ]
    },
    'httpd_methods': {
        'options': [None, 'Httpd request methods', 'requests', '', '', 'stacked'],
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
        'options': [None, 'CouchDB httpd requests', 'documents', '', '', 'stacked'],
        'lines': [
            ['requests', 'requests', 'absolute', 1, 1],
            ['bulk_requests', 'bulk_requests', 'absolute', 1, 1],
            ['view_reads', 'view_reads', 'absolute', 1, 1],
            ['temporary_view_reads', 'temporary_view_reads', 'absolute', 1, 1]
        ]
    },
    'status_codes': {
        'options': [None, 'Status codes queries', 'requests', '', '', 'stacked'],
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
        'options': [None, 'CouchDB open databases', 'databases', '', '', 'stacked'],
        'lines': [
            ['dbs', 'databases', 'absolute', 1, 1],
        ]
    },
    'open_files': {
        'options': [None, 'CouchDB open files', 'files', '', '', 'stacked'],
        'lines': [
            ['files', 'files', 'absolute', 1, 1],
        ]
    }
}

# DELTA
delta = {}


class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.couch_db = configuration['couch_db']
        self.couch_stats = configuration['couch_stats']
        if len(self.couch_stats) == 0 or len(self.couch_db) == 0:
            raise Exception('Invalid couch')
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
            'data_size': 0,
            'disk_size_overhead': 0,
            'db_reads': 0,
            'db_writes': 0,
            'clients': 0,
            'docs': 0,
            'docs_deleted': 0,
            'docs_delta': 0,
            'docs_deleted_delta': 0,
            'requests': 0,
            'bulk_requests': 0,
            'view_reads': 0,
            'temporary_view_reads': 0,
            'files': 0,
            'dbs': 0
        }

    def _get_data(self):
        for key in self.data.keys():
            self.data[key] = 0

        def calc_delta(metrics):
            if metric in delta:
                if delta[metric] is 0 or \
                   delta[metric] is None or \
                   delta[metric] < 0:
                    delta[metric] = self.data[metric]
                    return None
                previous = self.data[metric]
                self.data[metric] = self.data[metric] - delta[metric]
                delta[metric] = previous
                previous = 0
            else:
                delta[metric] = self.data[metric]

        try:
            """ STATS """
            stats = urllib2.urlopen(self.couch_stats).read()
            doc_stats = json.loads(stats)

            # httpd methods
            httpd_methods = doc_stats['httpd_request_methods']
            self.data['COPY'] = httpd_methods['COPY']['current']
            self.data['DELETE'] = httpd_methods['DELETE']['current']
            self.data['GET'] = httpd_methods['GET']['current']
            self.data['HEAD'] = httpd_methods['HEAD']['current']
            self.data['POST'] = httpd_methods['POST']['current']
            self.data['PUT'] = httpd_methods['PUT']['current']
            for metric in ['COPY','DELETE','GET','HEAD','POST','PUT']:
                calc_delta(metric)

            # httpd status codes
            status = doc_stats['httpd_status_codes']
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

            # DB I/O
            couchdb = doc_stats['couchdb']
            self.data['db_reads'] = couchdb['database_reads']['current']
            self.data['db_writes'] = couchdb['database_writes']['current']

            # open DBs
            self.data['dbs'] = couchdb['open_databases']['current']

            # open files
            self.data['files'] = couchdb['open_os_files']['current']

            # Auth cache
            self.data['cache_hits'] = couchdb['auth_cache_hits']['current']
            self.data['cache_misses'] = couchdb['auth_cache_misses']['current']

            # Requests
            httpd_requests = doc_stats['httpd']
            self.data['requests'] = httpd_requests['requests']['current']
            self.data['bulk_requests'] = httpd_requests[
                'bulk_requests']['current']
            self.data['view_reads'] = httpd_requests['view_reads']['current']
            self.data['temporary_view_reads'] = httpd_requests[
                'temporary_view_reads']['current']

            # Clients requesting changes
            self.data['clients'] = httpd_requests[
                'clients_requesting_changes']['current']

            """ COUCH_DB """
            db = urllib2.urlopen(self.couch_db).read()
            doc_db = json.loads(db)

            # DB fragmentation
            self.data['data_size'] = doc_db['data_size'] / 1000000
            self.data['disk_size_overhead'] = (doc_db['disk_size'] - doc_db['data_size']) / 1000000

            # DB documents
            self.data['docs'] = doc_db['doc_count']
            self.data['docs_deleted'] = doc_db['doc_del_count']

            # DB documents
            self.data['docs_delta'] = doc_db['doc_count']
            calc_delta('docs_delta')
            self.data['docs_deleted_delta'] = doc_db['doc_del_count']
            calc_delta('docs_deleted_delta')

            for item in self.data:
                if self.data[item] is None:
                    self.data[item] = 0
        except (ValueError, AttributeError):
            return self.data
        return self.data
