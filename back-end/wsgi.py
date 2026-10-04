import os

from app import create_app

app = create_app()
if os.getenv("LIFESIZE_WARM_UP", "1") == "1":
    app.extensions["chat"].warm_up()
