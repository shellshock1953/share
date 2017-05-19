# import sys
# sys.path.append('/data/shellshock/install/netdata/python.d/python_modules/')
from base import UrlService
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
        self.monitoring_dbs = self.configuration.get('monitoring_dbs')
        # self.monitoring_dbs = ['one']
        self.untrack_dbs = self.configuration.get('untrack_dbs', ['_replicator', '_users'])

        # urls
        self.baseurl = str(self.configuration.get('url'))
        # self.baseurl = 'http://10.0.0.10:5984/'
        self.active_tasks_url = str(self.baseurl + '_active_tasks/')
        self.all_dbs_url = str(self.baseurl + '_all_dbs/')

        # auth
        self.user = self.configuration.get('couch_username') or None
        # self.user = 'admin'
        self.password = self.configuration.get('couch_password') or None
        # self.password = 'admin'
        if self.user:
            self.base64string = base64.encodestring('%s:%s' % (self.user, self.password)).replace('\n', '')

        self.data = {}

    # def _get_all_dbs(self):
    #     self.url = self.all_dbs_url
    #     all_dbs = self._get_raw_data()
    #     return all_dbs

    def _get_db_stat(self, db_name):
        self.url = str(self.baseurl + db_name)
        try:
            request = urllib2.Request(self.url)
            if self.user:
                request.add_header("Authorization", "Basic %s" % self.base64string)
            db_stat_url = urllib2.urlopen(request).read()
            db_stat = json.loads(db_stat_url)
        except IOError as e:
            self.error(repr(e))
            self.error('Cant connect to %s. Check db is running and auth data is correct' % db_name)
            db_stat = None
        return db_stat

    def _get_active_tasks(self):
        self.url = self.active_tasks_url
        try:
            request = urllib2.Request(self.url)
            if self.user:
                request.add_header("Authorization", "Basic %s" % self.base64string)
            active_tasks_url = urllib2.urlopen(request).read()
            active_tasks = json.loads(active_tasks_url)
        except IOError as e:
            self.error(repr(e))
            self.error('Cant connect to CouchDB. Check service is running and auth data is correct')
            active_tasks = None
            self.ERROR = True
        return active_tasks

    def _get_data(self):
        def calc_delta(*args):
            # calc 'new - previous' values
            # result stored in DELTA{}
            for metric in args:
                if self.data[metric] is None:
                    self.data[metric] = 0
                if metric not in DELTA:  # if no such metric in DELTA (first run) -- store it!
                    DELTA[metric] = self.data[metric]
                current = self.data[metric]  # save current untouched value
                difference = self.data[metric] - DELTA[metric]  # current - previous
                self.data[metric] = difference  # prevent negative values (example -- doc deleting)
                DELTA[metric] = current  # save current for future use

        def get_host_and_db(url):
            import re
            if 'http' in url:
                if '@' in url:
                    # http://chronograph:*****@localhost:5984/openprocurement_chronograph/
                    source = re.split('[/:@]', url)[5]
                    db = re.split('[/:@]', url)[7]
                else:
                    # http://localhost:5984/openprocurement_chronograph/
                    source = re.split('[/:@]', url)[3]
                    db = re.split('[/:@]', url)[5]
            else:
                source = 'localhost'
                db = url
            return source, db

        def new_data(chart_var):
            if chart_var not in self._dimensions:
                return True

        try:
            # zero values EVERY time
            for key in self.data.keys():
                if 'source_seq' in key or 'destionation_seq' in key:
                    # if replication task disappear need to destroy metrics
                    # pdb.set_trace()
                    del self.data[key]
                else:
                    self.data[key] = 0

            # get new data
            # all_dbs = self._get_all_dbs()
            active_tasks = self._get_active_tasks()
            for db_name in self.monitoring_dbs:
                db_stats = self._get_db_stat(db_name)
                if db_stats is None:
                    self.error('Cant connect to %s.' % db_name)
                    continue
                # pdb.set_trace()

                # error handler

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
                calc_delta(db_name + '_docs_delta', db_name + '_docs_deleted_delta')
                # update_seq
                self.data[db_name + '_committed_db_seq'] = db_stats['committed_update_seq']
                self.data[db_name + '_update_db_seq'] = db_stats['update_seq']
                self.data[db_name + '_committed_db_seq_delta'] = db_stats['committed_update_seq']
                self.data[db_name + '_update_db_seq_delta'] = db_stats['update_seq']
                calc_delta(db_name + '_committed_db_seq_delta',db_name + '_update_db_seq_delta')

                """ Get db stats from /_active_task """
                if active_tasks:
                    for active_task in active_tasks:
                        if active_task['type'] == 'replication': # and db_name in active_task['target']:
                            # get normal db and host names
                            source_host, source_db = get_host_and_db(active_task['source'])
                            destination_host, destination_db = get_host_and_db(active_task['target'])

                            if db_name == destination_db:
                                repl_type = 'pull'
                            elif db_name == source_db:
                                repl_type = 'push'
                            # get values
                            source_seq = active_task['source_seq']
                            checkpointed_seq = active_task['checkpointed_source_seq']
                            # var name
                            source_seq_name = '{}:{}_{}_source_seq'.format(source_host, source_db, repl_type)
                            source_seq_name_delta = source_seq_name + '_delta'
                            checkpointed_seq_name = '{}:{}_{}_chekpointed_seq'.format(source_host, source_db, repl_type)
                            checkpointed_seq_name_delta = checkpointed_seq_name + '_delta'
                            # chart name
                            source_chart_name = 'source_seq {}:{}'.format(source_host, source_db)
                            checkpointed_chart_name = 'checkpointed_source_seq {}:{}'.format(source_host, source_db)
                            # send values into self.data
                            self.data[source_seq_name] = source_seq
                            self.data[checkpointed_seq_name] = checkpointed_seq
                            # delta vars
                            self.data[source_seq_name_delta] = source_seq
                            self.data[checkpointed_seq_name_delta] = checkpointed_seq
                            calc_delta(source_seq_name_delta, checkpointed_seq_name_delta)
                            # check for a new data
                            # if any -- we need to create new charts or add into chart new lines
                            if new_data(source_seq_name):
                                self.append_new_lines(db_name, source_seq_name, source_chart_name, repl_type)
                            if new_data(checkpointed_seq_name):
                                self.append_new_lines(db_name, checkpointed_seq_name, checkpointed_chart_name, repl_type)

        except (ValueError, AttributeError):
            # no need to set self.ERROR to True
            # we give plugin a chance to get new data
            # if not -- Netdata will kill plugin after gone of retries (set via conf file)
            self.error('error in _get_data()')
            return None
        return self.data

    def check(self):
        # check CouchDB connection
        # if no -- set self.ERROR to True
        self._get_active_tasks()
        self.debug('active tasks checked')
        for db_name in self.monitoring_dbs:
            # trying to connect to current db
            try:
                self.url = self.active_tasks_url
                request = urllib2.Request(self.url)
                if self.user:
                    request.add_header("Authorization", "Basic %s" % self.base64string)
                db_stat_url = urllib2.urlopen(request).read()
                self.debug('database %s checked' % db_name)
            except IOError as e:
                self.error(repr(e))
                self.error('%s removing from monitoring dbs' % db_name)
                self.monitoring_dbs.remove(db_name)
                continue

        if len(self.monitoring_dbs) == 0:
            self.error('No more dbs left...')
            self.ERROR = True

        if self.ERROR:
            self.error('exiting.')
            return False
        else:
            # pdb.set_trace()
            # TODO: reformat check() to get all possible errors and if any halt plugin
            # everything seems ok.
            # now we can create dynamic charts
            for db_name in self.monitoring_dbs:
                self.order.append(db_name + '_database_documents_delta')
                self.order.append(db_name + '_database_documents')
                self.order.append(db_name + '_database_fragmentation')
                self.order.append(db_name + '_database_seq_delta')
                self.order.append(db_name + '_database_seq')

                self.definitions[db_name + '_database_documents_delta'] = {'options': [], 'lines': []}
                self.definitions[db_name + '_database_documents_delta'] \
                    ['options'] = [None, 'Documents delta', 'documents', 'Database ' + db_name, '', 'line']
                self.definitions[db_name + '_database_documents_delta'] \
                    ['lines'].append([db_name + '_docs_delta', 'docs', 'absolute', 1, 1])
                self.definitions[db_name + '_database_documents_delta'] \
                    ['lines'].append([db_name + '_docs_deleted_delta', 'docs_deleted', 'absolute', 1, 1])

                self.definitions[db_name + '_database_documents'] = {'options': [], 'lines': []}
                self.definitions[db_name + '_database_documents'] \
                    ['options'] = [None, 'Documents count', 'documents', 'Database ' + db_name, '', 'line']
                self.definitions[db_name + '_database_documents'] \
                    ['lines'].append([db_name + '_docs', 'docs', 'absolute', 1, 1])
                self.definitions[db_name + '_database_documents'] \
                    ['lines'].append([db_name + '_docs_deleted', 'docs_deleted', 'absolute', 1, 1])

                self.definitions[db_name + '_database_fragmentation'] = {'options': [], 'lines': []}
                self.definitions[db_name + '_database_fragmentation'] \
                    ['options'] = [None, 'Database fragmentation', 'Megabytes', 'Database ' + db_name, '', 'stacked']
                self.definitions[db_name + '_database_fragmentation'] \
                    ['lines'].append([db_name + '_disk_size_overhead', 'disk size overhead', 'absolute', 1, 1])
                self.definitions[db_name + '_database_fragmentation'] \
                    ['lines'].append([db_name + '_data_size', 'data size', 'absolute', 1, 1])

                self.definitions[db_name + '_database_seq_delta'] = {'options': [], 'lines': []}
                self.definitions[db_name + '_database_seq_delta'] \
                    ['options'] = [None, 'Database seq delta', 'seq', 'Database ' + db_name, '', 'line']
                self.definitions[db_name + '_database_seq_delta'] \
                    ['lines'].append([db_name + '_committed_db_seq_delta', 'committed seq', 'absolute', 1, 1])
                self.definitions[db_name + '_database_seq_delta'] \
                    ['lines'].append([db_name + '_update_db_seq_delta', 'update seq', 'absolute', 1, 1])

                self.definitions[db_name + '_database_seq'] = {'options': [], 'lines': []}
                self.definitions[db_name + '_database_seq'] \
                    ['options'] = [None, 'Database seq', 'seq', 'Database ' + db_name, '', 'line']
                self.definitions[db_name + '_database_seq'] \
                    ['lines'].append([db_name + '_committed_db_seq', 'committed seq', 'absolute', 1, 1])
                self.definitions[db_name + '_database_seq'] \
                    ['lines'].append([db_name + '_update_db_seq', 'update seq', 'absolute', 1, 1])

            return True

    def append_new_lines(self, db_name, chart_var, chart_name, repl_type):

        chart_var_delta = chart_var + '_delta'
        chart_name_delta = 'delta_' + chart_name

        # meens firts time chart created
        if db_name + '_' + repl_type + '_replication_seq' not in self.order:
            self.info(
                'adding new lines of %s replication task: db_name: %s - chart_var: %s' % (repl_type, db_name, chart_var))
            self.order.append(db_name + '_' + repl_type + '_replication_seq_delta')
            self.order.append(db_name + '_' + repl_type + '_replication_seq')

            self.definitions[db_name + '_' + repl_type + '_replication_seq_delta'] = {'options': [], 'lines': []}
            self.definitions[db_name + '_' + repl_type + '_replication_seq'] = {'options': [], 'lines': []}

            self.definitions[db_name + '_' + repl_type + '_replication_seq_delta'] \
                ['options'] = [None, repl_type + ' replications seq delta', 'seq', 'Database ' + db_name, '', 'line']
            self.definitions[db_name + '_' + repl_type + '_replication_seq'] \
                ['options'] = [None, repl_type + ' replications seq', 'seq', 'Database ' + db_name, '', 'line']


        # can be added even if chart was created previous
        # must to add lines only
        self._dimensions.append(str(chart_var_delta))
        self._dimensions.append(str(chart_var))
        self.definitions[db_name + '_' + repl_type + '_replication_seq_delta']['lines'].append(
            [chart_var_delta, chart_name_delta, 'absolute', 1, 1]
        )
        self.definitions[db_name + '_' + repl_type + '_replication_seq']['lines'].append(
            [chart_var, chart_name, 'absolute', 1, 1]
        )
        # cant find other solutions
        # self.check()  # if not: wrong dimension id: replication_localhost.first_localhost.second Available dimensions are: indexer_task
        self.create()  # if not: Cannot find dimension with id 'replication_localhost.first_localhost.second'

# s = Service(configuration={'update_every':1,'priority':33333,'retries':60})
# s.check()
# s.create()
# s.update(1)
# s.run()