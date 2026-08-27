from fastapi import FastAPI

app = FastAPI(
    title="Help Desk API",
    description="API para gerenciamento de chamados de suporte técnico.",
    version="0.1.0",
)


@app.get("/")
def read_root():
    return {"message": "Help Desk API is running"}
