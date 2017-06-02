# -*- coding: utf8 -*-

import json
from distutils.command.config import config

from base import SimpleService

try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

ORDER = [
    'authentication_cache',
    'continuous_changes_listeners',
    'database_io_statistics_delta',
    'database_io_statistics',
    'httpd_methods',
    'httpd_requests',
    'status_codes',
    'open_databases',
    'open_files'
]

CHARTS = {
    'authentication_cache': {
        'options': [None, 'Authentication cache', 'ratio', 'Authentication cache', '', 'line'],
        'lines': [
            ['cache_hits', 'cache hits', 'absolute', 1, 1],
            ['cache_misses', 'cache misses', 'absolute', 1, 1]
        ]
    },
    'continuous_changes_listeners': {
        'options': [None, 'Continuous changes listeners', 'clients', 'Countinuous changes listeners', '', 'line'],
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
        'options': [None, 'I/P statistics', 'reads/writes', 'I/O statistics', '', 'line'],
        'lines': [
            ['db_reads', 'db reads', 'absolute', 1, 1],
            ['db_writes', 'db writes', 'absolute', 1, 1]
        ]
    },
    'httpd_methods': {
        'options': [None, 'Httpd methods', 'requests', 'Httpd request methods', '', 'line'],
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
            ['dbs', 'databases', 'absolute', 1, 1]
        ]
    },
    'open_files': {
        'options': [None, 'Open files', 'files', 'Open files', '', 'line'],
        'lines': [
            ['files', 'files', 'absolute', 1, 1]
        ]
    }
}

DELTA = {}

class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.baseurl = self.configuration.get('url')
        # self.baseurl = 'http://10.0.0.10:5984'
        self.stats_url = '{}/_stats/'.format(self.baseurl)
        self.order = ORDER
        self.definitions = CHARTS
        self.data = {}

    def _get_response(self, url):
        """
        Return json-formatted list from url
        :param url: string
        :return: list or False
        """
        try:
            request = urllib2.Request(url)
            response_raw = urllib2.urlopen(request).read()
            response = json.loads(response_raw)
        except IOError as e:
            self.error('Error in getting {}: {}'.format(url, str(repr(e))))
            response = False
        return response

    def __flush_data(self):
        for key in self.data.keys():
            self.data[key] = 0

    def __calc_delta(self, *args):
        for metric in args:
            if self.data[metric] is None:
                self.data[metric] = 0

            if metric not in DELTA:
                DELTA[metric] = self.data[metric]
            current = self.data[metric]
            difference = self.data[metric] - DELTA[metric]
            self.data[metric] = difference
            DELTA[metric] = current

    def _get_data(self):
        try:
            self.__flush_data()
            stats = self._get_response(self.stats_url)

            httpd_methods = stats['httpd_request_methods']
            self.data['COPY'] = httpd_methods['COPY']['current']
            self.data['DELETE'] = httpd_methods['DELETE']['current']
            self.data['GET'] = httpd_methods['GET']['current']
            self.data['HEAD'] = httpd_methods['HEAD']['current']
            self.data['POST'] = httpd_methods['POST']['current']
            self.data['PUT'] = httpd_methods['PUT']['current']
            self.__calc_delta(
                'COPY',
                'DELETE',
                'GET',
                'HEAD',
                'POST',
                'PUT'
            )

            status = stats['httpd_status_codes']
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
            self.__calc_delta(
                '200',
                '201',
                '202',
                '301',
                '304',
                '400',
                '401',
                '403',
                '404',
                '405',
                '409',
                '412',
                '500'
            )

            couchdb = stats['couchdb']
            self.data['db_reads'] = couchdb['database_reads']['current']
            self.data['db_writes'] = couchdb['database_writes']['current']
            self.data['db_reads_delta'] = couchdb['database_reads']['current']
            self.data['db_writes_delta'] = couchdb['database_writes']['current']
            self.__calc_delta(
                'db_reads_delta',
                'db_writes_delta'
            )

            self.data['dbs'] = couchdb['open_databases']['current']
            self.data['files'] = couchdb['open_os_files']['current']
            self.data['cache_hits'] = couchdb['auth_cache_hits']['current']
            self.data['cache_misses'] = couchdb['auth_cache_misses']['current']

            httpd_requests = stats['httpd']
            self.data['requests'] = httpd_requests['requests']['current']
            self.data['bulk_requests'] = httpd_requests['bulk_requests']['current']
            self.data['view_reads'] = httpd_requests['view_reads']['current']
            self.data['temporary_view_reads'] = httpd_requests['temporary_view_reads']['current']
            self.__calc_delta(
                'requests',
                'bulk_requests',
                'view_reads',
                'temporary_view_reads'
            )

            self.data['clients'] = httpd_requests['clients_requesting_changes']['current']

            for item in self.data:
                if self.data[item] is  None:
                    self.data[item] = 0
        except (ValueError, AttributeError):
            return None
        return self.data

# DEBUG = True
# if DEBUG:
#     s = Service(
#         configuration={
#             'update_every': 1,
#             'retries': 60,
#             'priority': 60000
#         }
#     )
#     s.check()
#     s.create()
#     s.run()
#
#
#
#

























