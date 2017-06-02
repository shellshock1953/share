# -*- coding: utf-8 -*-

import base64
import json

from base import SimpleService

try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

ORDER = [
    'active_tasks',
    'indexer_percentage',
    'replication_percentage',
    'database_compaction_percentage',
    'view_compaction_percentage'
]

CHARTS = {
    'active_tasks': {
        'options': [None, 'Active tasks', 'tasks', 'Active tasks', '', 'line'],
        'lines': [
            ['indexer_task', 'indexer', 'absolute', 1, 1],
            ['replication_task', 'replication', 'absolute', 1, 1],
            ['database_compaction_task', 'database_compaction', 'absolute', 1, 1],
            ['view_compaction_task', 'view_compaction', 'absolute', 1, 1],
        ]
    },

    'indexer_percentage': {
        'options': [None, 'Indexer task', 'percentage', 'Indexer task percentage', '', 'line'],
        'lines': []
    },
    'database_compaction_percentage': {
        'options': [None, 'Compaction task', 'percentage', 'Compaction task percentage', '', 'line'],
        'lines': []
    },
    'view_compaction_percentage': {
        'options': [None, 'View compaction task', 'percentage', 'View compaction task percentage', '', 'line'],
        'lines': []
    },
    'replication_percentage': {
        'options': [None, 'Replication task', 'percentage', 'Replication task percentage', '', 'line'],
        'lines': []
    }
}

class Service(SimpleService):
    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        # todo: parce threw config
        self.monitoring_tasks = ['indexer', 'database_compaction', 'view_compaction', 'replication']
        self.order = ORDER
        self.definitions = CHARTS
        self.baseurl = self.configuration.get('url')
        # self.baseurl = 'http://10.0.0.10:5984'
        self.active_tasks_url = '{}/_active_tasks/'.format(self.baseurl)
        self.untrack_dbs = self.configuration.get('untrack_dbs', ['_replicator', '_users'])
        self.user = self.configuration.get('couch_username') or None
        self.password = self.configuration.get('couch_password') or None
        self.encoded_auth = None
        if self.user and self.password:
            self.encoded_auth = base64.encodestring('%s:%s' % (self.user, self.password)).replace('\n', '')
        self.data = {}

        for task in self.monitoring_tasks:
            self.data['{}_task'.format(task)] = 0

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
        for key in self.data.keys():
            self.data[key] = 0

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

    def _get_data(self):
        self.__flush_data()
        active_tasks = self._get_response(self.active_tasks_url)

        for active_task in active_tasks:
            if active_task['type'] in self.monitoring_tasks:
                try:
                    task_name = active_task['type']

                    self.data['{}_task'.format(task_name)] += 1

                    if task_name == 'indexer' or task_name == 'view_compaction':
                        design_document = active_task['disign_document'].replace('/', '_')
                        chart_var = '{}_{}_{}'.format(task_name, active_task['database'], design_document)
                        self.data[chart_var] = active_task['progress']
                        self._check_new_data(task_name, chart_var)
                    if task_name == 'database_compaction':
                        chart_var = '{}_{}'.format(task_name, active_task['database'])
                        self.data[chart_var] = active_task['progress']
                        self._check_new_data(task_name, chart_var)
                    if task_name == 'replication':
                        source_host, source_db = self.__get_host_and_db(active_task['source'])
                        target_host, target_db = self.__get_host_and_db(active_task['target'])
                        chart_var = '{}_{}:{}_{}:{}'.format(task_name, source_host, source_db, target_host, target_db)
                        self.data[chart_var] = active_task['progress']
                        self._check_new_data(task_name, chart_var)
                except (ValueError, AttributeError) as e:
                    self.error('Cant get active tasks data: {}'.format(str(repr(e))))
                    return None
        return self.data

    def _check_new_data(self, task, chart_var):
        if chart_var not in self._dimensions:
            self._append_new_lines(task, chart_var)

    def _append_new_lines(self, task, chart_var):
        # todo: del this f
        self._dimensions.append(chart_var)
        self.definitions['{}_percentage'.format(task)]['lines'].append(
            [chart_var, chart_var, 'absolute', 1, 1]
        )
        self.create()
