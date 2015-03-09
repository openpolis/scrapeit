import csv

__author__ = 'guglielmo'

class DictInsensitive(dict):
    # This class overrides the __getitem__ method to automatically strip() and lower() the input key

    def __getitem__(self, key):
        return dict.__getitem__(self, key.strip().lower())

class DictReaderInsensitive(csv.DictReader):
    # This class overrides the csv.fieldnames property.
    # All fieldnames are without white space and in lower case

    @property
    def fieldnames(self):
        return [field.strip().lower() for field in csv.DictReader.fieldnames.fget(self)]

    def next(self):
        return DictInsensitive(csv.DictReader.next(self))

