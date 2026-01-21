from fastapi import FastAPI

app = FastAPI(
    title="Array Generator and Sorting Benchmark API",
    description="API for generating arrays and benchmarking sorting algorithms.",
)

@app.get("/")
async def root():
    return {"message": "Array Generator and Sorting Benchmark API is running..."}


