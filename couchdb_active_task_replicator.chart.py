from base import SimpleService
import json

try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

priority = 70000
retries = 60
update_every = 1

ORDER = [
    'test',
    'source'
]

CHARTS = {
    'test': {
        'options': [None, 'TEST', 'tasks', 'Active tasks', '', 'line'],
        'lines': [
            ['test', 'test', 'absolute', 1, 1]
        ]
    }
}


class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.active_tasks = open('/home/shellshock/share_DEBUG/active_task_repl.json').read()
        self.local_db = open('/home/shellshock/share_DEBUG/active_task_repl_localdb.json').read()
        self.order = ORDER
        self.definitions = CHARTS
        self.data = {
            'test': 0
        }

    def _get_data(self):
        self.data['test'] = 0
        try:
            tasks = json.loads(self.active_tasks)
            for task in tasks:
                self.data['test'] += 1
                source = task['source']
                source_seq = task['source_seq']
                my_seq = task['checkpointed_source_seq']

                CHARTS[source] = {
                    'options': [None, 'Dyn source', 'tasks', '', '', 'line'],
                    'lines': [
                        ['source_seq', 'source_seq', 'absolute', 1, 1],
                        ['my_seq', 'my_seq', 'absolute', 1, 1]
                    ]
                }


                self.data['source_seq'] = source_seq
                self.data['my_seq'] = my_seq


        except (ValueError, AttributeError):
            return None
        return self.data
