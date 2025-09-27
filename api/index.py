from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import json
import os

app = FastAPI()

# Enable CORS for all requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],  # Allow all methods for safety
    allow_headers=["*"],
)

# Load telemetry data once at startup (use relative path for Vercel)
json_path = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")
with open(json_path, "r") as f:
    raw_telemetry = json.load(f)

# Group records by region
from collections import defaultdict
telemetry = defaultdict(list)
for record in raw_telemetry:
    telemetry[record["region"]].append(record)

@app.post("/")
async def check_latency(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

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

    return result
