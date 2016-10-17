from app import create_app

app = create_app(mode="test")
client = app.test_client()
db = app.db

