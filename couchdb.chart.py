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

ORDER = ['httpd_queries', 'status_codes_queries']
CHARTS = {
    'httpd_queries': {
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
    'status_codes_queries': {
        'options': [None, 'Status codes queries', 'requests', '',
                    '', 'stacked'],
        'lines': [
            ['2xx_queries', '2xx', 'incremental', 1, 1],
            ['3xx_queries', '3xx', 'incremental', 1, 1],
            ['4xx_queries', '4xx', 'incremental', 1, 1],
            ['5xx_queries', '5xx', 'incremental', 1, 1]
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
        def sum_and_zero_if_none(*argv):
            sum = 0
            for arg in argv:
                # float for safety"
                sum += float(arg or 0)
            return round(sum)

        try:
            response = urllib2.urlopen(self.couch_url).read()

            httpd = json.loads(response)['httpd_request_methods']
            self.data['copy_queries'] = httpd['GET']['current']
            self.data['delete_queries'] = httpd['DELETE']['current']
            self.data['get_queries'] = httpd['GET']['current']
            self.data['head_queries'] = httpd['HEAD']['current']
            self.data['post_queries'] = httpd['POST']['current']
            self.data['put_queries'] = httpd['PUT']['current']

            status = json.loads(response)['httpd_status_codes']
            self.data['2xx_queries'] = sum_and_zero_if_none(
                status['200']['current'],
                status['201']['current'],
                status['202']['current']
            )

            self.data['3xx_queries'] = sum_and_zero_if_none(
                status['301']['current'],
                status['304']['current']
            )

            self.data['400_queries'] = sum_and_zero_if_none(
                status['400']['current'],
                status['401']['current'],
                status['403']['current'],
                status['404']['current'],
                status['405']['current'],
                status['409']['current'],
                status['412']['current']
            )

            self.data['5xx_queries'] = sum_and_zero_if_none(
                status['500']['current']
            )

            # replace CouchDB 'null' values with zero
            for key in self.data:
                if self.data[key] == None:
                    self.data[key] = 0
        except (ValueError, AttributeError):
            return self.data
        return self.data
