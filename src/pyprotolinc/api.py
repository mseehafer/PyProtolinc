from fastapi import FastAPI

from pyprotolinc.riskfactors.risk_factors import get_risk_factor_names

app = FastAPI()


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World!"}


@app.get("/risk_factors")
async def risk_factors() -> list[str]:
    return get_risk_factor_names()
