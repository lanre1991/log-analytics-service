import argparse
import json
import boto3
from collections import Counter


def process_logs(log_data, threshold):
    """
    Parses and analyzes log data, returning a summary JSON.
    """
    counts = Counter()
    total = 0

    for line in log_data:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue  # skip malformed lines

        if record.get("level") == "ERROR":
            service = record.get("service") or record.get("module") or "unknown"
            counts[service] += 1
            total += 1

    summary = {
        "total": total,
        "byService": dict(counts),
        "alert": total >= threshold,
    }
    return summary


def read_local_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            yield line


def read_latest_s3_file(bucket, prefix):
    s3 = boto3.client("s3")

    # Find latest object under prefix
    paginator = s3.get_paginator("list_objects_v2")
    latest_obj = None
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if latest_obj is None or obj["LastModified"] > latest_obj["LastModified"]:
                latest_obj = obj

    if not latest_obj:
        raise ValueError("No objects found at the given bucket/prefix")

    key = latest_obj["Key"]
    resp = s3.get_object(Bucket=bucket, Key=key)
    for line in resp["Body"].iter_lines():
        yield line.decode("utf-8")


def main():
    parser = argparse.ArgumentParser(description="Log Analytics Service")
    parser.add_argument("--bucket", help="S3 bucket name")
    parser.add_argument("--prefix", help="S3 prefix (folder)")
    parser.add_argument("--file", help="Local JSONL log file")
    parser.add_argument("--threshold", type=int, default=3, help="Error threshold for alerts")

    args = parser.parse_args()

    if not args.file and not args.bucket:
        parser.error("Provide either --file or --bucket")

    if args.file:
        lines = read_local_file(args.file)
    else:
        lines = read_latest_s3_file(args.bucket, args.prefix or "")

    result = process_logs(lines, args.threshold)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()