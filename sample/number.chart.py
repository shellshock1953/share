from base import LogService


priority = 60000
retries = 60

ORDER = ['number']
CHARTS = {
    'number': {
        #           name, 'title',          'units',     'family',      'context', 'line'],
        'options': [None, 'Number in file', 'units', '', '', 'line'],
        'lines': [
        # [unique_dimension_name, name, algorithm, multiplier, divisor]
            ['number', None, 'absolute', 1, 1],
        ]
    }
}


class Service(LogService):
    def __init__(self, configuration=None, name=None):
        LogService.__init__(self, configuration=configuration, name=name)
        self.log_path = configuration['file']
        if len(self.log_path) == 0:
            raise Exception('Invalid log path')
        self.order = ORDER
        self.definitions = CHARTS
        self.data = {
            'number': 0
        }

    def _get_data(self):
        self.data['number'] = 0
        try:
            raw = self._get_raw_data()
            if raw is None:
                return None
            elif not raw:
                return self.data
        except (ValueError, AttributeError):
            return None
        self.data['number'] = raw

        # for line in raw:
        #     if 'Save' in line:
        #         self.data['save'] += 1
        #     elif 'Update' in line:
        #         self.data['update'] += 1

        return self.data
