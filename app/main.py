from fastapi import FastAPI, HTTPException

app = FastAPI(title="Func")

def fibonacci(n: int):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

@app.get("/fibonacci/{index}")

def get_fibonacci(index: int):
    if index < 0:
        raise HTTPException(status_code=400, detail="ind must be >= 0")
    return {"index": index, "value": fibonacci(index)}


