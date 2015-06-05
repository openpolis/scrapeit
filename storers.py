#!/usr/bin/env python
#  -*- coding: utf-8 -*-

from datetime import datetime
import json
import logging
import logging.config
import itertools
from requests.auth import _basic_auth_str
from requests.exceptions import HTTPError
import tortilla
from scrapers import DataScraperException

__author__ = 'guglielmo'



logging.config.dictConfig(json.load(open('logging.conf.json')))


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)


class DataStorerException(Exception):
    pass

class DataStorer(object):
    """
    Base DataStorer class from which each class extends.
    Default logger and arguments parser defined
    """

    def __init__(self, **kwargs):
        self.logger = logging.getLogger('import_script')

    def store(self, **kwargs):
        """
        Need to be implemented by extending class.

        :param kwargs:
        :return:
        """
        raise Exception("not implemented")



class ESDataStorer(DataStorer):

    def __init__(self, es_url,
                 es_index, es_doctype,
                 es_batchsize=0, es_delete=False,
                 log_level='info'
    ):
        DataStorer.__init__(self)

        self.log_level = log_level
        self.es_url = es_url
        self.es_index = es_index
        self.es_doctype = es_doctype
        self.es_batchsize = es_batchsize
        self.es_delete = es_delete

        self.logger.setLevel(getattr(logging, self.log_level.upper(), logging.WARNING))

        self.est = tortilla.wrap(self.es_url)

        self.es_setup()




    def get_bulk_data(self, iterator):
        """

        :param file:
        :param minint_url:
        :return:
        """

        # main loop generating bulk data to upload to elastic search index
        bulk_data = []
        for row in iterator:
            if type(row) == tuple:
                self.logger.error(row[0])
                self.logger.error(",".join(row[1].values()))
                continue

            self.logger.debug("Processing: {0}".format(row['unique_id']))

            bulk_data.append({
                'index':{
                    '_index': self.es_index,
                    '_type': self.es_doctype,
                    '_id': row.pop('unique_id')
                }
            })
            bulk_data.append(row)


        return bulk_data


    def store(self, iterator):
        # retrieve bulk_data from minint_url
        bulk_data = self.get_bulk_data(iterator)

        # send bulk_data to elastic search
        if self.es_batchsize <= 0:
            self.es_batchsize = int(len(bulk_data) / 2)
        grouped_bulk_data = grouper(bulk_data, 2*self.es_batchsize)

        self.logger.info(
            "Sending {0} record to elastic search instance, batch_size: {1}".format(
                int(len(bulk_data)/2), self.es_batchsize
            )
        )

        c = 0
        for group in grouped_bulk_data:
            cleaned_group = [g for g in group if g]
            datastring = "\n".join(map(json.dumps, cleaned_group)) + "\n"
            self.est._bulk.post(data=datastring,format=(None, 'json'))
            self.est.post('{0}/_refresh'.format(self.es_index))
            c += int(len(cleaned_group)/2)
            self.logger.info("{0} record sent".format(c))



    def es_setup(self):
        """

        :param version:
        :return:
        """
        # create politici_version index, if non-existing
        try:
            self.est.head(self.es_index)
        except HTTPError as e:
            if e.response.status_code == 401:
                self.logger.error(e)
                quit()
            elif e.response.status_code == 404:
                self.est.put(self.es_index)
                self.logger.info("Index created")
            else:
                self.logger.error(e)
                quit()
        except Exception as e:
            self.logger.error(e)
            quit()

        # remove all docs of type given, if present
        if self.es_delete:
            try:
                self.est.head(self.es_index)
                self.est.delete("{0}/{1}".format(self.es_index, self.es_doctype))
            except HTTPError as e:
                err = e.response
                if err.status_code == 404:
                    pass
                else:
                    quit()


        # generate alias, pointing to versioned index
        # self.est._aliases.post(data={
        #         "actions": [
        #         { "add": {
        #             "alias": "{0}".format(self.es_index),
        #             "index": "{0}_{1}".format(self.es_index, self.es_version)
        #         }}
        #     ]
        # })



