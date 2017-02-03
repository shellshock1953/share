# -*- coding: utf-8 -*-
# Description: CouchDB statistics netdata python.d module

from base import SimpleService
import json
try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

# defaults
priority = 70000
retries = 60
update_every = 10

ORDER = []
CHARTS = {}


def parser(doc):
    """ convert json data into category+subcategory+item vars """

    result_dict = {}
    categories = doc.keys()
    ORDER = categories
    CHARTS = {}
    CHARTS_lines = []

    for category in categories:
        subcategories = doc[category].keys()
        for subcategory in subcategories:
            items = doc[category][subcategory].keys()
            for item in items:
                if isinstance(doc[category][subcategory][item], unicode):
                    continue
                elif doc[category][subcategory][item] is None:
                    doc[category][subcategory][item] = 0

                name = category+'_'+subcategory+'_'+item
                chart_name = subcategory+'_'+item
                result_dict[name] = doc[category][subcategory][item]
                CHARTS_lines.append([name, chart_name, 'absolute', 1, 1])

        # create dymamics charts based on categories
        CHARTS[category] = {
           'options': [None, category, 'requests', '', '', 'stacked'],
           'lines': CHARTS_lines
        }
        CHARTS_lines = []

    return ORDER, CHARTS, result_dict


class Service(SimpleService):

    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.couch_url = configuration['couch_url']
        if len(self.couch_url) == 0:
            raise Exception('Invalid couch_url')
        try:
            response = urllib2.urlopen(self.couch_url).read()
            doc = json.loads(responce)
            ORDER, CHARTS, DATA = parser(doc)
        except (ValueError, AttributeError):
            return None

        self.order = ORDER
        self.definitions = CHARTS
        self.data = DATA

    def _get_data(self):
        return self.data
