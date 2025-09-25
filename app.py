import json
import boto3
from flask import Flask, request, jsonify

# -------- Core --------
def process_log_content(log_content: str, threshold: int):
    error_counts = {}
    total = 0
    for line in (log_content or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("level") == "ERROR":
            svc = rec.get("service") or rec.get("module") or "unknown"
            error_counts[svc] = error_counts.get(svc, 0) + 1
            total += 1
    return {"total": total, "byService": error_counts, "alert": total >= int(threshold)}

def get_latest_log_from_s3(bucket: str, prefix: str = "") -> str:
    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")
    latest = None
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix or ""):
        for obj in page.get("Contents", []):
            if latest is None or obj["LastModified"] > latest["LastModified"]:
                latest = obj
    if not latest:
        raise FileNotFoundError("No log files found under the given bucket/prefix.")
    obj = s3.get_object(Bucket=bucket, Key=latest["Key"])
    return obj["Body"].read().decode("utf-8", errors="ignore")

# -------- Flask --------
app = Flask(__name__)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/analyze")
def analyze():
    bucket = request.args.get("bucket")
    prefix = request.args.get("prefix", "")
    threshold = int(request.args.get("threshold", "3"))
    if not bucket:
        return jsonify({"error": "Provide ?bucket=<name> (&prefix, &threshold)"}), 400
    try:
        content = get_latest_log_from_s3(bucket, prefix)
        return jsonify(process_log_content(content, threshold))
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
