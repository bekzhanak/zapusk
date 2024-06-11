from fastapi import FastAPI, Request
from utils import *

payments = load_json("payments.json")

app = FastAPI()


@app.get("/hello/")
async def hello(request: Request):
    return {"message": "Hello world"}

@app.post("/webhook/")
async def receive_data(request: Request):
    body_dict = await request.json()

    if not body_dict.get("payment_status") == "success":
        return

    phone = body_dict.get("customer_phone")

    payments[phone] = body_dict.get("sum")

    save_json("payments.json", payments)

    return {"message": "Data received!"}

# Run the API (optional, for development purposes)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("service:app", host="127.0.0.1", port=8000)
