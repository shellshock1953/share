# -*- coding: utf-8 -*-
# Description: CouchDB statistics netdata python.d module


from base import SimpleService
#from python_modules.base import SimpleService

import json
try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

priority = 70000
retries = 60
update_every = 1

ORDER = ['httpd_queries_absolute', 'status_codes_queries_absolute',
         'httpd_queries_incremental', 'status_codes_queries_incremental',
         'database_fragmentation']
CHARTS = {
    'httpd_queries_absolute': {
        'options': [None, 'Http queries', 'requests', '',
                    '', 'stacked'],
        'lines': [
            ['copy_queries', 'COPY', 'absolute', 1, 1],
            ['delete_queries', 'DELETE', 'absolute', 1, 1],
            ['get_queries', 'GET', 'absolute', 1, 1],
            ['head_queries', 'HEAD', 'absolute', 1, 1],
            ['post_queries', 'POST', 'absolute', 1, 1],
            ['put_queries', 'PUT', 'absolute', 1, 1]
        ]
    },
    'status_codes_queries_absolute': {
        'options': [None, 'Status codes queries', 'requests', '',
                    '', 'stacked'],
        'lines': [
            ['200_queries', '200', 'absolute', 1, 1],
            ['201_queries', '201', 'absolute', 1, 1],
            ['202_queries', '202', 'absolute', 1, 1],
            ['301_queries', '301', 'absolute', 1, 1],
            ['304_queries', '304', 'absolute', 1, 1],
            ['400_queries', '400', 'absolute', 1, 1],
            ['401_queries', '401', 'absolute', 1, 1],
            ['403_queries', '403', 'absolute', 1, 1],
            ['404_queries', '404', 'absolute', 1, 1],
            ['405_queries', '405', 'absolute', 1, 1],
            ['409_queries', '409', 'absolute', 1, 1],
            ['412_queries', '412', 'absolute', 1, 1],
            ['500_queries', '500', 'absolute', 1, 1]
        ]
    },
    'httpd_queries_incremental': {
        'options': [None, 'Http queries', 'requests', '',
                    '', 'stacked'],
        'lines': [
            ['copy_queries', 'COPY', 'incremental', 1, 1],
            ['delete_queries', 'DELETE', 'incremental', 1, 1],
            ['get_queries', 'GET', 'incremental', 1, 1],
            ['head_queries', 'HEAD', 'incremental', 1, 1],
            ['post_queries', 'POST', 'incremental', 1, 1],
            ['put_queries', 'PUT', 'incremental', 1, 1]
        ]
    },
    'status_codes_queries_incremental': {
        'options': [None, 'Status codes queries', 'requests', '',
                    '', 'stacked'],
        'lines': [
            ['200_queries', '200', 'incremental', 1, 1],
            ['201_queries', '201', 'incremental', 1, 1],
            ['202_queries', '202', 'incremental', 1, 1],
            ['301_queries', '301', 'incremental', 1, 1],
            ['304_queries', '304', 'incremental', 1, 1],
            ['400_queries', '400', 'incremental', 1, 1],
            ['401_queries', '401', 'incremental', 1, 1],
            ['403_queries', '403', 'incremental', 1, 1],
            ['404_queries', '404', 'incremental', 1, 1],
            ['405_queries', '405', 'incremental', 1, 1],
            ['409_queries', '409', 'incremental', 1, 1],
            ['412_queries', '412', 'incremental', 1, 1],
            ['500_queries', '500', 'incremental', 1, 1]
        ]
    },
    'database_fragmentation': {
        'options': [None, 'Database fragmentation', 'Megabytes', '',
                    '', 'stacked'],
        'lines': [
            ['disk_size_overhead', 'disk_size_overhead', 'absolute', 1, 1],
            ['data_size', 'data_size', 'absolute', 1, 1]
        ]
    }
}


class Service(SimpleService):

    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.couch_db = configuration['couch_db']
        self.couch_stats = configuration['couch_stats']
        self.couch_config = configuration['couch_config']
        if len(self.couch_stats) == 0:
            raise Exception('Invalid couch_stats')
        self.order = ORDER
        self.definitions = CHARTS
        self.data = {
            'copy_queries': 0,
            'delete_queries': 0,
            'get_queries': 0,
            'head_queries': 0,
            'post_queries': 0,
            'put_queries': 0,
            '200_queries': 0,
            '201_queries': 0,
            '202_queries': 0,
            '301_queries': 0,
            '304_queries': 0,
            '400_queries': 0,
            '401_queries': 0,
            '403_queries': 0,
            '404_queries': 0,
            '405_queries': 0,
            '409_queries': 0,
            '412_queries': 0,
            '500_queries': 0,
            'data_size': 0,
            'disk_size_overhead': 0
        }

    def _get_data(self):
        try:
            stats = urllib2.urlopen(self.couch_stats).read()

            httpd = json.loads(stats)['httpd_request_methods']
            self.data['copy_queries'] = httpd['COPY']['current']
            self.data['delete_queries'] = httpd['DELETE']['current']
            self.data['get_queries'] = httpd['GET']['current']
            self.data['head_queries'] = httpd['HEAD']['current']
            self.data['post_queries'] = httpd['POST']['current']
            self.data['put_queries'] = httpd['PUT']['current']

            status = json.loads(stats)['httpd_status_codes']
            self.data['200_queries'] = status['200']['current']
            self.data['201_queries'] = status['201']['current']
            self.data['202_queries'] = status['202']['current']
            self.data['301_queries'] = status['301']['current']
            self.data['304_queries'] = status['304']['current']
            self.data['400_queries'] = status['400']['current']
            self.data['401_queries'] = status['401']['current']
            self.data['403_queries'] = status['403']['current']
            self.data['404_queries'] = status['404']['current']
            self.data['405_queries'] = status['405']['current']
            self.data['409_queries'] = status['409']['current']
            self.data['412_queries'] = status['412']['current']
            self.data['500_queries'] = status['500']['current']

            # fragmentation located in self.couch_db
            # it is ('disk_size' - 'data_size')
            database = urllib2.urlopen(self.couch_db).read()
            frag = json.loads(database)
            # convert to megabytes
            # data_size and disk_size storaged in bytes
            self.data['data_size'] = frag['data_size'] / 1000000
            self.data['disk_size_overhead'] = (frag['disk_size'] -frag['data_size']) / 1000000

            # replace CouchDB 'null' values with zero
            for key in self.data:
                if self.data[key] == None:
                    self.data[key] = 0
        except (ValueError, AttributeError):
            return self.data
        return self.data

#s = Service(configuration={ 'update_every':1, 'priority':6000, 'retries':60, 'couch_url':'http://0.0.0.0:5984/_stats' },name=None)
#d = s._get_data()
# print d['200_queries']
