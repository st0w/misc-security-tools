# ---*< bitly_grinder/models.py >*--------------------------------------------
# Copyright (C) 2011 st0w
# 
# This module is part of bit.ly grinder and is released under the MIT License.
# Please see the LICENSE file for details.

"""Data model definitions

Created on Oct 22, 2011

"""
# ---*< Standard imports >*---------------------------------------------------

# ---*< Third-party imports >*------------------------------------------------
from dictshield.document import Document
from dictshield.fields import DateTimeField, IntField, ListField, StringField

# ---*< Local imports >*------------------------------------------------------

# ---*< Initialization >*-----------------------------------------------------

# ---*< Code >*---------------------------------------------------------------
class BitlyUrl(Document):
    """Data related to bit.ly resolution"""
    _public_fields = ('base_url', 'resolved_url', 'status', 'path')

    base_url = StringField(required=True)
    resolved_url = StringField(required=True)
    status = IntField()
    path = ListField(StringField())


__all__ = (BitlyUrl)
