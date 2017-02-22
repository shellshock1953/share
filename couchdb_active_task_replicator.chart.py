# import sys
# sys.path.append('/data/shellshock/install/netdata/python.d/python_modules')

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
        self.data = {}
        self.file = open('/data/shellshock/share/active_task_repl.json').read()
        self.tasks = json.loads(self.file)

    def _get_data(self):
        for key in self.data.keys():
            self.data[key] = 0
        try:
            self.tasks = json.loads(self.file)
            for task in self.tasks:
                source = task['source']
                source_seq = task['source_seq']
                local_seq = task['source_seq']

                self.data[source + '_source_seq'] = source_seq
                self.data[source + '_local_seq'] = local_seq
            return self.data
        except:
            self.error("err in _get_data")

    # if false -- exit
    # used for dynamic chart creation
    def check(self):
        try:
            self.chart_creation()
            return True
        except:
            self.error("err in check()")
            return False

    def chart_creation(self):
        try:
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
                                [local_seq_var, 'local_seq', 'absolute', 1, 1], ]
                        }
                    })
        except:
            self.error("err in chart_creation()")

    def create(self):
        try:
            for task in self.tasks:
                source = task['source']
                self.chart_name = source
                status = SimpleService.create(self)
                return status
        except:
            self.error("err in create()")

    def update(self, interval):
        try:
            for task in self.tasks:
                source = task['source']
                self.chart_name = source
                status = SimpleService.update(self, interval=interval)
                return status
        except:
            self.error("err in update()")

# s = Service(configuration={'priority': 60000, 'retries': 60, 'update_every': 1}, name=None)
# s._get_data()
# import pdb; pdb.set_trace()
# s.check()
# s.create()
# s.update(1)
# print s.definitions
# print s.data
