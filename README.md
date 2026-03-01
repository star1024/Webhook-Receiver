# Webhook Receiver + Event Log Demo

A minimal local demo for receiving webhook payloads and inspecting them in a browser.

This project provides:

- `POST /webhook` to receive JSON payloads
- `GET /api/events` to inspect the latest captured events
- `POST /api/events/clear` to reset the demo log
- `GET /api/health` for a simple health check
- a browser UI at `/` to view the event log

The app uses only Python standard library modules, so there are no extra dependencies to install.

## Demo Highlights

- Fast local setup for demos and testing
- Browser-based event log viewer
- PowerShell-friendly verification flow
- Event persistence in `data/events.jsonl`

## Run

Start the server from the project directory:

```powershell
python .\app.py
```

Open:

```text
http://127.0.0.1:8000
```

## Quick Manual Test

Send a webhook from PowerShell:

```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/webhook" `
  -ContentType "application/json" `
  -Body '{"event":"order.created","orderId":12345,"source":"demo"}'
```

Fetch the event log:

```powershell
Invoke-RestMethod -Method GET `
  -Uri "http://127.0.0.1:8000/api/events"
```

## Automated Demo Test

Run the verification script:

```powershell
.\demo-test.ps1
```

Optional parameters:

```powershell
.\demo-test.ps1 -BaseUrl "http://127.0.0.1:8000" -KeepData
```

What the script checks:

1. `GET /api/health`
2. `POST /webhook`
3. `GET /api/events`
4. `POST /api/events/clear` unless `-KeepData` is used

The script exits with a non-zero code if any check fails.

## API

### `POST /webhook`

Receives a webhook payload. If the request body is valid JSON, it is parsed and stored in the event log. If the body is not valid JSON, the raw request body is stored under `raw_body`.

### `GET /api/events`

Returns the current event log as JSON.

### `POST /api/events/clear`

Clears all current demo events.

### `GET /api/health`

Returns service status and the current event count.

## Storage

Captured events are:

- kept in memory for the live UI
- appended to `data/events.jsonl`

## PowerShell Notes

In PowerShell, `curl` is often an alias for `Invoke-WebRequest`, not the standard curl CLI. To avoid quoting issues, prefer:

```powershell
Invoke-RestMethod
```

or explicitly use:

```powershell
curl.exe
```

If you see `raw_body` in the event log, the request body was not valid JSON. Use single quotes around the JSON string in PowerShell.
