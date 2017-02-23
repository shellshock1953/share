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
        self.data = {}
        self.file = open('/data/shellshock/share/active_task_repl.json').read()
        self.tasks = json.loads(self.file)
        self.new_charts = []

    def _get_data(self):
        # zeroid data
        for key in self.data.keys():
            self.data[key] = 0
        try:
            refresh_file = open('/data/shellshock/share/active_task_repl.json').read()
            refresh_tasks = json.loads(refresh_file)
            for task in refresh_tasks:
                source = task['source']

                # Ops - got new source -- adding those for future chart_creation()
                if source not in self.order:
                    self.new_charts.append(source)

                source_seq = task['source_seq']
                local_seq = task['source_seq']

                self.data[source + '_source_seq'] = source_seq
                self.data[source + '_local_seq'] = local_seq


            # refresh_file.close()
            return self.data
        except:
            self.error("err in _get_data")
            return None

    # if false -- exit
    # used for dynamic chart creation
    # because check() runs before run()
    def check(self):
        try:
            status = self.chart_creation()
            return status
        except:
            self.error("err in check()")
            return False

    def chart_creation(self):
        def create(source):
            if source not in self.order:
                # ORDER
                self.order.append(source)
                source_seq_var = source + '_source_seq'
                local_seq_var = source + '_local_seq'

                # CHARTS
                self.definitions.update({
                    source: {
                        'options': [None, 'Replications', 'seq', '', '', 'line'],
                        'lines': [
                            [source_seq_var, 'source_seq', 'absolute', 1, 1],
                            [local_seq_var, 'local_seq', 'absolute', 1, 1], ]
                    }
                })
                self.create()

        try:
            for source in self.new_charts:
                create(source)
                self.new_charts.remove(source)
            else:
                for task in self.tasks:
                    source = task['source']
                    create(source)

            return True
        except:
            self.error("err in chart_creation()")
            return False


    # modified update() to check for a new replication tasks
    def update(self, interval):
        data = self._get_data()
        if data is None:
            self.debug("failed to receive data during update().")
            return False

        updated = False
        # do we have new charts?
        if self.new_charts:
            self.chart_creation()

        for chart in self.order:
            if self.begin(self.chart_name + "." + chart, interval):
                updated = True
                for dim in self.definitions[chart]['lines']:
                    try:
                        self.set(dim[0], data[dim[0]])
                    except KeyError:
                        pass
                self.end()

            # try to create new chart after plugin has been started

        self.commit()
        if not updated:
            self.error("no charts to update")

        return updated

s = Service(configuration={'priority': 60000, 'retries': 60, 'update_every': 1}, name=None)
s.check()
s.update(1)
s.run()
