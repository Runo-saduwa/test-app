from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class WebhookPayload(BaseModel):
    event: str
    data: dict

@app.post("/api/v1/hook")
async def webhook(payload: WebhookPayload):
    print('payload received')  # Convert payload to a dictionary
    return {"message": "Webhook received", "data": payload}
