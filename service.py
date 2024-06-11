from fastapi import FastAPI, Request
from utils import *

payments = load_json("payments.json")

app = FastAPI()


@app.get("/hello/")
async def hello(request: Request):
    return {"message": "Hello world"}

@app.post("/webhook/")
async def receive_data(request: Request):
    body_dict = await request.body()
    body_dict = body_dict.decode("utf-8")
    arr = body_dict.split("&")

    for i in arr:
        data = i.split("=")
        if data[0] == "customer_phone":
            phone = data[1]
            print(phone.encode("utf-8"))
        elif data[0] == "sum":
            sum = data[1]
        elif data[0] == "payment_status":
            status = data[1]

    print(type(body_dict))
    print(body_dict)

    if not status == "success":
        return

    payments[phone] = sum

    save_json("payments.json", payments)

    return {"message": "Data received!"}

# Run the API (optional, for development purposes)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("service:app", host="127.0.0.1", port=8000)
