# Career Quest

Career Quest is an employee development platform built with Go and server-rendered HTML. It helps employees identify skill gaps, choose relevant learning activities, and track progress toward the next career grade. HR users can manage accounts, import datasets, and review team participation.

## Features

- Individual employee and HR accounts with role-based access.
- Skill profiles, next-grade requirements, and progress tracking.
- Up to three ordered development recommendations with supporting evidence.
- Optional AI-assisted recommendations with a clearly labeled rules fallback.
- Activity completion with recorded before-and-after skill changes.
- HR summaries for skill gaps, assessment coverage, and participation.
- Validated JSON and ZIP imports with preview for native ZIP datasets.
- Server-side sessions, CSRF protection, and atomic local persistence.

## Technology

| Component | Implementation |
| --- | --- |
| Backend | Go 1.27+, standard library |
| Interface | Server-rendered HTML templates and CSS |
| Storage | Local JSON files |
| Optional AI | OpenAI Responses API with validated structured selections |
| Dependencies | No external Go packages or frontend build required |

## Quick Start

Install [Go](https://go.dev/doc/install) **1.27 or newer**, then reopen your terminal and check `go version`. No Node.js, npm, database server, or frontend build is required.

Extract the complete project archive. Open a terminal in the directory containing `go.mod`, then run:

```powershell
go run ./cmd/career-quest
```

Open [http://localhost:567](http://localhost:567).

To use another port:

```powershell
go run ./cmd/career-quest --port 8080
```

The server binds to `127.0.0.1`. Run one instance per data directory. Press `Ctrl+C` to stop the server gracefully.

For a public website, follow [Deploy on a Linux server](#deploy-on-a-linux-server). Starting the local command alone does not publish the application.

## First-Time Setup

1. Start the application. A fresh installation creates an empty workspace and an HR account.
2. Read the initial credentials locally from `data/private/initial-credentials.txt`.
3. Sign in as HR and import your dataset.
4. Create employee accounts for the imported profiles.
5. Sign in as an employee to review skills, generate recommendations, and record completed activities.

No sample employees or activities are bundled. Existing application data and accounts are loaded on subsequent starts. Keep credential delivery files private and remove them after securely distributing the credentials.

An operator can create or reset an account while the server is stopped:

```text
go run ./cmd/career-quest provision <username> <employee-id|hr>
```

Credentials are written to a private `data/private/delivery-*.txt` file. Restart the server after command-line account changes. Put configuration options before `provision` when using a custom data directory.

## Configuration

Command-line flags override environment variables. Relative paths resolve from the working directory.

| Flag | Environment variable | Default |
| --- | --- | --- |
| `--port` | `PORT` | `567` |
| `--data-dir` | `CAREER_DATA_DIR` | `data` |
| `--secure-cookies` | `CAREER_SECURE_COOKIES=1` | Disabled |
| `--shutdown-timeout` | — | `15s` |
| `--ai-model` | `OPENAI_MODEL` | `gpt-4.1-mini` |
| — | `OPENAI_API_KEY` | Unset; rules-based recommendations |
| `--ai-timeout` | — | `20s` |

These defaults describe the bundled application configuration.

```powershell
go run ./cmd/career-quest --data-dir "C:\CareerQuest\data" --port 8080
go run ./cmd/career-quest --help
```

Enable secure cookies when serving through an HTTPS reverse proxy. Leave them disabled for direct local HTTP access.

## AI-Assisted Recommendations

The application includes an optional OpenAI provider. It reads `OPENAI_API_KEY` from the process environment; `.env` files are not loaded automatically. The application can run without an API key using its rules engine.

### Enable AI locally

Stop the running app first. In **PowerShell**, enter the key at the hidden prompt, then start the app in that same terminal:

```powershell
$careerKey = Read-Host "OpenAI API key" -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new('', $careerKey).Password
Remove-Variable careerKey
go run ./cmd/career-quest
```

In **Bash on Linux/macOS**:

```bash
read -rsp 'OpenAI API key: ' OPENAI_API_KEY
printf '\n'
export OPENAI_API_KEY
go run ./cmd/career-quest
```

These commands set the key for the current terminal and its child processes. Restarting from another terminal requires setting it again. Do not put the key in source files or the README. For a server, use the protected environment file in the deployment guide below.

Sign in to an employee with assessed skill gaps, next-grade requirements, and eligible activities. Open **Recommendations** and choose **Find my next steps** or **Refresh next steps**. A successful live result displays **AI-ASSISTED**; a generic sidebar label saying “AI-assisted recommendations” does not prove that a request succeeded. Expand **Why this fits you** to inspect the supporting evidence. A profile with no next-grade requirements cannot exercise AI selection.

The provider sends relevant skills, role and grade information, target requirements, and a bounded shortlist of eligible activities with history evidence. Employee names, employee and manager IDs, account records, and unrelated profiles are excluded. Activity titles and descriptions are included. Requests set `store: false`.

The model proposes ordered activities and evidence references. The Go backend validates eligibility, evidence, comparisons, and cumulative skill gains before saving recommendations. The model cannot directly modify employee skills.

Successful results are labeled **AI-ASSISTED**. Missing configuration uses the rules engine; timeouts, refusals, API errors, and invalid output produce a labeled **rules fallback**. Completion or import invalidates affected recommendations.

The default total AI budget is 20 seconds, including 16 seconds for generation. The implementation limits model requests to two concurrent slots and does not retry automatically. Live AI behavior requires valid credentials and model access; the presence of integration code alone does not establish successful live inference.

## Data and Imports

Application state is stored in `data/state.json`. Account records and credential delivery files are stored in `data/private/`. These paths are excluded from version control. Back up runtime data before replacing a dataset.

### JSON

A complete dataset contains `employees`, `requirements`, `activities`, and `history` arrays. Employee, activity, and requirement lists must be nonempty. Assessment levels are 0–10; target levels are 1–10. Missing assessments remain unknown.

Limits: 2 MB, 1,000 employees, 1,000 activities, and 20,000 history records. Field definitions are in `internal/careerquest/domain.go`.

### Native ZIP

Supported packages contain:

- `employees.json`
- `events.json`
- `skills.json`
- `activity_history.csv`

Upload a complete dataset to replace current data, or append employee profiles and history to an existing official catalogue. ZIP uploads are limited to 20 MB. Review the import preview before confirming.

Replacement clears recommendations and invalidates employee identity bindings; HR must assign accounts to imported profiles. Append imports preserve unchanged identity bindings. Previews expire after ten minutes and require regeneration if source data changes.

## Build and Static Analysis

Run from the project root:

```powershell
go build -o bin/career-quest.exe ./cmd/career-quest
go vet ./...
```

On Linux/macOS, build with `go build -o bin/career-quest ./cmd/career-quest`. If building an extracted archive fails with a VCS stamping error, add `-buildvcs=false` to the build command.

Run the executable from the project directory to use its `data/` folder, or specify `--data-dir`. Templates and styles are embedded in the binary, so no separate web directory is needed at runtime.

The archive does not bundle automated test files. The commands above build the application and perform static analysis; they do not establish end-to-end or live AI verification.

## Deploy on a Linux server

This is a single-server deployment for Ubuntu/Debian with systemd and Caddy. It keeps the Go server on loopback and exposes HTTPS through a reverse proxy on the **same host**. The project does not include a Docker image or a one-click hosting configuration. A platform that requires listening on `0.0.0.0` needs a code/configuration change before deployment.

### 1. Prepare the server and build

You need SSH/sudo access, Go 1.27+, and a domain you control. Upload the project source to `/srv/career-quest-src` (or substitute your source directory). Keep credentials and runtime data out of the source upload; see migration below if preserving an existing workspace.

Run on the Linux server:

```bash
cd /srv/career-quest-src
go version
go build -o career-quest ./cmd/career-quest
go vet ./...
sudo useradd --system --home /var/lib/career-quest --shell /usr/sbin/nologin careerquest
sudo install -d -o root -g root -m 755 /opt/career-quest
sudo install -m 755 career-quest /opt/career-quest/career-quest
sudo install -d -o careerquest -g careerquest -m 700 /var/lib/career-quest
sudo install -d -o root -g root -m 700 /etc/career-quest
sudo install -m 600 /dev/null /etc/career-quest/environment
sudoedit /etc/career-quest/environment
```

The user and empty environment file commands are for the **first installation only**. For AI, put the following in the environment file, replacing the placeholder privately:

```ini
OPENAI_API_KEY=replace-with-your-own-key
OPENAI_MODEL=gpt-4.1-mini
```

Leave the file empty to run with rules-based recommendations. Do not use `export` in this file. Outbound HTTPS access to the OpenAI API is required for AI requests.

### 2. Run as a service

Create `/etc/systemd/system/career-quest.service` with `sudoedit`:

```ini
[Unit]
Description=Career Quest employee development
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=careerquest
Group=careerquest
WorkingDirectory=/opt/career-quest
EnvironmentFile=/etc/career-quest/environment
ExecStart=/opt/career-quest/career-quest --port 8080 --data-dir /var/lib/career-quest --secure-cookies
Restart=on-failure
RestartSec=5
TimeoutStopSec=30
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=strict
ReadWritePaths=/var/lib/career-quest

[Install]
WantedBy=multi-user.target
```

Start it and verify that the local server responds:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now career-quest
sudo systemctl status career-quest --no-pager
curl -I http://127.0.0.1:8080/
```

The service starts at boot and restarts after failure. Sessions are held in memory, so users must sign in again after an application restart. Secure cookies mean browser sign-in must use the HTTPS domain configured next, not direct HTTP.

### 3. Add a domain and HTTPS

Install Caddy using its [official Debian/Ubuntu package instructions](https://caddyserver.com/docs/install#debian-ubuntu-raspbian). Point your domain's DNS `A` record to the server's public IPv4 address; only add an `AAAA` record if IPv6 is working. Allow inbound TCP ports **80 and 443** in both your hosting firewall and host firewall; keep SSH access available. Do not expose port 8080.

Use `sudoedit /etc/caddy/Caddyfile` and add this site block, replacing `career.example.com` with your domain. Preserve any other sites already configured:

```caddyfile
career.example.com {
    reverse_proxy 127.0.0.1:8080
}
```

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl enable --now caddy
sudo systemctl reload caddy
```

Caddy provisions and renews HTTPS certificates when DNS and network access are correct. See its [HTTPS guide](https://caddyserver.com/docs/quick-starts/https). Open `https://career.example.com`, using your actual domain.

### 4. Initialize and verify

On a fresh installation, read `/var/lib/career-quest/private/initial-credentials.txt` privately on the server. Sign in as HR, import your dataset, and create employee accounts. This plaintext delivery file is not needed for authentication; remove it after securely saving/distributing credentials. Keep `private/accounts.json`, which holds the account records and password hashes.

Verify HR sign-in, dataset import, employee sign-in, and a recommendation. With AI configured, verify **AI-ASSISTED on the generated result**. Check activity completion using a dedicated verification profile because completion changes stored skills and history. Local build/static checks do not verify the deployed server or API access.

### Operations, updates, and backups

```bash
sudo journalctl -u career-quest -n 100 --no-pager
sudo systemctl restart career-quest
```

Restart after changing the environment file. The service reads it on each start.

Before updates or dataset replacement, stop the service and take a protected copy of the **entire `/var/lib/career-quest` directory**, including `state.json` and `private/accounts.json`; then start the service again. Keep dated, access-restricted backups off the server and verify restoration. Back up `/etc/career-quest/environment` separately as a secret, plus the service and Caddy configuration. Never serve backups through the website.

For an application update, build the new source first. Stop the service, retain a copy of the previous binary, install the new binary at `/opt/career-quest/career-quest`, then start the service and check its logs and sign-in page. Do not replace or clear the data directory during an update. If rollback is needed, stop the service and restore the previous binary together with a compatible data backup.

To migrate the existing local workspace, stop both instances and copy the **contents** of local `data/` into `/var/lib/career-quest` before starting the server. Restore ownership with `sudo chown -R careerquest:careerquest /var/lib/career-quest` and restrict access with `sudo chmod -R u+rwX,go-rwx /var/lib/career-quest`. Do not run two processes against the same directory.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `go` is not recognized or the toolchain is too old | Install Go 1.27+ and reopen the terminal; check `go version`. |
| Port already in use | Stop the existing instance or choose another `--port`. Update the proxy if changing the deployed port. |
| Empty employee workspace | A fresh install has no demo data. Sign in as HR, import a dataset, and bind an employee account. |
| No next-grade requirements / no useful activities | Import the relevant requirements and activities; check the employee's grade and assessments. |
| Rules-based: AI is not configured | Set `OPENAI_API_KEY` in the process environment or service environment file, then restart. `.env` files are not auto-loaded. |
| AI fallback | Read the result's reason. Check key validity, API quota/model access, outbound HTTPS, or timeout. The app preserves rules recommendations when AI fails. |
| Changes do not appear | Rebuild/restart after source changes; templates and CSS are embedded. Sign in again after restarting. |
| Sign-in does not persist over HTTP | Use the HTTPS domain when `--secure-cookies` is enabled; disable that option only for local HTTP. |
| HTTPS or proxy failure | Check DNS, ports 80/443, `systemctl status caddy`, and the backend response on `127.0.0.1:8080`. |
| Forgotten password | Stop the app and use the documented `provision` command to reset the account; deliver the new private credentials and restart. |

## Project Structure

```text
cmd/
  career-quest/
    main.go                 Command entry point and flags
internal/
  careerquest/
    config.go               Runtime configuration
    runtime.go              Startup and graceful shutdown
    server.go               HTTP workflows
    auth.go                 Accounts and sessions
    domain.go               Domain types and validation
    reasoning.go            Recommendation scoring and evidence
    provider.go             Provider contracts and validation
    openai.go               OpenAI transport
    progress.go             Skill progress calculations
    engagement.go           Participation indicators
    summary.go              Indexed summaries
    import_official.go      Native dataset adapter
    official_http.go        Import preview and commit
    store.go                Atomic local persistence
    assets.go               Embedded web assets
    web/
      templates/            Page layouts and reusable sections
      static/               Public styles and assets
data/                       Local runtime data
README.md
go.mod
```

## Scope and Limitations

- Runs locally or on a single server behind an HTTPS proxy, with one process per data directory.
- Uses JSON persistence rather than a separate database server.
- Activity completion is self-reported.
- Meeting skill targets does not automatically promote an employee.
- AI recommendations depend on external API availability and configuration.

Use `gofmt` for Go source and keep runtime data, credentials, and generated binaries out of version control.
