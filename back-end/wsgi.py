from app import create_app

app = create_app()
app.extensions["chat"].warm_up()
