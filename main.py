from RESTApi import create_app

app = create_app()

if __name__ == "__main__":
    from uvicorn import run

    PORT = 8000
    run("main:app", host="0.0.0.0", reload=True, port=PORT)
