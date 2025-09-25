# Log Analytics Service

Parses JSON Lines (JSONL) error logs stored in **S3**, summarizes them, and exposes the result via:
- **CLI** (`cli.py`)
- **HTTP** (`GET /analyze`, `GET /health`) using Flask

**Response shape**
```json
{ "total": N, "byService": { "svc": n }, "alert": true | false }
````

* `total` — number of records where `level == "ERROR"`
* `byService` — grouped by `service` (fallback to `module`, else `"unknown"`)
* `alert` — `true` when `total >= threshold` (default `3`)

---

## What this README covers

This is exactly what was done for the task:

* Use **existing** S3 bucket: `devops-assignment-logs-18-08` (objects are at the bucket **root**, so no prefix).
* Run locally with a virtualenv.
* Test via **CLI** and **HTTP** against the interview AWS account.
* No bucket creation; no extra infra yet (Part 2 will handle Docker/Terraform/CI/CD).

---

## 1) Requirements

* macOS/Linux shell
* Python **3.10+**
* AWS CLI v2 configured for the interview account with permissions to **List/Get** from the bucket
* Do **not** commit any credentials

---

## 2) Setup

```bash
# clone your repo
git clone repo
cd log-analytics-service

# create and activate a virtualenv
python3 -m venv .venv
source .venv/bin/activate

# install deps
pip install -r requirements.txt
```

---

## 3) Configure AWS CLI

Use a named profile. 

```bash
aws configure --profile (name given)
# Access key ID:  created in console
# Secret access key: created in console
# Default region:     used what default set on console (eu-north-1) 
# Output format:      json
```

---

## 4) Bucket previously created

 used existing bucket that already contains `.jsonl` logs at the root:

Bucket:
BUCKET=devops-assignment-logs-18-08
```

---

## 5) Run — CLI

Analyse a **local** file:

```bash
source .venv/bin/activate
python cli.py --file sample.log --threshold 3
```

Analyse the **latest** object from **S3** (by `LastModified`):

```bash
source .venv/bin/activate
python cli.py --bucket "$BUCKET" --threshold 3
# (no --prefix needed since files are at the bucket root)
```

**Example output**

```json
{
  "total": 2,
  "byService": { "billing": 1, "orders": 1 },
  "alert": false
}
```

---

## 6) Run — HTTP

**Terminal A** — start the server:

```bash
source .venv/bin/activate
export FLASK_APP=app.py
flask run -p 8081
# -> http://127.0.0.1:8081
```

**Terminal B** — call endpoints:

```bash
# health
curl "http://127.0.0.1:8081/health"

# analyze (bucket at root)
curl "http://127.0.0.1:8081/analyze?bucket=$BUCKET&threshold=3"
```

---

## 7) API Reference

### `GET /health`

Returns:

```json
{"ok": true}
```

### `GET /analyze`

**Query params**

* `bucket` (required)
* `threshold` (optional; default `3`)
* `prefix` (optional; default `""`) — not needed for this bucket because objects are at root

**Success (200)**

```json
{ "total": 2, "byService": { "billing": 1, "orders": 1 }, "alert": false }
```
## Possible Errors 

400 — missing bucket

404 — no objects found under bucket/prefix

500 — unexpected error (permissions, etc.)

---

## 8) Project Structure

```
.
├── app.py               # Flask app + core logic + S3 helper
├── cli.py               # CLI entrypoint (same logic as HTTP)
├── requirements.txt
├── sample.log           # example JSONL for local run
├── README.md
└── .gitignore
```

---

## 10) What’s next (Part 2 – infra)

Part 2 will add Docker, Terraform (ECS Fargate + ALB + CloudFront), and CI/CD. Those files will live under:

* `Dockerfile`
* `terraform/`
* `.github/workflows/`

This README focuses on **Part 1 (Application)** as implemented above.

```