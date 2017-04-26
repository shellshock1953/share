from base import UrlService
import pdb
import base64
import json

try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

# DELTA contains previous metrics, to calculate difference 'now - previous'
# used to avoid non-integer metric presentation in Netdata dashboard
DELTA = {}


class Service(UrlService):
    def __init__(self, configuration=None, name=None):
        self.ERROR = False
        UrlService.__init__(self, configuration=configuration, name=name)
        self.order = []
        self.definitions = {}

        # config parsing
        self.monitoring_tasks = self.configuration.get('monitoring_tasks')
        self.monitoring_dbs = self.configuration.get('monitoring_dbs')
        self.untrack_dbs = self.configuration.get('untrack_dbs', ['_replicator', '_users'])

        # urls
        self.baseurl = str(self.configuration.get('url'))
        self.active_tasks_url = str(self.baseurl + '_active_tasks/')
        self.all_dbs_url = str(self.baseurl + '_all_dbs/')

        # auth
        self.user = self.configuration.get('user') or None
        self.password = self.configuration.get('pass') or None
        if self.user:
            self.base64string = base64.encodestring('%s:%s' % (self.user, self.password)).replace('\n', '')

        self.data = {}

    # def _get_all_dbs(self):
    #     self.url = self.all_dbs_url
    #     all_dbs = self._get_raw_data()
    #     return all_dbs

    def _get_db_stat(self, db_name):
        self.url = str(self.baseurl + db_name)
        self.ERROR = False
        try:
            request = urllib2.Request(self.url)
            if self.user:
                request.add_header("Authorization", "Basic %s" % self.base64string)
            db_stat_url = urllib2.urlopen(request).read()
            db_stat = json.loads(db_stat_url)
        except IOError:
            self.error('Cant connect to %s. Check db is running and auth data is correct' % db_name)
            self.ERROR = True
        return db_stat

    def _get_active_tasks(self):
        # pdb.set_trace()
        self.ERROR = False
        self.url = self.active_tasks_url
        try:
            request = urllib2.Request(self.url)
            if self.user:
                request.add_header("Authorization", "Basic %s" % self.base64string)
            active_tasks_url = urllib2.urlopen(request).read()
            active_tasks = json.loads(active_tasks_url)
        except IOError:
            self.error('Cant connect to couchdb. Check db is running and auth data is correct')
            self.ERROR = True
        return active_tasks

    def _get_data(self):
        def calc_delta(*args):
            """
           calc 'new - previous' values
           result stored in DELTA{}
           """
            for metric in args:
                if self.data[metric] is None: self.data[metric] = 0
                if metric in DELTA:
                    # prevent negative values
                    if self.data[metric] < DELTA[metric]:
                        DELTA[metric] = 0
                        return None
                    previous = self.data[metric]
                    self.data[metric] = self.data[metric] - DELTA[metric]
                    DELTA[metric] = previous
                else:
                    DELTA[metric] = self.data[metric]

        def get_host_and_db(url):
            import re
            if 'http' in url:
                if '@' in url:
                    # http://chronograph:*****@localhost:5984/openprocurement_chronograph/
                    source = re.split('/|:|@', url)[5]
                    db = re.split('/|:|@', url)[7]
                else:
                    # http://localhost:5984/openprocurement_chronograph/
                    source = re.split('/|:|@', url)[3]
                    db = re.split('/|:|@', url)[5]
            else:
                source = 'localhost'
                db = url
            return source

        def check_new_data(db_name, chart_var):
            if chart_var not in self._dimensions:
                self.append_new_lines(db_name, chart_var)

        try:
            # zero values EVERY time
            for key in self.data.keys():
                self.data[key] = 0

            # get new data
            # all_dbs = self._get_all_dbs()
            active_tasks = self._get_active_tasks()
            for db_name in self.monitoring_dbs:
                db_stats = self._get_db_stat(db_name)
                # pdb.set_trace()

                # error handler
                if self.ERROR:
                    self.error('Error in getting data')
                    return None
                else:

                    """ Get general /db stats """
                    # DB fragmentation
                    self.data[db_name + '_data_size'] = db_stats['data_size'] / 1000000
                    self.data[db_name + '_disk_size_overhead'] = \
                        (db_stats['disk_size'] - db_stats['data_size']) / 1000000
                    # DB documents
                    self.data[db_name + '_docs'] = db_stats['doc_count']
                    self.data[db_name + '_docs_deleted'] = db_stats['doc_del_count']
                    # DB delta documents
                    self.data[db_name + '_docs_delta'] = db_stats['doc_count']
                    self.data[db_name + '_docs_deleted_delta'] = db_stats['doc_del_count']
                    calc_delta(db_name + '_docs_delta',
                               db_name + '_docs_deleted_delta')
                    # update_seq
                    self.data[db_name + '_db_seq'] = db_stats['committed_update_seq']
                    calc_delta(db_name + '_db_seq')

                    """ Get db stats from /_active_task """
                    if active_tasks:
                        for active_task in active_tasks:
                            if active_task['type'] == 'replication' and db_name in active_task['target']:
                                source = get_host_and_db(active_task['source'])
                                # target = get_host_and_db(active_task['target'])

                                source_seq = active_task['source_seq']
                                local_seq = active_task['checkpointed_source_seq']
                                source_seq_name = db_name + '_' + source + '_source_seq'
                                local_seq_name = db_name + '_' + source + '_local_seq'
                                self.data[source_seq_name] = source_seq
                                self.data[local_seq_name] = local_seq
                                calc_delta(source_seq_name, local_seq_name)
                                check_new_data(db_name, source_seq_name)
                                check_new_data(db_name, local_seq_name)

        except (ValueError, AttributeError):
            self.error('error in _get_data()')
            return None
        return self.data

    def check(self):
        # TODO: reformat check()
        # no need to refresh() -- first start
        # dynamic creation in check() because of few databases
        for db_name in self.monitoring_dbs:
            self.definitions[db_name + '_database_documents_delta'] = {'options': [], 'lines': []}
            self.definitions[db_name + '_database_documents_delta']['options'] = [None, 'Documents', 'documents',
                                                                                  'Documents delta', '', 'line']
            self.definitions[db_name + '_database_documents_delta']['lines'].append(
                [db_name + '_docs_delta', 'docs', 'absolute', 1, 1])
            self.definitions[db_name + '_database_documents_delta']['lines'].append(
                [db_name + '_docs_deleted_delta', 'docs_deleted', 'absolute', 1, 1])

            self.definitions[db_name + '_database_documents'] = {'options': [], 'lines': []}
            self.definitions[db_name + '_database_documents']['options'] = [None, 'Documents', 'documents', 'Documents',
                                                                            '', 'line']
            self.definitions[db_name + '_database_documents']['lines'].append(
                [db_name + '_docs', 'docs', 'absolute', 1, 1])
            self.definitions[db_name + '_database_documents']['lines'].append(
                [db_name + '_docs_deleted', 'docs_deleted', 'absolute', 1, 1])

            self.definitions[db_name + '_database_fragmentation'] = {'options': [], 'lines': []}
            self.definitions[db_name + '_database_fragmentation']['options'] = [None, 'Database fragmentation',
                                                                                'Megabytes', 'Database fragmentation',
                                                                                '', 'line']
            self.definitions[db_name + '_database_fragmentation']['lines'].append(
                [db_name + '_disk_size_overhead', 'disk size overhead', 'absolute', 1, 1])
            self.definitions[db_name + '_database_fragmentation']['lines'].append(
                [db_name + '_data_size', 'data size', 'absolute', 1, 1])

            self.definitions[db_name + '_database_seq'] = {'options': [], 'lines': []}
            self.definitions[db_name + '_database_seq']['options'] = [None, 'Database seq', 'seq', 'Database seq', '',
                                                                      'line']
            self.definitions[db_name + '_database_seq']['lines'].append(
                [db_name + '_db_seq', 'db seq', 'absolute', 1, 1])


            self.order.append(db_name + '_database_documents_delta')
            self.order.append(db_name + '_database_documents')
            self.order.append(db_name + '_database_fragmentation')
            self.order.append(db_name + '_database_seq')
        return True

    def append_new_lines(self, db_name, chart_var):
        self.definitions[db_name + '_replication_seq'] = {'options': [], 'lines': []}
        self.definitions[db_name + '_replication_seq']['options'] = [None, 'Replications', 'seq', 'Replication seq',
                                                                     '', 'line']
        self.order.append(db_name + '_replication_seq')

        self._dimensions.append(str(chart_var))
        self.info('adding new lines of replication task: db_name: %s - chart_var: %s' % (db_name, chart_var))
        self.definitions[db_name + '_replication_seq']['lines'].append(
            [chart_var, chart_var, 'absolute', 1, 1]
        )
        # cant find other solutions
        self.check()  # if not: wrong dimension id: replication_localhost.first_localhost.second Available dimensions are: indexer_task
        self.create()  # if not: Cannot find dimension with id 'replication_localhost.first_localhost.second'
