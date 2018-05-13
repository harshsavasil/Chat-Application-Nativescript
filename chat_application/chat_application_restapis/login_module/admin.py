# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from kombu.transport.django import models as kombu_models
site.register(kombu_models.Message)