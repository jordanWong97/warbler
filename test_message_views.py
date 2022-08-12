"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import LikedMessage, db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageBaseViewTestCase(TestCase):
    def setUp(self):
        Message.query.delete()
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        db.session.flush()

        m1 = Message(text="m1-text", user_id=u1.id)
        m2 = Message(text="m2-text", user_id=u2.id)
        db.session.add_all([m1, m2])
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id

        self.m1_id = m1.id
        self.m2_id = m2.id

        self.client = app.test_client()


class MessageAddViewTestCase(MessageBaseViewTestCase):
    def test_add_message(self):
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            # Now, that session setting is saved, so we can have
            # the rest of ours test
            resp = c.post("/messages/new",
                            data={"text": "Hello"},
                            follow_redirects = True)
            html = resp.get_data(as_text=True)

            Message.query.filter_by(text="Hello").one()

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>Hello</p>', html)


    def test_render_add_message(self):
        """ tests if we render the create message form"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
            resp = c.get("/messages/new")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<form method="POST">', html)
            self.assertIn('<button class="btn', html)


    def test_add_message_if_not_logged_in(self):
        """ test redirecting for adding message when not logged in """

        with self.client as c:

            resp = c.post("/messages/new",
                            data={"text": "Hello"},
                            follow_redirects = True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<a href="/signup"', html)
            self.assertIn('home anon page test', html)


    # TODO: is it possible to access adding a message as another user?
    # def test_add_message_as_another_user(self):
    #     """ test prohibiting from adding message as another user """

    #     with self.client as c:
    #         with c.session_transaction() as sess:
    #             sess[CURR_USER_KEY] = self.u2_id

    #         resp = c.post("/messages/new",
    #                         data={"text": "Hello"},
    #                         follow_redirects = True)
    #         html = resp.get_data(as_text=True)

    #         self.assertEqual(resp.status_code, 200)
    #         self.assertIn('<p>Hello</p>', html)


    def test_delete_message(self):
        """ test deleting a message when logged in """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            Message.query.filter_by(text="m1-text").one()

            resp = c.post(f"/messages/{self.m1_id}/delete", follow_redirects = True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn('m1-text', html)


    def test_delete_message_if_not_logged_in(self):
        """ test redirecting for deleting message when not logged in """

        with self.client as c:

            resp = c.post(f"/messages/{self.m1_id}/delete", follow_redirects = True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<a href="/signup"', html)
            self.assertIn('home anon page test', html)


    def test_delete_message_as_another_user(self):
        """ test prohibiting from deleting message as another user """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id


            resp = c.post(f"/messages/{self.m2_id}/delete", follow_redirects = True)
            html = resp.get_data(as_text=True)

            Message.query.filter_by(text="m2-text").one()

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>@u1', html)


    def test_show_message(self):
        """ tests if specific message page renders """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

        resp = c.get(f'/messages/{self.m1_id}')
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('<div class="message-area">', html)
        self.assertIn('m1-text</p>', html)


    def test_like_message(self):
        """ tests if a liked message is added to user's liked messages list and
        route redirects back to user profile"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

        resp = c.post(f"/messages/{self.m2_id}/like", follow_redirects = True)
        html = resp.get_data(as_text=True)

        LikedMessage.query.filter_by(user_id = self.u1_id,
                                    message_id = self.m2_id).one()

        self.assertEqual(resp.status_code, 200)
        self.assertIn('<div class="col-sm-6">', html)
        self.assertIn('show user profile test', html)


    def test_unlike_message(self):
        """ tests if a liked message is removed from user's liked messages list
        and route redirects back to user profile"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

        c.post(f"/messages/{self.m2_id}/like")
        resp = c.post(f"/messages/{self.m2_id}/unlike", follow_redirects = True)
        html = resp.get_data(as_text=True)

        unliked = LikedMessage.query.filter_by(user_id = self.u1_id,
                                    message_id = self.m2_id).all()

        self.assertEqual(resp.status_code, 200)
        self.assertIn('<div class="col-sm-6">', html)
        self.assertIn('show user profile test', html)
        self.assertFalse(unliked)















