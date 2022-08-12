"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy.exc import IntegrityError
# from psycopg2 import errors

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class MessageModelTestCase(TestCase):
    def setUp(self):
        User.query.delete()
        Message.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)

        db.session.commit()

        self.u1_id = u1.id

        m1 = Message(text = "text", user_id = self.u1_id)
        m2 = Message(text = "text2", user_id = self.u1_id)

        db.session.add(*[m1,m2])
        db.session.commit()

        self.m1_id = m1.id
        self.m2_id = m2.id
        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()


    def test_message_model(self):
        """test if message is created successfully"""

        msg1 = Message.query.get(self.m1_id)

        self.assertEqual(msg1.text, 'text')
        self.assertEqual(msg1.user_id, self.u1_id)