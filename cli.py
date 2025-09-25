import argparse, json
from app import process_log_content, get_latest_log_from_s3

def main():
    p = argparse.ArgumentParser(description="Log Analytics Service CLI")
    p.add_argument("--file", help="Local JSONL file")
    p.add_argument("--bucket", help="S3 bucket name")
    p.add_argument("--prefix", default="", help="S3 prefix")
    p.add_argument("--threshold", type=int, default=3)
    args = p.parse_args()

    if not args.file and not args.bucket:
        p.error("Provide either --file or --bucket")

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = get_latest_log_from_s3(args.bucket, args.prefix)

    result = process_log_content(content, args.threshold)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
