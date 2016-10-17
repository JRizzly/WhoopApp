import unittest

from . import *

from app.users.models import User


class UserModelTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(class_):
        db.drop_all()
        db.create_all()

        session = db.session
        for user in (
            User(username="admin-user", role="admin",
                 password="admin", email="admin@example.com"),
                User(username="user", role="user", password="user", email="user@example.com")):
            session.add(user)
        session.commit()

    @classmethod
    def tearDownClass(class_):
        db.drop_all()

    def setUp(self):
        pass

    def tearDown(self):
        db.session.commit()

    def test_users_loaded(self):
        assert User.query.count() == 2
