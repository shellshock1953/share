""" dynamic plugin for CouchDB replication monitoring """
# TODO:
# - test dymanics CHARTS

import sys
sys.path.append('/data/shellshock/install/netdata/python.d/python_modules')
from base import SimpleService
import json

try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

priority = 70000
retries = 60
update_every = 1

ORDER = []

CHARTS = {
    'replication': {
        'options': [None, 'Indexer tasks', 'tasks', '', '', 'line'],
        'lines': []
    }
}

class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.couch_tsk = open('active_task_repl.json').readlines()
        if len(self.couch_stats) == 0 or len(self.couch_db) == 0:
            raise Exception('Invalid couch')
        self.order = ORDER
        self.definitions = CHARTS
        self.data = {}

        def _get_data(self):
            try:
                active_tasks = json.loads(self.couch_tsk)
            except (ValueError, AttributeError):
                return self.data
            return self.data