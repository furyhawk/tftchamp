#!/usr/bin/env python3.10
# -*- coding: UTF-8 -*-

try:
    from pymongo import MongoClient
except ImportError:
    raise ImportError('PyMongo is not installed in your machine.')


class MongoDB(object):

    def __init__(self, host='localhost', port=27017,
                 database_name=None, collection_name=None,
                 drop_n_create=False):
        try:
            # creating connection while object creation
            self._connection = MongoClient(
                host=host, port=port, maxPoolSize=200)
        except Exception as error:
            raise Exception(error)

        # drop database and create new one (optional)
        if drop_n_create:
            self.drop_db(database_name)

        self._database = None
        self._collection = None
        # assigning database name while object creation
        if database_name:
            self._database = self._connection[database_name]
        # assigning collection name while object creation
        if collection_name:
            self._collection = self._database[collection_name]

    @staticmethod
    def check_state(obj):
        if not obj:
            return False
        else:
            return True

    def check_db(self):
        # validate the database name
        if not self.check_state(self._database):
            raise ValueError('Database is empty/not created.')

    def check_collection(self):
        # validate the collection name
        if not self.check_state(self._collection):
            raise ValueError('Collection is empty/not created.')

    def get_overall_details(self):
        # get overall connection information
        client = self._connection
        return dict((db, [collection for collection in client[db].collection_names(
        )]) for db in client.database_names())

    def get_current_status(self):
        # get current connection information
        return {
            'connection': self._connection,
            'database':   self._database,
            'collection': self._collection
        }

    def create_db(self, database_name=None):
        # create the database name
        self._database = self._connection[database_name]

    def create_collection(self, collection_name=None):
        # create the collection name
        self.check_db()
        self._collection = self._database[collection_name]

    def get_database_names(self):
        # get the database name you are currently connected too
        return self._connection.database_names()

    def get_collection_names(self):
        # get the collection name you are currently connected too
        self.check_collection()
        return self._database.collection_names(include_system_collections=False)

    def drop_db(self, database_name):
        # drop/delete whole database
        self._database = None
        self._collection = None
        return self._connection.drop_database(str(database_name))

    def drop_collection(self):
        # drop/delete a collection
        self._collection.drop()
        self._collection = None

    def insert(self, post):
        # add/append/new single record
        self.check_collection()
        post_id = self._collection.insert_one(post).inserted_id
        return post_id

    def insert_many(self, posts):
        # add/append/new multiple records
        self.check_collection()
        result = self._collection.insert_many(posts)
        return result.inserted_ids

    def find_one(self, *args, count=False):
        # search/find many matching records returns iterator object
        self.check_collection()
        if not count:
            return self._collection.find_one(*args)
        # return only count
        return self._collection.find(*args).count()

    def find(self, *args, count=False):
        # search/find many matching records returns iterator object
        self.check_collection()
        if not count:
            return self._collection.find(*args)
        # return only count
        return self._collection.find(*args).count()

    def count(self):
        # get the records count in collection
        self.check_collection()
        return self._collection.count()

    def remove(self, *args):
        # remove/delete records
        return self._collection.remove(*args)

    def update(self, *args):
        # updating/modifying the records
        return self._collection.update(*args)

    def aggregate(self, *args):
        # grouping the records
        return self._collection.aggregate(*args)
