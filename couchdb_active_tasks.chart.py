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

ORDER = [
    'active_tasks',
    'indexer',
    'replication',
    'database_compaction',
    'view_compaction'
]

CHARTS = {
    # show number of each running tasks
    'active_tasks': {
        'options': [None, 'Active tasks', 'tasks', 'Active tasks', '', 'line'],
        'lines': [
            # available tasks
            ['indexer_task', 'indexer', 'absolute', 1, 1],
            ['replication_task', 'replication', 'absolute', 1, 1],
            ['database_compaction_task', 'database_compaction', 'absolute', 1, 1],
            ['view_compaction_task', 'view_compaction', 'absolute', 1, 1]
        ]
    },
    # show number of bases per each task
    # empty lines because of dynamic chart creation
    # we dont know what dbs we will use
    'indexer': {
        'options': [None, 'Indexer task', 'tasks', 'Indexer task', '', 'line'],
        'lines': []
    },
    'database_compaction': {
        'options': [None, 'DB compaction task', 'tasks', 'DB compaction task', '', 'line'],
        'lines': []
    },
    'view_compaction': {
        'options': [None, 'View compaction task', 'tasks', 'View compaction task', '', 'line'],
        'lines': []
    },
    'replication': {
        'options': [None, 'Replication task', 'tasks', 'Replication task', '', 'line'],
        'lines': []
    }
}


class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.tasks_to_monitor = ['indexer', 'database_compaction', 'view_compaction', 'replication']
        # self.couch_url = configuration['couch_url']
        self.couch_url = 'http://127.0.0.1:5984/'
        self.couch_tsk = self.couch_url + '_active_tasks'
        self.couch_dbs = self.couch_url + '_all_dbs'
        if len(self.couch_url) is 0: raise Exception('Invalid couch url')
        self.refresh()

        self.new_source_replications = []
        self.order = ORDER
        self.definitions = CHARTS
        self.data = {
            'indexer_task': 0,
            'database_compaction_task': 0,
            'view_compaction_task': 0,
            'replication_task': 0,

        }
    def refresh(self):
        # open active tasks urls
        active_tasks_url = urllib2.urlopen(self.couch_tsk).read()
        self.active_tasks = json.loads(active_tasks_url)
        #  open dbs urls
        all_dbs_url = urllib2.urlopen(self.couch_dbs).read()
        self.all_dbs = json.loads(all_dbs_url)


    # if false -- exit
    # used for dynamic chart creation
    # because check() runs once before run()
    def check(self):
        # no need to refresh() -- first start
        try:
            # init task and DBs per task presentation
            for monitoring_task in self.tasks_to_monitor:
                self.data[monitoring_task + '_task'] = 0
                for db in self.all_dbs:
                    if db[0] == '_': continue
                    self.data[monitoring_task + '_' + db] = 0
                    CHARTS[monitoring_task]['lines'].append(
                        [monitoring_task + '_' + db, db, 'absolute', 1, 1])

            # init replication charts
            status = self.create_replication_charts()
            return status
        except:
            self.error("err in check()")
            return False

    def fix_source_name(self, source):
        fixed_source_name = ""
        if '/' in source:
            fixed_source_name = source.split('/')[3]
            return fixed_source_name
        else:
            return source

    def create_replication_charts(self):
        # TODO: chart name be like: source + "_source_replication"
        def create(source):
            # fix name
            source = self.fix_source_name(source)

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
            # self.new_replication contains newi source replications only
            # with fixed names (no http://)
            for source in self.new_source_replications:
                create(source)
                self.new_charts.remove(source)
            else:
                # only for replications
                for task in self.active_tasks:
                    if task['type'] == 'replication':
                        source = task['source']
                        create(source)

            return True
        except:
            self.error("err in chart_creation()")
            return False

    def _get_data(self):
        try:
            # get new data
            self.refresh()

            # zero values EVERY time
            for key in self.data.keys():
                self.data[key] = 0

            # calculate running tasks
            for active_task in self.active_tasks:
                for monitoring_task in self.tasks_to_monitor:
                    if monitoring_task == active_task['type']:
                        self.data[monitoring_task + '_task'] += 1

            # calculate dbs per task
            for db in self.all_dbs:
                if db[0] == '_': continue
                for active_task in self.active_tasks:
                    try:
                        active_task_database = active_task['database']
                    except KeyError:
                        active_task_database = self.fix_source_name(active_task['target'])

                    if active_task_database == db:
                        self.data[active_task['type'] + '_' + db] += 1

            # calculate seq for replication task
            for active_task in self.active_tasks:
                if active_task['type'] == 'replication':
                    source = self.fix_source_name(active_task['source'])

                    # TODO: chart name be like: source + "_source_replication"
                    if source not in self.order:
                        self.new_source_replications.append(source)

                    source_seq = active_task['source_seq']
                    local_seq = active_task['source_seq']
                    self.data[source + '_source_seq'] = source_seq
                    self.data[source + '_local_seq'] = local_seq


        except (ValueError, AttributeError):
            return None
        return self.data

    # modified update() to check for a new replication tasks
    def update(self, interval):
        data = self._get_data()
        if data is None:
            self.debug("failed to receive data during update().")
            return False

        updated = False
        # do we have new replication charts to be created?
        if self.new_source_replications:
            self.create_replication_charts()

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

# s = Service(configuration={'priority': 60000, 'retries': 60, 'update_every': 1}, name=None)
# s.check()
# s.update(1)
# s.run()
