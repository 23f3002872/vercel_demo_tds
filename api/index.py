from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
import numpy as np
import json
import os
from collections import defaultdict

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       
    allow_methods=["*"],        # allow all HTTP methods
    allow_headers=["*"],        # allow all headers
    expose_headers=["*"],       # expose all headers
    allow_credentials=False    # must be False with "*"
)



# Load telemetry once
json_path = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")
with open(json_path, "r") as f:
    raw_telemetry = json.load(f)

telemetry = defaultdict(list)
for record in raw_telemetry:
    telemetry[record["region"]].append(record)

@app.get("/")
def root():
    return {"message": "Latency API is live"}

@app.post("/api/latency")
async def check_latency(payload: dict):
    regions = payload.get("regions", [])
    threshold = payload.get("threshold_ms", 180)

    result = {}
    for region in regions:
        records = telemetry.get(region, [])
        if not records:
            continue

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]
        breaches = sum(1 for r in records if r["latency_ms"] > threshold)

        result[region] = {
            "avg_latency": round(np.mean(latencies), 2),
            "p95_latency": round(np.percentile(latencies, 95), 2),
            "avg_uptime": round(np.mean(uptimes), 2),
            "breaches": breaches
        }

    return JSONResponse(content=result)
