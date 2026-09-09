from fastapi import FastAPI
from transitiq_v2.api.exception_routes import router as issue_router
from transitiq_v2.api.analysis_routes import router as analysis_router

app = FastAPI()

app.include_router(issue_router)
app.include_router(analysis_router)
