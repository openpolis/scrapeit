import json
import logging
import logging.config

__author__ = 'guglielmo'
from scrapers import MinintStoriciDataScraper
from storers import ESDataStorer

year_from = 2005
year_to = 2007
batch_size = 1000
es_url = 'http://blackbox:9200'

logging.config.dictConfig(json.load(open('logging.conf.json')))
logger = logging.getLogger('import_script')
logger.setLevel(logging.INFO)

dst = ESDataStorer(
    es_url=es_url,
    es_index='amministratori_v1',
    es_doctype='incarico_storico',
    es_batchsize=batch_size,
    log_level='info'
)

for y in range(year_from, year_to):
    for t in ('regioni', 'province', 'comuni'):
        logger.info('++++++ YEAR: {0}, TYPE: {1} ++++++++'.format(y, t))
        dsc = MinintStoriciDataScraper(
            url='http://amministratori.interno.it/amministratori/storico/{0}3112{1}.zip'.format(t, y),
            log_level='info'
        )
        dst.store(dsc.scrape())