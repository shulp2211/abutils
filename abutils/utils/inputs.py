#!/usr/bin/env python
# filename: inputs.py


#
# Copyright (c) 2018 Bryan Briney
# License: The MIT license (http://opensource.org/licenses/MIT)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software
# and associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
# BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#



from abc import ABCMeta, abstractmethod
import json
import os

from Bio import SeqIO

from . import mongodb
from .pipeline import list_files
from ..core.sequence import Sequence


if sys.version_info[0] > 2:
    STR_TYPES = [str, ]
else:
    STR_TYPES = [str, unicode]



def read_input(input, data_type,
               collection=None, mongo_ip='localhost', mongo_port=27017, mongo_user=None, mongo_password=None,
               query=None, projection=None, **kwargs):
    '''
    Returns an Input class based on the data information provided.

    Args:

        data_type (str): One of the following: `'fasta'`, `'json'`, or `'mongodb'`.

        input (str): Path to an input file for FASTA or JSON data types, or the database name for MongoDB data.

        collection (str): Name of a MongoDB collection. Required for the MongoDB data type.

        mongo_ip (str): IP address of the MongoDB server. Default is `'localhost'` if not provided.

        mongo_port (int): Port of the MongoDB server. Default is `27017` if not provided.

        query (dict): Query to limit the results returned from a MongoDB database.

        projection (dict): Projection to specify fields to be retuired from a MongoDB database.
    '''



class BaseInput():
    '''
    Base class for parsing inputs (JSON, MongoDB, FASTA files, etc)
    '''

    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @property
    @abstractmethod
    'Returns the data type'
    def data_type(self):
        pass

    @property
    @abstractmethod
    def as_list(self):
        'Returns the input as a list of Sequence objects'
        pass

    @property
    @abstractmethod
    def as_generator(self):
        ' Returns the input as a genarator of Sequence objects'
        pass


class FASTAInput(BaseInput):
    '''
    Representation of FASTA input data.
    '''

    def __init__(self, input_file):
        self.input_file = input_file

    @property
    def data_type(self):
        return 'fasta'

    @property
    def files(self):
        if type(self.input_file) in STR_TYPES:
            if os.path.isdir(self.input_file):
                return list_files(self.input_file, 'json')
            else:
                return [self.input_file, ]
        else:
            return self.input_file

    @lazy_property
    def as_list(self):
        sequences = []
        for input_file in self.files:
            with open(input_file, 'r') as f:
                for seq in SeqIO.parse(f, 'fasta'):
                    sequences.append(Sequence(str(seq.seq), id=seq.id))
        return sequences

    @property
    def as_generator(self):
        for input_file in self.files:
            with open(input_file, 'r') as f:
                for seq in SeqIO.parse(f, 'fasta'):
                    yield Sequence(str(seq.seq), id=seq.id)


class JSONInput(BaseInput):
    '''
    Representation of JSON input data
    '''

    def __init__(self, input_file):
        self.input_file = input_file

    @property
    def data_type(self):
        return 'json'

    @property
    def files(self):
        if type(self.input_file) in STR_TYPES:
            if os.path.isdir(self.input_file):
                return list_files(self.input_file, 'json')
            else:
                return [self.input_file, ]
        else:
            return self.input_file

    @lazy_property
    def as_list(self):
        sequences = []
        for input_file in self.files:
            with open(input_file, 'r') as f:
                for line in f:
                    j = json.loads(line.strip().lstrip(']').rstrip(']').rstrip(','))
                    sequences.append(Sequence(j))
        return sequences

    @property
    def as_generator(self):
        for input_file in self.files:
            with open(input_file, 'r') as f:
                for line in f:
                    j = json.loads(line.strip().lstrip(']').rstrip(']').rstrip(','))
                    yield Sequence(j)


class MongoDBInput(BaseInput):
    '''
    Representation of MongoDB input data
    '''


    def __init__(self, database, collection, ip, port, user, password, query, projection):
        self.db_name = database
        self.raw_collections = collection
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        self.query = query
        self.projection = projection

    @property
    def data_type(self):
        return 'mongodb'

    @property
    def db(self):
        return mongodb.get_db(self.db_name, ip=self.ip, port=self.port,
                              user=self.user, password=self.password)

    @property
    def collections(self):
        if type(self.raw_collections) in STR_TYPES:
            return [self.raw_collections, ]
        elif self.raw_collections is None:
            return mongodb.get_collections(self.db)
        else:
            return self.raw_collections

    @lazy_property
    def as_list(self):
        sequences = []
        for collection in self.collections:
            res = self.db[collection].find(self.query, self.projection)
            for r in res:
                sequences.append(Sequence(r))
        return sequences

    @property
    def as_generator(self):
        for collection in self.collections:
            res = self.db[collection].find(self.query, self.projection)
            for r in res:
                yield Sequence(r)

        
    def _process_collections(self, collection):
        if type(collection) in STR_TYPES:
            return [collection, ]
        elif collection is None:
            return mongodb.get_collections(self.db)
        else:
            return collection





