from fastapi import FastAPI, Request


app = FastAPI()


@app.post("/")
async def receive_data(request: Request):
    # Get headers
    headers = dict(request.headers)

    # Access body as bytes (for raw data)
    body_bytes = await request.body()

    # Optionally, decode body as string (if applicable)
    try:
        body_str = body_bytes.decode("utf-8")
    except UnicodeDecodeError:
        body_str = "Non-UTF-8 encoded body"

    # Get other request information
    method = request.method
    base_url = request.base_url
    client_ip = request.client.host

    # Print information
    print(f"--- New Request ---")
    print(f"Method: {method}")
    print(f"Base URL: {base_url}")
    print(f"Headers: {headers}")
    print(f"Body (bytes): {body_bytes}")
    print(f"Body (string, if decodable): {body_str}")
    print(f"Client IP: {client_ip}")
    print("------------------")

    return {"message": "Data received!"}

# Run the API (optional, for development purposes)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("service:app", host="0.0.0.0", port=8000)
