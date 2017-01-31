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
         'httpd_queries_incremental', 'status_codes_queries_incremental']
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
    }
}


class Service(SimpleService):

    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.couch_url = configuration['couch_url']
        if len(self.couch_url) == 0:
            raise Exception('Invalid couch_url')
        self.order = ORDER
        self.definitions = CHARTS
        self.data = {
            'copy_queries': 0,
            'delete_queries':   0,
            'get_queries':  0,
            'head_queries': 0,
            'post_queries': 0,
            'put_queries':  0,
            '2xx_queries': 0,
            '3xx_queries': 0,
            '4xx_queries': 0,
            '5xx_queries': 0
        }

    def _get_data(self):
        try:
            response = urllib2.urlopen(self.couch_url).read()

            httpd = json.loads(response)['httpd_request_methods']
            self.data['copy_queries'] = httpd['COPY']['mean']
            self.data['delete_queries'] = httpd['DELETE']['mean']
            self.data['get_queries'] = httpd['GET']['mean']
            self.data['head_queries'] = httpd['HEAD']['mean']
            self.data['post_queries'] = httpd['POST']['mean']
            self.data['put_queries'] = httpd['PUT']['mean']

            status = json.loads(response)['httpd_status_codes']
            self.data['200_queries'] = status['200']['mean']
            self.data['201_queries'] = status['201']['mean']
            self.data['202_queries'] = status['202']['mean']
            self.data['301_queries'] = status['301']['mean']
            self.data['304_queries'] = status['304']['mean']
            self.data['400_queries'] = status['400']['mean']
            self.data['401_queries'] = status['401']['mean']
            self.data['403_queries'] = status['403']['mean']
            self.data['404_queries'] = status['404']['mean']
            self.data['405_queries'] = status['405']['mean']
            self.data['409_queries'] = status['409']['mean']
            self.data['412_queries'] = status['412']['mean']
            self.data['500_queries'] = status['500']['mean']

            # replace CouchDB 'null' values with zero
            for key in self.data:
                if self.data[key] == None:
                    self.data[key] = float(1.99)
        except (ValueError, AttributeError):
            return self.data
        return self.data

#s = Service(configuration={ 'update_every':1, 'priority':6000, 'retries':60, 'couch_url':'http://0.0.0.0:5984/_stats' },name=None)
#d = s._get_data()
#print d['200_queries']
