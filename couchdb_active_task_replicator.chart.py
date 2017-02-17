""" dynamic plugin for CouchDB replication monitoring """
# TODO:
# - test dymanics CHARTS

import sys

#sys.path.append('/data/shellshock/install/netdata/python.d/python_modules/')
#sys.path.append('/usr/libexec/netdata/python.d/python_modules/')
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
        self.couch_tsk = open('/home/shellshock/share_DEBUG/active_task_repl.json').read()
        # if len(self.couch_stats) == 0 or len(self.couch_db) == 0:
        #     raise Exception('Invalid couch')
        self.order = ORDER
        self.definitions = CHARTS
        self.data = {
            'source':0
        }

    def _get_data(self):
        active_tasks = json.loads(self.couch_tsk)
        for task in active_tasks:
            print task
        return self.data


#s = Service(configuration={'priority': 60000, 'retries': 60, 'update_every': 1}, name=None)
#d = s._get_data()
