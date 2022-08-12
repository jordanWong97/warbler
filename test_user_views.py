"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, Message, User

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


class BaseViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        db.session.flush()

        m1 = Message(text="m1-text", user_id=u1.id)
        db.session.add_all([m1])
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id
        self.m1_id = m1.id

        self.client = app.test_client()


    def tearDown(self):
        db.session.rollback()
        # rollback only if commit fails?


    def test_signup_page(self):
        """ tests if sign-up page renders correctly"""

        with self.client as c:

            resp = c.get('/signup')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Join Warbler today', html)


    def test_signup(self):
        """ tests redirect on successful user signup """

        with self.client as c:

            resp = c.post("/signup", follow_redirects = True,
                                    data={"username": "test_user1",
                                        "email": "test@test.com",
                                        "password": "password"})

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>@test_user1', html)


    def test_login_page(self):
        """tests if user login renders"""

        with self.client as c:

            resp = c.get('/login')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Welcome back.', html)


    def test_user_login(self):
        """ tests redirect on successful user login """

        with self.client as c:

            resp = c.post("/login", follow_redirects = True,
                                    data={"username": "u1",
                                        "password": "password"})

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>@u1', html)


    def test_logout(self):
        """ tests if logout redirects correctly back to login page """

        with self.client as c:

            resp = c.post("/login", follow_redirects = True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Welcome back.', html)


    def test_list_users(self):
        """ tests if list of users page is rendered correctly """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id


            resp = c.get('/users')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>@u1', html)
            self.assertIn('<p>@u2', html)


    def test_show_single_user_logged_in(self):
        """ tests if a specific user's profile renders if user is logged in """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id


            resp = c.get(f'/users/{self.u1_id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<ul class="list-group" id="messages">', html)


    def test_show_single_user_if_not_logged_in(self):
        """ tests that a specific user's profile does not render if user is
        logged out"""

        with self.client as c:

            resp = c.get(f'/users/{self.u1_id}', follow_redirects = True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="home-hero">', html)


    def test_show_user_following_if_logged_in(self):
        """ tests if a user's following page renders if user is logged in """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id


            resp = c.get(f'/users/{self.u1_id}/following')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="col-sm-9">', html)


    def test_show_user_following_if_logged_out(self):
        """ tests if a user's following page renders if user is logged out """

        with self.client as c:

            resp = c.get(f'/users/{self.u1_id}/following',
                                follow_redirects = True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="home-hero">', html)


    def test_show_user_followers_if_logged_out(self):
        """ tests if a user's followers page renders if user is logged out """

        with self.client as c:

            resp = c.get(f'/users/{self.u1_id}/followers',
                                follow_redirects = True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="home-hero">', html)


    def test_user_follow(self):
        """ tests redirect on successful user follow """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(f"/users/follow/{self.u2_id}", follow_redirects = True)

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="col-sm-9">', html)
            self.assertIn('<p>@u2', html)


    def test_user_stop_follow(self):
        """ tests redirect on successful user follow removal """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            c.post(f"/users/follow/{self.u2_id}")
            resp = c.post(f"/users/stop-following/{self.u2_id}",
                                        follow_redirects = True)

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="col-sm-9">', html)
            self.assertNotIn('<p>@u2', html)


    def test_render_profile(self):
        """ renders profile for specified user """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id


            resp = c.get(f'/users/profile')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h2 class="join-message">Edit Your Profile.</h2>', html)


    def test_edit_profile(self):
        """ checks successful user profile update """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(f"/users/profile", follow_redirects = True,
                                            data = {"username": "hello",
                                                    "email": "test@test2.com",
                                                    "image_url":"",
                                                    "header_image_url":"",
                                                    "bio": "",
                                                    "password": "password"})
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('hello', html)
            self.assertIn('test@test2.com', html)


    def test_delete_user(self):
        """checks if user is deleted successfully and redirects to correct page """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(f"/users/delete", follow_redirects = True)

            # is this a good check?
            user = User.query.get(self.u1_id)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="row justify-content-md-center">', html)
            self.assertIsNone(user)


    def test_show_liked_message(self):
        """ renders template for user's liked message page """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f'/users/{self.u1_id}/likedmessages')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<ul class="list-group', html)