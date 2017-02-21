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


class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.date = {}  # what to show
        self.file = open('/data/shellshock/share/active_task_repl.json').read() #  where to get showing info
        self.data = {}

    def _get_data(self):
        self.tasks = json.loads(self.file)
        for task in self.tasks:
            source = task['source']
            source_seq = task['source_seq']
            local_seq = task['source_seq']

            self.data[source + '_source_seq'] = source_seq
            self.data[source + '_local_seq'] = local_seq

    # if false -- exit
    # used for dynamic chart creation
    def check(self):
        self.chart_creation()

    def chart_creation(self):
        for task in self.tasks:
            source = task['source']

            if source not in self.order:
                self.order.append(source)

                source_seq_var = source + '_source_seq'
                local_seq_var = source + '_local_seq'

                self.definitions.update({
                        source: {
                                'options': [None, 'Replications', 'seq', '', '', 'line'],
                                'lines': [
                                        [source_seq_var, 'source_seq', 'absolute', 1, 1],
                                        [local_seq_var, 'local_seq', 'absolute', 1, 1],
                                         ]
                                }
                        })





s = Service(configuration={'priority':60000,'retries':60,'update_every':1},name=None)
s._get_data()
s.check()
print s.definitions
print s.data
