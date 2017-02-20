""" dynamic plugin for CouchDB replication monitoring """
# TODO:
# - test dymanics CHARTS

# IM_PATH = '/data/shellshock/install/netdata/python.d/python_modules/'
# REPL_JSON = '/data/shellshock/share/active_task_repl.json'
# LOCAL_JSON = '/data/shellshock/share/active_task_repl_localdb.json'
#
IM_PATH = '/usr/libexec/netdata/python.d/python_modules/'
REPL_JSON = '/home/shellshock/share_DEBUG/active_task_repl.json'
LOCAL_JSON = '/home/shellshock/share_DEBUG/active_task_repl_localdb.json'


import sys

sys.path.append(IM_PATH)
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
CHARTS = {}


class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.couch_tsk = open(REPL_JSON).read()
        self.couch_local = open(LOCAL_JSON).read()
        self.order = ORDER
        self.definitions = CHARTS
        self.data = {
            'source':0
        }

    def _get_data(self):
        local_db = json.loads(self.couch_local)
        active_tasks = json.loads(self.couch_tsk)
        for task in active_tasks:
            source = task['source']
            source_seq = task['source_seq']
            my_seq = task['checkpointed_source_seq']
            db_seq = local_db['update_seq']
            chart_name = source

            CHARTS[source] = {
                'options': [None, chart_name, 'tasks', '', '', 'line'],
                'lines': [
                    [source_seq, 'source_seq', 'absolute', 1, 1],
                    [my_seq, 'my_seq', 'absolute', 1, 1],
                    [db_seq, 'db_seq', 'absolute', 1, 1],
                ]
            }

            self.data['source_seq'] = source_seq
            self.data['my_seq'] = my_seq
            self.data['db_seq'] = db_seq

        return self.data



# s = Service(configuration={'priority': 60000, 'retries': 60, 'update_every': 1}, name=None)
# d = s._get_data()

for chart in CHARTS.keys():
    ORDER.append(chart)

