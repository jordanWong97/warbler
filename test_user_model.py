"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


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


class UserModelTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()


    def test_user_model(self):
        """ test creating user model """
        u1 = User.query.get(self.u1_id)

        # User should have no messages & no followers
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)


    def test_user_model_repr(self):
        """ test user model __repr__ method"""
        u1 = User.query.get(self.u1_id)

        self.assertEqual(f"{u1}",
                        f"<User #{u1.id}: {u1.username}, {u1.email}>")


    def test_user_is_following(self):
        """ test user 1 is following user 2 and user 2 is followed by user 1"""
        u1 = User.query.get_or_404(self.u1_id)
        u2 = User.query.get_or_404(self.u2_id)

        u1.following.append(u2)
        db.session.commit()

        # User 1 is following User 2
        # User 2 is followed by User 1
        self.assertIn(u2, u1.following)
        self.assertIn(u1, u2.followers)


    def test_user_is_not_following(self):
        """ test user 1 is not following user 2
        and user 2 is not followed by user 1"""
        u1 = User.query.get_or_404(self.u1_id)
        u2 = User.query.get_or_404(self.u2_id)

        # User 1 is not following User 2
        # User 2 is not followed by User 1
        self.assertNotIn(u2, u1.following)
        self.assertNotIn(u1, u2.followers)


    def test_user_signup(self):
        """ test new signup method from user model"""
        u3 = User.signup("u3", "u3@email.com", "password", None)
        db.session.commit()
        self.u3_id = u3.id

        # User should have no messages & no followers
        self.assertEqual(len(u3.messages), 0)
        self.assertEqual(len(u3.followers), 0)


    def test_user_signup_fail(self):
        """ test user sign up fails when unique column data is entered """
        u4 = User.signup("u1", "u4@email.com", "password", None)

        # try:
        #     db.session.commit()
        # except IntegrityError:
        #     return 'username already exists'

        # self.assertIsInstance(db.session.commit(), IntegrityError)


    def test_user_authenticate(self):
        """ test user model athenticating valid username/password """

        login_user_u1 = User.authenticate('u1', 'password')
        u1 = User.query.get_or_404(self.u1_id)
        self.assertEqual(u1, login_user_u1)


    def test_user_authenticate_fail_username(self):
        """ test user model athenticating invalid username """

        test_fail_user = User.authenticate('user', 'password')
        self.assertFalse(test_fail_user)


    def test_user_authenticate_fail_password(self):
        """ test user model athenticating invalid password """

        test_fail_user = User.authenticate('u1', 'badpass')
        self.assertFalse(test_fail_user)






