from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
async def healthz():
    return JSONResponse({"status": "ok"})

def handler(request):
    return app(request)
