#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import csv
from datetime import datetime
import io
import json
import logging
import logging.config
import re
import requests
import zipfile
from slugify import slugify
from utils import DictReaderInsensitive, DictInsensitive
__author__ = 'guglielmo'

# pre-compile some regular expressions used within the loops
prov_com_re = re.compile(r'(?P<city>[\w \']+)\((?P<prov>[\w \']+)\)')
state_re = re.compile(r'(?P<state>[\w \']+)')


logging.config.dictConfig(json.load(open('logging.conf.json')))

class DataScraperException(Exception):
    pass

class DataScraper(object):
    """
    Base DataScraper class from which each class extends.
    Default logger and arguments parser defined
    """

    def __init__(self, **kwargs):
        self.logger = logging.getLogger('import_script')

    def scrape(self, **kwargs):
        """
        Need to be implemented by extending class.

        :param kwargs:
        :return:
        """
        raise Exception("not implemented")

    def get_iterator(self):
        raise Exception("not implemented")

class MinintCSVDictReader(DictReaderInsensitive):

    def __init__(self, f, institution=None, **kwargs):
        DictReaderInsensitive.__init__(self, f, **kwargs)
        self.institution = institution

    def get_unique_id(self, row):
        istituzione = self.institution
        key = "denominazione_{0}".format(self.institution)
        localita = row[key]

        start_date = datetime.strptime(row['data_entrata_in_carica'], "%d/%m/%Y").strftime("%Y%m%d")

        unique_id = slugify(
            "-".join([
                row['politico_id'],
                row['descrizione_carica'],
                istituzione,
                localita,
                start_date,
                'in carica'
            ])
        )

        return unique_id


    def __next__(self):
        row = DictReaderInsensitive.__next__(self)
        carica = row['descrizione_carica'].lower()
        if 'commissario' in carica or 'commissione' in carica:
            row['politico_id'] = slugify("{cognome} {nome}").format(**row)
        else:
            try:
                row['politico_id'] = slugify("{cognome} {nome} {data_nascita} {luogo_nascita} {sesso}".format(**row))
            except DataScraperException as e:
                return  (e, row)

        # replace LISTA CIVICA | NOME with LISTA CIVICA: NOME
        # then create a list out of the pipe separated string
        row['desc_partito'] = [s.strip() for s in row['desc_partito'].replace('LISTA CIVICA | ', 'LISTA CIVICA: ').split('|')]

        row['istituzione'] = self.institution
        row['unique_id'] = self.get_unique_id(row)

        return row

class MinintStoriciCSVDictReader(MinintCSVDictReader):

    def get_unique_id(self, row):
        istituzione = self.institution
        localita = 'nd'
        key = "desc_{0}".format(self.institution)
        localita = row[key]

        start_date = datetime.strptime(row['data_nomina'], "%d/%m/%Y").strftime("%Y%m%d")
        if row['data_cessazione']:
            end_date = datetime.strptime(row['data_cessazione'], "%d/%m/%Y").strftime("%Y%m%d")
        else:
            end_date = 'in carica'

        unique_id = slugify(
            "-".join([
                row['politico_id'],
                row['descrizione_carica'],
                istituzione,
                localita,
                start_date,
                end_date
            ])
        )

        return unique_id


    def __next__(self):
        row = DictReaderInsensitive.__next__(self)
        carica = row['descrizione_carica'].lower()
        if 'commissario' in carica or 'commissione' in carica:
            row['politico_id'] = slugify("{cognome} {nome}").format(**row)
        else:
            try:
                row['politico_id'] = slugify("{cognome} {nome} {data_nascita} {desc_sede_nascita} {sesso}".format(**row))
            except DataScraperException as e:
                return  (e, row)

        # replace LISTA CIVICA | NOME with LISTA CIVICA: NOME
        # then create a list out of the pipe separated string
        row['desc_partito'] = [s.strip() for s in row['desc_partito'].replace('LISTA CIVICA | ', 'LISTA CIVICA: ').split('|')]

        row['istituzione'] = self.institution
        row['unique_id'] = self.get_unique_id(row)

        return row

class MinintDataScraper(DataScraper):

    def __init__(self, url, log_level):
        DataScraper.__init__(self)
        self.url = url
        self.log_level = log_level


    def scrape(self):
        self.logger.setLevel(getattr(logging, self.log_level.upper(), logging.WARNING))

        self.logger.info("Start")
        self.logger.debug("minint_url: {0}".format(self.url))

        # retrieve bulk_data from minint_url
        return self.get_iterator()


    def get_iterator(self):
        """
        Read the zip file from the site, extract its content and return a csv.DictReader to it
        :return: csv.DictReader
        """
        # request zip file from url
        r = requests.get(self.url)

        # read content from url and create a ZipFile out of it's content,
        archive = zipfile.ZipFile(io.BytesIO(r.content), 'r')

        # extract filename
        file = archive.infolist()[0].filename

        # uncompress zipped file and remove the first 2 lines (they are notes)
        archive_txt = "\n".join(archive.read(file).decode('latin1').split("\r\n")[2:])

        # create an extended csv.DictReader
        # injecting codice fiscale and unique_id computation
        dummy, filename = file.split("/")
        institution = {
            'ammreg.txt': 'regione',
            'ammprov.txt': 'provincia',
            'ammcom.txt': 'comune'
        }[filename]
        archive_reader = MinintCSVDictReader(io.StringIO(archive_txt), delimiter=";", institution=institution)

        return archive_reader

class MinintStoriciDataScraper(MinintDataScraper):

    def get_iterator(self):
        """
        Read the zip file from the site, extract its content and return a csv.DictReader to it
        :return: csv.DictReader
        """
        # request zip file from url
        r = requests.get(self.url)

        # read content from url and create a ZipFile out of it's content,
        archive = zipfile.ZipFile(io.BytesIO(r.content), 'r')

        # extract filename
        file = archive.infolist()[0].filename

        # uncompress zipped file
        archive_txt = "\n".join(archive.read(file).decode('latin1').split("\r\n"))

        # create an extended csv.DictReader
        # injecting codice fiscale and unique_id computation
        institution_context = file[:-12]
        institution = {
            'regioni':  'regione',
            'province': 'provincia',
            'comuni':   'comune'
        }[institution_context]
        archive_reader = MinintStoriciCSVDictReader(
            io.StringIO(archive_txt), delimiter=";", institution=institution
        )

        return archive_reader
