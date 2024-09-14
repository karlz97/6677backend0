from fastapi import FastAPI
from app.routes import router
from app.database import init_db
import os
import uvicorn

app = FastAPI()

app.include_router(router)


@app.on_event("startup")
async def startup_event():
    init_db()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
