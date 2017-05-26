 -*- coding: utf-8 -*-
# DEBUG = True

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
        self.untrack_dbs = self.configuration.get('untrack_dbs', ['_replicator', '_users'])
        self.baseurl = self.configuration.get('url')
        self.active_tasks_url = '{}_active_tasks/'.format(self.baseurl)
        self.user = self.configuration.get('couch_username') or None
        self.password = self.configuration.get('couch_password') or None
        self.encoded_auth = None
        if self.user and self.password:
            self.encoded_auth = base64.encodestring('%s:%s' % (self.user, self.password)).replace('\n, ''')
        self.data = {}

    def check(self):
        try:
            check_dbs = self.monitoring_dbs[:]
            for db in check_dbs:
                status = self._get_db_stats(db)
                if not status:
                    self.error('Cant connect to database %s, passing it' % db)
                    self.monitoring_dbs.remove(db)
                    if len(self.monitoring_dbs) == 0:
                        self.error('No more databases left.')
                        return False
                else:
                    self.info('Database %s checked' % db)
                    self.__create_stats_charts(db)
        except Exception as e:
            self.error('Error in check: {}'.format(str(repr(e))))
            return False
        return True

    def _get_responce(self, url):
        """
        Return json-formated list from url
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
            if 'source_seq' in key or 'check_seq' in key:
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

    def _get_db_stats(self, db_name):
        """
        Get data from http://localhost:couch_port/db_name/
        and store it in self.data.
        :param db_name: str
        :return: None or False
        """
        db_stats_url = '{}/{}'.format(self.baseurl, db_name)
        db_stats = self._get_responce(db_stats_url)
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
                return True
            except (ValueError, AttributeError) as e:
                self.error('Cant get database stats: {}'.format(str(repr(e))))
                return False

    def _get_replication_data(self):
        return True

    def __create_stats_charts(self, db_name):
        """
        Called only from check
        :param db_name: str
        :return: None
        """
        documents_delta = '{}_database_documents_delta'.format(db_name)
        documents = '{}_database_documents'.format(db_name)
        fragmentation = '{}_database_fragmentation'.format(db_name)
        seq_delta = '{}_database_seq_delta'.format(db_name)
        seq = '{}_database_seq'.format(db_name)
        self.order.extend((
            documents_delta,
            documents,
            fragmentation,
            seq_delta,
            seq))

        for chart in self.order:
            self.definitions[chart] = {'options': [], 'lines': []}

        self.definitions[documents_delta]['options'] = \
            [None, 'Documents delta', 'documents', 'Database '.format(db_name), '', 'line']
        self.definitions[documents_delta]['lines'].extend((
            ['{}_doc_delta'.format(db_name), 'docs', 'absolute', 1, 1],
            ['{}_docs_deleted_delta', 'docs_deleted', 'absolute', 1, 1]
        ))

        self.definitions[documents]['options'] = \
            [None, 'Documents count', 'documents', 'Database '.format(db_name), '', 'line']
        self.definitions[documents]['lines'].extend((
            ['{}_docs'.format(db_name), 'docs', 'absolute', 1, 1],
            ['{}_docs_deleted'.format(db_name), 'docs_deleted', 'absolute', 1, 1]
        ))

        self.definitions[fragmentation]['options'] = \
            [None, 'Database fragmentation', 'Megabytes', 'Database '.format(db_name), '', 'stacked']
        self.definitions[fragmentation]['lines'].extend((
            ['{}_disk_size_overhead'.format(db_name), 'disk size overhead', 'absolute', 1, 1],
            ['{}_data_size'.format(db_name), 'data size', 'absolute', 1, 1]
        ))

        self.definitions[seq_delta]['options'] = \
            [None, 'Database seq delta', 'seq', 'Database '.format(db_name), '', 'line']
        self.definitions[seq_delta]['lines'].extend((
            ['{}_committed_db_seq_delta'.format(db_name), 'committed seq', 'absolute', 1, 1],
            ['{}_update_db_seq_delta'.format(db_name), 'update seq', 'absolute', 1, 1]
        ))

        self.definitions[seq]['options'] = \
            [None, 'Database seq', 'seq', 'Database '.format(db_name), '', 'line']
        self.definitions[seq]['lines'].extend((
            ['{}_committed_db_seq'.format(db_name), 'committed seq', 'absolute', 1, 1],
            ['{}_update_db_seq'.format(db_name), 'update seq', 'absolute', 1, 1]
        ))

    def __create_replication_charts(self, db_name):
        return True

    def _get_data(self):
        self.__flush_data()
        for db in self.monitoring_dbs:
            self._get_db_stats(db)
        return self.data


# if DEBUG:
#
#     s = Service(
#         configuration={
#             'update_every': 1,
#             'retries': 60,
#             'priority': 60000
#         }
#     )
#     s.baseurl = 'http://10.0.0.10:5984'
#     s.monitoring_dbs = ['one','two','three','four']
#     s.check()
#     s.create()
#     s.update(1)
#     s.run()