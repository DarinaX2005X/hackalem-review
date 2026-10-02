# Vencera AI — HackAlem MVP

Working, responsive contractor-matching MVP for Kazakhstan. The browser bundles the official anonymized 66-profile CSV for a reliable offline demo. A small optional Node API serves the same matcher.

## Run

The Vite frontend needs Node.js 20.19+ or 22.12+. The shared Node API and `npm test` need Node.js 24 because they import the TypeScript matcher directly.

```bash
npm install
npm run dev
```

Open the URL printed by Vite. Run `npm test` for the CSV/acceptance checks and `npm run build` for the production check. `Vencera-AI-demo.html` is a standalone, directly openable build for sharing; regenerate it after changes with `npm run build` then `node scripts/create-standalone.mjs`.

With Node.js 24, `npm run build && npm run serve` starts the production static server and `POST /api/match` on `http://127.0.0.1:4173`. The endpoint accepts the PDF's `budget_kzt`, `duration_hours`, `must_keep`, and `preferences` fields, and returns status, up to three cards, structured/source-text evidence, diagnostics, decision trace, and scoring version. The UI calls the same matcher locally so the standalone HTML also works without the server.

## Data and import

`data/contractors.csv` is a byte-for-byte copy of the user-supplied hackathon CSV. The original Downloads file is untouched. `src/data/contractors.json` is the parsed app data. Regenerate both with:

```bash
node scripts/import-csv.mjs "path/to/hackathon dataset anonymized .csv"
```

The importer checks the exact column schema, 66 unique IDs, 13 synthetic profiles, 8 imputed cities, and 18 imputed prices. The app displays these flags per card. Descriptions are labeled as profile statements, not verified portfolio or third-party evidence.

## Matching rules

`src/matcher.ts` applies exact city and category matching, then event format, starting price ≤ budget, required language, applicable duration, and exact busy-date exclusion. `max_hours: null` means not applicable. No result is marked available outside the CSV calendar (23 September–31 December 2026). The user can mark date or budget flexible and language required or desired; alternatives never change fixed conditions.

Eligible profiles are ranked deterministically by a versioned (`csv-v1`) overlap between request words and the profile description, then starting price ascending, then ID ascending. Only the first three are shown. The same query and data always give the same IDs and order. The interface shows structured evidence, a source excerpt, a material unknown, a follow-up question, and a Decision Trace with sequential filter counts. Rejection counts use the first failing condition in the fixed filter order.

Prices are explicitly **starting prices**, not a final quote. Source descriptions are self-reported claims. There are no fabricated ratings, reviews, guarantees, or availability outside the dataset.

## Experience

The landing page uses a black-and-white editorial system, Cormorant Garamond display typography, restrained motion, and an original AI-generated campaign image at `public/images/vencera-editorial-hero.png`. The concierge guides the user through event, city, category, date, budget, language importance, duration, and a free-text preference, then runs the same CSV-backed matcher. Animated workflow steps, result trace, category index, mobile navigation, and reduced-motion support are included.

## Scenario walkthroughs

Use the concierge and choose the following inputs:

- Wedding, Almaty, host, 30 September 2026, 1,000,000 ₸, Russian required, 8 hours: five eligible, up to three shown.
- Same conditions at 10 hours: three eligible profiles.
- Wedding ceremony host, Almaty, 24 September 2026, 300,000 ₸, Russian required, 3 hours: two real matches.
- Florist, Astana, 24 September 2026, 300,000 ₸, date flexible: no available profile that day; 25 September is suggested.
- Instrumentalist, Astana: category-missing state.

Choose the same city/category/date with date fixed in the florist case to confirm that no alternative date is suggested. Choose a date outside the calendar to see the unverified-availability state.

## Architecture and limits

- `src/App.tsx`: editorial landing page, animated concierge chat, results, Decision Trace, process and category sections.
- `src/matcher.ts`: deterministic filtering, ranking, diagnostics, permitted alternatives, shared with the optional API.
- `server.mjs`: production static server and `POST /api/match` adapter.
- `src/demo.ts`: real CSV demo queries, not fake profiles.
- `src/types.ts`: interface contract.
- `src/styles.css`: responsive design.
- `public/images/vencera-editorial-hero.png`: original campaign visual.

This hackathon build does not persist user data, and its optional API is not a hardened public deployment. The PDF's portfolio-media phase is intentionally not implemented: the CSV has no rights-cleared project photos or videos, and `description` is not a portfolio. Booking, payments, accounts, notifications, face/emotion/age inference, and ratings are also outside MVP scope. Before a public portfolio launch, confirm consent, image rights, Kazakh data residency, retention/deletion, moderation, and applicable law with qualified counsel.

The [Figma handoff](https://www.figma.com/design/CZg4hdmY8aqptG3db2L2CZ) reflects the earlier UI baseline. The code is the current source of truth for the CSV-powered MVP.
