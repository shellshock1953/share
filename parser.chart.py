# -*- coding: utf-8 -*-
# Description: CouchDB statistics netdata python.d module

# from base import SimpleService

import json
import pprint
try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

# defaults
priority = 70000
retries = 60
update_every = 1


def parser(doc):
    global ORDER
    result_dict = {}
    categories = doc.keys()
    ORDER = categories
    CHARTS = {}
    lines = []

    for category in categories:
        subcategories = doc[category].keys()
        for subcategory in subcategories:
            items = doc[category][subcategory].keys()
            for item in items:
                if isinstance(doc[category][subcategory][item], unicode):
                    description = doc[category][subcategory][item]
                    continue
                elif doc[category][subcategory][item] is None:
                    doc[category][subcategory][item] = 0

                result_dict[category+'_'+subcategory+'_'+item] = \
                    doc[category][subcategory][item]
                lines.append(
                    [item,
                     item,
                     'incremental', 1, 1 ]
                )

        CHARTS[category] = {
            'options': [None, description, 'requests', '', '', 'stacked'],
            'lines': lines
        }
    return ORDER, CHARTS, result_dict

#f = open('data.json','r').read()
#doc = json.loads(f)
#ORDER, CHARTS, result = parser(doc)
#pprint.pprint(CHARTS)


class Service(SimpleService):

    def __init__(self, configuration=None, name=None):
        SimpleService.__init__(self, configuration=configuration, name=name)
        self.couch_url = configuration['couch_url']
        if len(self.couch_url) == 0:
            raise Exception('Invalid couch_url')

        try:
            response = urllib2.urlopen(self.couch_url).read()
            doc = json.loads(response)
            ORDER, CHARTS, data = parser(doc)
        except (ValueError, AttributeError):
            return None

        self.order = ORDER
        self.definitions = CHARTS
        self.data = data

        def _get_data(self):
            return self.data
