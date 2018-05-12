# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models

from mongoengine import Document, EmbeddedDocument, fields
from datetime import datetime
from chat_application_restapis.settings import THE_MONGO_CLIENT

def get_mongo_db(db_name):
    return THE_MONGO_CLIENT[db_name]