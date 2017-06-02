# -*- coding: utf-8 -*-

import base64
import json

from base import SimpleService

try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

DELTA = {}


class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.monitoring_dbs = self.configuration.get('monitoring_dbs')
        self.monitoring_dbs = ['one', 'two']
        # self.untrack_dbs = self.configuration.get('untrack_dbs', ['_replicator', '_users'])
        # self.baseurl = self.configuration.get('url')
        self.baseurl = 'http://10.0.0.10:5984'
        self.active_tasks_url = '{}/_active_tasks/'.format(self.baseurl)
        self.user = self.configuration.get('couch_username') or None
        self.password = self.configuration.get('couch_password') or None
        self.encoded_auth = None
        if self.user and self.password:
            self.encoded_auth = base64.encodestring('%s:%s' % (self.user, self.password)).replace('\n', '')
        self.repl_order = []
        self.repl_definitions = {}
        self.data = {}
    def check(self):
        try:
            # check connection
            check_dbs = self.monitoring_dbs[:]
            for db in check_dbs:
                status = self._get_stats_data(db)
                if not status:
                    self.error('Cant connect to database %s, passing it' % db)
                    self.monitoring_dbs.remove(db)
                    if len(self.monitoring_dbs) == 0:
                        self.error('No more databases left.')
                        return False
                else:
                    self.info('Database %s checked' % db)

        except Exception as e:
            self.error('Error in check: {}'.format(str(repr(e))))
            return False
        return True

    def _get_response(self, url):
        """
        Return json-formatted list from url
        :param url: string
        :return: list or False
        """
        try:
            request = urllib2.Request(url)
            if self.encoded_auth:
                request.add_header("Authorization", "Basic %s" % self.encoded_auth)
            response_raw = urllib2.urlopen(request).read()
            response = json.loads(response_raw)
        except IOError as e:
            self.error('Error in getting {}: {}'.format(url, str(repr(e))))
            response = False
        return response

    def __flush_data(self):
        # !!! POSSIBLE ISSUES
        for key in self.data.keys():
            if 'source_seq' in key or 'checkpointed_seq' in key:
                del self.data[key]
            else:
                self.data[key] = 0

    def __calc_delta(self, *args):
        """
        Calc delta (difference) between current and previous metric data 
        :param args: str
        :return: None
        """
        for metric in args:
            delta_metric = '{}_delta'.format(metric)
            if self.data[metric] is None:
                self.data[metric] = 0
            if metric not in DELTA:
                DELTA[metric] = self.data[metric]
            current = self.data[metric]
            difference = self.data[metric] - DELTA[metric]
            self.data[delta_metric] = difference
            DELTA[metric] = current

    def __get_host_and_db(self, url):
        """
        Cut and return host and db of remote server from given url 
        :param url: str
        :return: str
        """
        import re
        if 'http' in url:
            if '@' in url:  # if auth
                source = re.split('[/:@]', url)[5]
                db = re.split('[/:@]', url)[7]
            else:
                source = re.split('[/:]', url)[3]
                db = re.split('[/:@]', url)[5]
        else:
            source = 'localhost'
            db = url
        return source, db

    def _get_stats_data(self, db_name):
        """
        Get data from http://localhost:couch_port/db_name/
        and store it in self.data.
        :param db_name: str
        :return: None or False
        """
        db_stats_url = '{}/{}'.format(self.baseurl, db_name)
        db_stats = self._get_response(db_stats_url)
        if not db_stats:
            return False
        else:
            try:
                self.data['{}_data_size'.format(db_name)] = db_stats['data_size'] / 1000000
                self.data['{}_disk_size_overhead'.format(db_name)] = \
                    (db_stats['disk_size'] - db_stats['data_size']) / 1000000
                self.data['{}_docs'.format(db_name)] = db_stats['doc_count']
                self.data['{}_docs_deleted'.format(db_name)] = db_stats['doc_del_count']
                self.data['{}_committed_db_seq'.format(db_name)] = \
                    db_stats['committed_update_seq']
                self.data['{}_update_db_seq'.format(db_name)] = db_stats['update_seq']
                self.__calc_delta(
                    '{}_docs'.format(db_name),
                    '{}_docs_deleted'.format(db_name),
                    '{}_committed_db_seq'.format(db_name),
                    '{}_update_db_seq'.format(db_name)
                )
                self.__create_stats_charts(db_name)
            except (ValueError, AttributeError) as e:
                self.error('Cant get database stats: {}'.format(str(repr(e))))
                return False
        return True

    def __create_stats_charts(self, db_name):
        """
        Called only from check()
        :param db_name: str
        :return: order, definitions
        """
        order = []
        definitions = {}
        documents_delta = '{}_database_documents_delta'.format(db_name)
        documents = '{}_database_documents'.format(db_name)
        fragmentation = '{}_database_fragmentation'.format(db_name)
        seq_delta = '{}_database_seq_delta'.format(db_name)
        seq = '{}_database_seq'.format(db_name)
        order.extend((
            documents_delta,
            documents,
            fragmentation,
            seq_delta,
            seq))

        for chart in order:
            definitions[chart] = {'options': [], 'lines': []}

        definitions[documents_delta]['options'] = \
            [None, 'Documents delta', 'documents', 'Database {}'.format(db_name), '', 'line']
        definitions[documents_delta]['lines'].extend((
            ['{}_docs_delta'.format(db_name), 'docs delta', 'absolute', 1, 1],
            ['{}_docs_deleted_delta'.format(db_name), 'docs_deleted delta', 'absolute', 1, 1]
        ))
        definitions[documents]['options'] = \
            [None, 'Documents count', 'documents', 'Database {}'.format(db_name), '', 'line']
        definitions[documents]['lines'].extend((
            ['{}_docs'.format(db_name), 'docs', 'absolute', 1, 1],
            ['{}_docs_deleted'.format(db_name), 'docs_deleted', 'absolute', 1, 1]
        ))
        definitions[fragmentation]['options'] = \
            [None, 'Database fragmentation', 'Megabytes', 'Database {}'.format(db_name), '', 'stacked']
        definitions[fragmentation]['lines'].extend((
            ['{}_disk_size_overhead'.format(db_name), 'disk size overhead', 'absolute', 1, 1],
            ['{}_data_size'.format(db_name), 'data size', 'absolute', 1, 1]
        ))
        definitions[seq_delta]['options'] = \
            [None, 'Database seq delta', 'seq', 'Database {}'.format(db_name), '', 'line']
        definitions[seq_delta]['lines'].extend((
            ['{}_committed_db_seq_delta'.format(db_name), 'committed seq', 'absolute', 1, 1],
            ['{}_update_db_seq_delta'.format(db_name), 'update seq', 'absolute', 1, 1]
        ))
        definitions[seq]['options'] = \
            [None, 'Database seq', 'seq', 'Database {}'.format(db_name), '', 'line']
        definitions[seq]['lines'].extend((
            ['{}_committed_db_seq'.format(db_name), 'committed seq', 'absolute', 1, 1],
            ['{}_update_db_seq'.format(db_name), 'update seq', 'absolute', 1, 1]
        ))
        self.order = self.order + order
        self.definitions.update(definitions)

    def _get_replication_data(self, db_name):
        """
        Get replication data from /_active_tasks
        :param db_name: str
        :return: None or False
        """
        active_tasks = self._get_response(self.active_tasks_url)
        if not active_tasks:
            return None
        else:
            for active_task in active_tasks:
                if active_task['type'] == "replication":
                    source_host, source_db = self.__get_host_and_db(active_task['source'])
                    target_host, target_db = self.__get_host_and_db(active_task['target'])

                    if target_host == 'localhost' and target_db == db_name:
                        repl_type = 'pull'
                    elif target_host != 'localhost' and source_db == db_name:
                        repl_type = 'push'
                    else:
                        continue
                    # values
                    source_seq = active_task['source_seq']
                    checkpointed_seq = active_task['checkpointed_source_seq']
                    # var names
                    source_seq_name = '{}:{}_{}_source_seq'.format(source_host, source_db, repl_type)
                    checkpointed_seq_name = '{}:{}_checkpointed_seq'.format(source_host, source_db, repl_type)
                    # chart var
                    source_chart_name = 'source_seq {}:{}'.format(source_host, source_db)
                    checkpointed_chart_name = 'checkpointed_source_seq {}:{}'.format(source_host, source_db)
                    self.data[source_seq_name] = source_seq
                    self.data[checkpointed_seq_name] = checkpointed_seq
                    self.__calc_delta(
                        source_seq_name,
                        checkpointed_seq_name
                    )

                    # need to create charts
                    self.__create_replication_charts(db_name, source_chart_name, source_seq_name, repl_type)
                    self.__create_replication_charts(db_name, checkpointed_chart_name, checkpointed_seq_name,
                                                     repl_type)
            self.order = self.order + self.repl_order
            self.definitions.update(self.repl_definitions)

    def __create_replication_charts(self, db_name, chart_name, var_name, repl_type):
        """
        :param db_name: db
        :param chart_name: source_seq host:db
        :param var_name: host:db_pull_source_seq
        :param repl_type: pull
        :return: order, definitions
        """
        dimension_name = '{}_{}_replication_seq'.format(db_name, repl_type)
        dimension_name_delta = '{}_{}_replication_seq_delta'.format(db_name, repl_type)

        chart_name_delta = '{}_delta'.format(chart_name)
        var_name_delta = '{}_delta'.format(var_name)

        if self.repl_definitions == {}:  # first run
            if dimension_name not in self.order:
                self.repl_order.append(dimension_name_delta)
                self.repl_order.append(dimension_name)

                for chart in self.repl_order:
                    self.repl_definitions[chart] = {'options': [], 'lines': []}

        self.repl_definitions[dimension_name_delta]['options'] = \
            [None, '{} replication seq delta'.format(repl_type), 'seq', 'Database {}'.format(db_name), '', 'line']
        self.repl_definitions[dimension_name]['options'] = \
            [None, '{} replication seq'.format(repl_type), 'seq', 'Database {}'.format(db_name), '', 'line']

        self.repl_definitions[dimension_name_delta]['lines'].append(
            [var_name_delta, chart_name_delta, 'absolute', 1, 1]
        )
        self.repl_definitions[dimension_name]['lines'].append(
            [var_name, chart_name, 'absolute', 1, 1]
        )

    def _get_data(self):
        create = False
        temp_order = self.order[:]
        temp_definitions = self.definitions.copy()
        #  clear
        self.__flush_data()
        self.order = []
        self.definitions = {}
        #  get data
        for db in self.monitoring_dbs:
            self._get_stats_data(db)
            self._get_replication_data(db)
            self.repl_order = []
            self.repl_definitions = {}
        # check new data
        if temp_order != self.order or temp_definitions != self.definitions:
            create = True
        # create charts
        if create: self.create()
        return self.data

    def create(self):
        """
        Create charts
        :return: boolean
        """
        # data = self._get_data()
        # if data is None:
        #     return False

        idx = 0
        for name in self.order:
            options = self.definitions[name]['options'] + [self.priority + idx, self.update_every]
            self.chart(self.chart_name + "." + name, *options)
            # check if server has this datapoint
            for line in self.definitions[name]['lines']:
                if line[0] in self.data:
                    self.dimension(*line)
            idx += 1

        self.commit()
        return True

#
DEBUG = True
if DEBUG:
    s = Service(
        configuration={
            'update_every': 1,
            'retries': 60,
            'priority': 60000
        }
    )
    s.check()
    s.create()
    s.run()
