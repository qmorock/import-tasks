# Copyright (C) 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""OAuth 2.0 utilities for Django.

Utilities for using OAuth 2.0 in conjunction with
the Django datastore.
"""

__author__ = 'jcgregorio@google.com (Joe Gregorio)'

import apiclient.oauth2client
import base64
import pickle

from django.db import models
from apiclient.oauth2client.client import Storage as BaseStorage

class CredentialsField(models.Field):

  __metaclass__ = models.SubfieldBase

  def db_type(self, connection=None):
    return 'VARCHAR'

  def to_python(self, value):
    if not value:
      return None
    if isinstance(value, apiclient.oauth2client.client.Credentials):
      return value
    return pickle.loads(base64.b64decode(value))

  def get_db_prep_value(self, value):
    return base64.b64encode(pickle.dumps(value))


class FlowField(models.Field):

  __metaclass__ = models.SubfieldBase

  def db_type(self, connection=None):
    return 'VARCHAR'

  def to_python(self, value):
    if value is None:
      return None
    if isinstance(value, apiclient.oauth2client.client.Flow):
      return value
    return pickle.loads(base64.b64decode(value))

  def get_db_prep_value(self, value):
    return base64.b64encode(pickle.dumps(value))


class Storage(BaseStorage):
  """Store and retrieve a single credential to and from
  the datastore.

  This Storage helper presumes the Credentials
  have been stored as a CredenialsField
  on a db model class.
  """

  def __init__(self, model_class, key_name, key_value, property_name):
    """Constructor for Storage.

    Args:
      model: db.Model, model class
      key_name: string, key name for the entity that has the credentials
      key_value: string, key value for the entity that has the credentials
      property_name: string, name of the property that is an CredentialsProperty
    """
    self.model_class = model_class
    self.key_name = key_name
    self.key_value = key_value
    self.property_name = property_name

  def get(self):
    """Retrieve Credential from datastore.

    Returns:
      apiclient.oauth2client.Credentials
    """
    credential = None

    query = {self.key_name: self.key_value}
    entities = self.model_class.objects.filter(**query)
    if len(entities) > 0:
      credential = getattr(entities[0], self.property_name)
      if credential and hasattr(credential, 'set_store'):
        credential.set_store(self.put)
    return credential

  def put(self, credentials):
    """Write a Credentials to the datastore.

    Args:
      credentials: Credentials, the credentials to store.
    """
    args = {self.key_name: self.key_value}
    entity = self.model_class(**args)
    setattr(entity, self.property_name, credentials)
    entity.save()
