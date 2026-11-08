from fastapi import FastAPI

from app.api import invoices

app = FastAPI(title="billing")
app.include_router(invoices.router)
