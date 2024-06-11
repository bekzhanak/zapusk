from fastapi import FastAPI, Request
from utils import *

payments = load_json("payments.json")

app = FastAPI()


@app.get("/hello/")
async def hello(request: Request):
    return {"message": "Hello world"}

@app.post("/webhook/")
async def receive_data(request: Request):
    try:
        body_dict = await request.json()
    except Exception:
        body_dict = await request.body()

    if not body_dict["payment_status"] == "success":
        return

    phone = body_dict["customer_phone"]

    payments[phone] = body_dict["sum"]

    save_json("payments.json", payments)

    return {"message": "Data received!"}

# Run the API (optional, for development purposes)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("service:app", host="127.0.0.1", port=8000)
