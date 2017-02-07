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

ORDER = ['httpd_queries', 'status_codes', 'io_statistics', 'database_fragmentation']
CHARTS = {
    'httpd_queries': {
        'options': [None, 'Http queries', 'requests', '', '', 'stacked'],
        'lines': [
            ['COPY', 'COPY queries', 'absolute', 1, 1],
            ['DELETE', 'DELETE queries', 'absolute', 1, 1],
            ['GET', 'GET queries', 'absolute', 1, 1],
            ['HEAD', 'HEAD queries', 'absolute', 1, 1],
            ['POST', 'POST queries', 'absolute', 1, 1],
            ['PUT', 'PUT queries', 'absolute', 1, 1]
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
    'io_statistics': {
        'options': [None, 'I/O statistics', 'reads/writes', '', '', 'stacked'],
        'lines': [
            ['reads', 'db reads', 'absolute', 1, 1],
            ['writes', 'db writes', 'absolute', 1, 1]
        ]
    },
    'database_fragmentation': {
        'options': [None, 'Database fragmentation', 'Megabytes', '', '', 'stacked'],
        'lines': [
            ['disk_size_overhead', 'disk size overhead', 'absolute', 1, 1],
            ['data_size', 'data size', 'absolute', 1, 1]
        ]
    }
}


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
            'COPY': 0,
            'DELETE': 0,
            'GET': 0,
            'HEAD': 0,
            'POST': 0,
            'PUT': 0,
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
            'reads': 0,
            'writes': 0,
            'data_size': 0,
            'disk_size_overhead': 0
        }

    def _get_data(self):
        try:
            stats = urllib2.urlopen(self.couch_stats).read()

            # http queries
            httpd = json.loads(stats)['httpd_request_methods']
            self.data['COPY'] = httpd['COPY']['current']
            self.data['DELETE'] = httpd['DELETE']['current']
            self.data['GET'] = httpd['GET']['current']
            self.data['HEAD'] = httpd['HEAD']['current']
            self.data['POST'] = httpd['POST']['current']
            self.data['PUT'] = httpd['PUT']['current']

            # http status codes
            status = json.loads(stats)['httpd_status_codes']
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
            io = json.loads(stats)['couchdb']
            self.data['db_reads'] = io['database_reads']['current']
            self.data['db_writes'] = io['database_writes']['current']

            # fragmentation located in self.couch_db
            # it is ('disk_size' - 'data_size')
            database = urllib2.urlopen(self.couch_db).read()
            frag = json.loads(database)
            # convert to megabytes
            # data_size and disk_size storaged in bytes
            self.data['data_size'] = frag['data_size'] / 1000000
            self.data['disk_size_overhead'] = (
                frag['disk_size'] - frag['data_size']) / 1000000

        except (ValueError, AttributeError):
            return self.data
        return self.data
