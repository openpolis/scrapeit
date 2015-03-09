#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import argparse
import sys
from scrapers import MinintDataScraper, MinintStoriciDataScraper
from storers import ESDataStorer

__author__ = 'guglielmo'

class ScrapeCommand(object):

    def __init__(self):
        parser = argparse.ArgumentParser(
            description='Scrape data from given sources',
            usage='''scrape <source_type> [<args>]

The currently available source types are:
   minint           Active administratorss
   minint_storici   Historical data
''')
        parser.add_argument('source_type', help='Source type')
        # parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.source_type):
            print('Unrecognized source type')
            parser.print_help()
            exit(1)
        # use dispatch pattern to invoke method with same name
        getattr(self, args.source_type)()

    def parseargs(self, argparser):
        argparser.add_argument('url', metavar='URL', type=str,
           help='The path to the zipped file to scrape.',
        )
        argparser.add_argument('--es_url', metavar='ES_URL', type=str,
           help='''
           The path to ElasticSearch instance, with password.
           URL format: http://user:password@host:port/index/doctype
           ''',
           default="http://localhost:9200/politici/incarico"
        )
        argparser.add_argument('--es_delete', action='store_true',
           help='Deletes all documents of type incarico, before insertion.',
           default=False
        )
        argparser.add_argument('--es_batchsize', type=int,
           help='Batch size for bulk uploading. 0 means all data are sent together.',
           default=0
        )
        argparser.add_argument('--log_level', metavar='LOG_LEVEL', type=str,
           help='Console log level: warning, info, debug.',
           default='info',
        )
        return argparser.parse_args(sys.argv[2:])

    def minint(self):
        parser = argparse.ArgumentParser(
            description='Scrape data from the Anagrafe section of http://amministratori.interno.it/')
        args = self.parseargs(parser)
        print('Running scrape2es minint, url=%s' % args.url)
        dsc = MinintDataScraper(args.url, args.log_level)
        dst = ESDataStorer(
            es_index=args.es_url.split("/")[-2],
            es_doctype=args.es_url.split("/")[-1],
            es_url="/".join(args.es_url.split("/")[:-2]),
            es_delete=args.es_delete,
            es_batchsize=args.es_batchsize,
            log_level=args.log_level
        )

        # What's scraped is stored.
        dst.store(dsc.scrape())



    def minint_storici(self):
        parser = argparse.ArgumentParser(
            description='Scrape data from the Dati Storici section of http://amministratori.interno.it/')
        args = self.parseargs(parser)
        print('Running scrape2es minint_storici, url=%s' % args.url)

        dsc = MinintStoriciDataScraper(args.url, args.log_level)
        dst = ESDataStorer(
            es_index=args.es_url.split("/")[-2],
            es_doctype=args.es_url.split("/")[-1],
            es_url="/".join(args.es_url.split("/")[:-2]),
            es_delete=args.es_delete,
            es_batchsize=args.es_batchsize,
            log_level=args.log_level
        )

        # What's scraped is stored.
        dst.store(dsc.scrape())


if __name__ == '__main__':
    ScrapeCommand()
