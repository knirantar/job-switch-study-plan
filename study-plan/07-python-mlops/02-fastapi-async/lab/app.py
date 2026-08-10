from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Annotated, AsyncIterator

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, field_validator


@dataclass
class Runtime:
    scorer: "Scorer"
    slots: asyncio.Semaphore


class Scorer:
    async def score(self, amount: Decimal) -> Decimal:
        await asyncio.sleep(0)
        return min(Decimal("0.99"), amount / Decimal("10000"))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.runtime = Runtime(scorer=Scorer(), slots=asyncio.Semaphore(4))
    yield
    del app.state.runtime


app = FastAPI(title="Claim Risk API", version="1.0.0", lifespan=lifespan)


class ScoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    claim_id: str = Field(pattern=r"^CLM-[0-9]{1,10}$")
    amount: Decimal = Field(ge=Decimal("0"), le=Decimal("10000000"), max_digits=10, decimal_places=2)

    @field_validator("amount", mode="before")
    @classmethod
    def parse_decimal_string(cls, value: object) -> Decimal:
        if not isinstance(value, str):
            raise ValueError("amount must be an exact decimal string")
        try:
            parsed = Decimal(value)
        except InvalidOperation as error:
            raise ValueError("amount must be a decimal string") from error
        if not parsed.is_finite():
            raise ValueError("amount must be finite")
        return parsed

    @field_validator("amount")
    @classmethod
    def finite_amount(cls, value: Decimal) -> Decimal:
        if not value.is_finite():
            raise ValueError("amount must be finite")
        return value


class ScoreResponse(BaseModel):
    claim_id: str
    risk_score: Decimal
    needs_review: bool


async def require_api_key(x_api_key: Annotated[str | None, Header()] = None) -> str:
    if x_api_key != "lab-key-2026":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    return "lab-client"


def runtime(request: Request) -> Runtime:
    return request.app.state.runtime


@app.get("/livez", include_in_schema=False)
async def live() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/readyz", include_in_schema=False)
async def ready(request: Request) -> dict[str, str]:
    if not hasattr(request.app.state, "runtime"):
        raise HTTPException(status_code=503, detail="not ready")
    return {"status": "ready"}


@app.post("/v1/scores", response_model=ScoreResponse, status_code=200)
async def score_claim(
    body: ScoreRequest,
    _: Annotated[str, Depends(require_api_key)],
    resources: Annotated[Runtime, Depends(runtime)],
) -> ScoreResponse:
    try:
        async with asyncio.timeout(0.250):
            async with resources.slots:
                score = await resources.scorer.score(body.amount)
    except TimeoutError as error:
        raise HTTPException(status_code=504, detail="scoring deadline exceeded") from error
    return ScoreResponse(claim_id=body.claim_id, risk_score=score, needs_review=score >= Decimal("0.80"))
