# Career Quest

Career Quest is a local employee-development dashboard. It helps employees review their skills and career goals, receive ranked learning recommendations, and track completed activities. Administrators can view HR metrics, create events, and import additional employee data.

The recommendation engine is deterministic: it ranks activities using target-role requirements, skill gaps, and the employee's learning history. The project does not call an external AI service.

## Requirements

- Node.js 20 or newer
- npm

## Run locally

```bash
git clone https://github.com/BAITC-Hacks/hack-ee5a3cd4-404-notfound.git
cd hack-ee5a3cd4-404-notfound
npm ci
npm run dev
```

Open [http://127.0.0.1:3000](http://127.0.0.1:3000).

Without a `.env` file, development mode uses this local-only administrator account:

```text
Username: admin
Password: local-development-only
```

The development server listens on `127.0.0.1`, so this fallback account is not exposed on the network. Never use it in production.

## Production

Create `.env` from the example and provide at least one user plus a 32-character-or-longer session secret:

```bash
cp .env.example .env
npm run build
NODE_ENV=production npm start
```

Example configuration:

```dotenv
APP_AUTH_USERS='[{"username":"admin","password":"replace-with-a-long-password","role":"admin"},{"username":"employee-001","password":"replace-with-a-long-password","role":"employee","employeeId":"EMP_001"}]'
AUTH_SESSION_SECRET="replace-with-at-least-32-random-characters"
```

In production the app will not start without valid `APP_AUTH_USERS` and `AUTH_SESSION_SECRET`. Use a secret manager rather than committing production credentials. Set `PORT` to change the default port (`3000`).

## Roles

- `admin` can work with all employee profiles, HR analytics, imports, and custom learning events.
- `employee` must be linked to an `employeeId` and can access only that employee's profile and actions.

Sessions are signed, stored in `HttpOnly` cookies, and expire after eight hours. State-changing API requests require a CSRF token.

## Data and state

The base dataset lives in `data/`:

- `employees.json`
- `skills.json`
- `events.json`
- `activity_history.csv`

Changes made through the app are saved to `data/runtime-state.json`. That file is ignored by Git. In a deployed environment, set `RUNTIME_STATE_PATH` to a persistent-volume location, for example:

```dotenv
RUNTIME_STATE_PATH="/var/lib/career-quest/runtime-state.json"
```

## Checks

```bash
npm run lint
npm run build
RUNTIME_STATE_PATH=/tmp/career-quest-check.json npx tsx src/scripts/verifyAllRequirements.ts
```

The last command exercises the included data and recommendation scenarios. It writes temporary state to the provided path; remove that file after the check if desired.

## Project layout

- `server.ts` - Express API and Vite/production-server setup.
- `src/` - React interface, API client, authorization, validation, and application logic.
- `data/` - bundled sample data.
