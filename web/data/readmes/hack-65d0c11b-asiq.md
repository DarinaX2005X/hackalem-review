# QazLedger AI

AI accounting and financial analysis agent for Kazakhstan businesses.

QazLedger AI analyzes bank statement transactions, classifies accounting operations and prepares unposted draft documents in 1C for accountant review.

For HackAlem AI, the project was extended with **QazLedger MoneyGraph** — an AML transaction-network analysis module.

---

# HackAlem AI — QazLedger MoneyGraph

**Track 02 — Finance**

QazLedger MoneyGraph helps an AML analyst reconstruct the movement of funds through a transaction network, identify important accounts in the chain and prioritize nodes that require additional review.

The system combines deterministic graph analysis and risk scoring with AI-generated explanations.

## MoneyGraph Features

- builds a transaction graph from financial transfers;
- analyzes incoming and outgoing money flows;
- identifies relationships between accounts;
- detects concentration and redistribution patterns;
- assigns functional roles to nodes;
- calculates a deterministic Risk Score;
- ranks nodes by investigation priority;
- generates an AI explanation of detected patterns;
- keeps the final decision with the human AML analyst.

### Supported node roles

- `COLLECTOR` — receives funds from multiple sources and consolidates them;
- `DISTRIBUTOR` — receives funds and redistributes them to multiple recipients;
- `TRANSIT` — passes most received funds further through the network;
- `SINK` — accumulates incoming funds with little outgoing activity;
- `NORMAL` — no significant network pattern detected by the current rules.

## MoneyGraph Workflow

```text
Transactions
      ↓
Graph Construction
      ↓
Flow Analysis
      ↓
Role Detection
      ↓
Risk Scoring
      ↓
Top Risk Ranking
      ↓
OpenAI Explanation
      ↓
AML Analyst Review
```

The Risk Score and node roles are calculated by deterministic application logic.

OpenAI is used to explain the calculated results in human-readable form.  
The AI does not determine whether an account or person has committed an illegal activity.

## Example

Example transaction network:

```text
A001 ─┐
A002 ─┼──→ B001 ───→ C001
A003 ─┘
          COLLECTOR
          Risk 66
```

In this example:

- B001 receives funds from three different senders;
- total incoming amount: `370000`;
- total outgoing amount: `340000`;
- approximately 92% of received funds are transferred further;
- B001 is classified as `COLLECTOR`;
- Risk Score: `66`.

MoneyGraph marks the node as a priority for additional analyst review and generates an explanation of the detected transaction pattern.

## MoneyGraph Demo

The web interface displays:

- transaction input;
- transaction graph;
- node roles;
- Risk Score;
- Top Risk ranking;
- incoming and outgoing amounts;
- AI-generated AML explanation.

If the screenshot is uploaded to `screenshots/moneygraph.jpg`:

![QazLedger MoneyGraph](screenshots/moneygraph.jpg)

---

# Original QazLedger AI

## Problem

Accountants spend significant time manually processing bank statements:

- identifying counterparties;
- understanding payment purposes;
- classifying transactions;
- checking internal transfers;
- entering data into 1C;
- avoiding duplicate documents.

This process is repetitive and error-prone.

## Solution

QazLedger AI combines AI analysis with deterministic accounting rules and 1C integration.

The system can:

- import Kaspi Bank statements;
- analyze transaction direction and payment purpose;
- identify counterparties;
- classify accounting operations;
- detect internal transfers between own bank accounts;
- detect Kaspi Pay fees;
- detect Kaspi Bank fees;
- detect sales receipts;
- detect payments to accountable persons;
- return confidence score and explanation;
- allow the accountant to select which transactions should be created;
- create unposted draft documents in 1C;
- prevent duplicate document creation;
- never post accounting documents automatically.

## Accounting Workflow

```text
Bank Statement
      ↓
1C Statement Import
      ↓
QazLedger AI Analysis
      ↓
Transaction Classification
      ↓
Accountant Review
      ↓
Selected Transactions
      ↓
Unposted 1C Draft Documents
      ↓
Manual Verification
      ↓
Posting by Accountant
```

## Human-in-the-loop

QazLedger AI is designed as a human-in-the-loop accounting assistant.

AI does not directly post accounting documents.

The accountant can review:

- transaction date;
- amount;
- counterparty;
- AI decision;
- AI rule;
- confidence score;
- status;
- explanation.

Only transactions explicitly selected by the accountant are sent to the 1C document creation layer.

---

# Architecture

## Backend

Technologies:

- Node.js
- Express
- OpenAI API
- JavaScript

The backend exposes two main AI/analysis workflows.

### Accounting Analysis

`POST /api/analyze`

Receives one structured banking transaction and returns:

- accounting rule;
- operation name;
- transaction direction;
- suggested document;
- confidence score;
- manual review flag;
- explanation;
- suggested comment.

### MoneyGraph Analysis

`POST /api/moneygraph`

Receives an array of transactions and returns:

- graph nodes;
- graph edges;
- incoming and outgoing amounts;
- number of senders and receivers;
- node roles;
- Risk Score;
- Top Risk ranking;
- AI-generated AML summary.

Example request:

```json
{
  "transactions": [
    {
      "from": "A001",
      "to": "B001",
      "amount": 100000,
      "date": "2026-09-20"
    },
    {
      "from": "A002",
      "to": "B001",
      "amount": 150000,
      "date": "2026-09-20"
    },
    {
      "from": "A003",
      "to": "B001",
      "amount": 120000,
      "date": "2026-09-21"
    },
    {
      "from": "B001",
      "to": "C001",
      "amount": 340000,
      "date": "2026-09-21"
    }
  ]
}
```

Example result:

```text
B001
Role: COLLECTOR
Risk Score: 66
Incoming: 370000
Outgoing: 340000
Unique Senders: 3
Unique Receivers: 1
Flow Ratio: 0.92
```

---

# 1C Integration

Integration is implemented for:

**1C: Accounting for Kazakhstan, edition 3.0**

The 1C module:

- imports the bank statement;
- sends transactions for AI analysis;
- displays AI results;
- allows manual approval;
- creates unposted accounting drafts;
- searches existing documents;
- protects against duplicate creation;
- resolves own-bank-account transfers.

## Example Classifications

QazLedger AI supports rules such as:

- `SALE`
- `INTERNAL_TRANSFER`
- `ACCOUNTABLE_PERSON`
- `KASPI_PAY_FEE`
- `KASPI_BANK_FEE`
- `SUPPLIER_PAYMENT`
- `REFUND`
- `TAX_PAYMENT`
- `PAYROLL`
- `MANUAL_REVIEW`

## Internal Transfers

For transfers between the company's own bank accounts, QazLedger AI determines the transfer direction and creates only the required accounting document.

Example:

```text
Alatau City Bank → Kaspi Bank
```

The system creates an unposted outgoing payment order with:

- source bank account;
- destination bank account;
- amount;
- KNP;
- transaction date.

Duplicate internal-transfer documents are not created.

---

# Safety

QazLedger AI follows a human-controlled workflow.

### Accounting module

- no automatic posting;
- human confirmation before document creation;
- duplicate protection;
- confidence-based review;
- unposted drafts only;
- accountant remains in control.

### MoneyGraph module

- Risk Score is an analytical priority indicator;
- risk is calculated from transaction-network patterns;
- AI does not declare an account suspicious or criminal;
- AI explanations are based on calculated graph metrics;
- final assessment remains with the AML analyst.

---

# Current Status

Working prototype.

### Accounting workflow

```text
Kaspi Statement
→ AI Analysis
→ Human Approval
→ 1C Draft
→ Duplicate Check
```

Current 1C integration version:

```text
v1.5.0
```

### HackAlem MoneyGraph workflow

```text
Transactions
→ Graph Analysis
→ Role Detection
→ Risk Score
→ Top Risk
→ OpenAI Explanation
→ Analyst Review
```

The MoneyGraph prototype has been tested with a transaction chain containing multiple senders, a collector node and a downstream recipient.

---

# Working Prototype

## AI Transaction Analysis

QazLedger AI analyzes bank statement transactions directly inside 1C and shows the proposed accounting decision, rule, confidence score and explanation.

![QazLedger AI transaction analysis](screenshots/ai-analysis.jpg)

## 1C Draft Creation

After accountant approval, QazLedger AI creates an unposted 1C accounting document.

Example: transfer between the company's own bank accounts from Alatau City Bank to Kaspi Bank.

![QazLedger AI 1C internal transfer](screenshots/internal-transfer.jpg)

The accountant remains in control and manually verifies the draft before posting.

## MoneyGraph AML Analysis

MoneyGraph analyzes a financial transaction network, calculates node roles and Risk Scores and generates an AML-oriented explanation.

![QazLedger MoneyGraph](screenshots/moneygraph.jpg)

---

# Local Run

Go to the backend directory:

```bash
cd backend
```

Install dependencies:

```bash
npm install
```

Create a local `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5.6-terra
```

Do not upload `.env` to GitHub.

Start the server:

```bash
npm start
```

Open:

```text
http://localhost:3000
```

Health check:

```text
http://localhost:3000/health
```

Expected result:

```json
{
  "ok": true
}
```

---

# Project Structure

```text
/
├── backend/
│   ├── public/
│   │   └── index.html
│   ├── package.json
│   └── server.js
│
├── 1c/
│   ├── README.md
│   ├── ASIQ_Kaspi_1C_v1.5.0_OWN_TRANSFER_DIRECTION.txt
│   └── ASIQ_Kaspi_QazLedgerAI_CREATE_SELECTED_FULL.txt
│
├── screenshots/
│   ├── ai-analysis.jpg
│   ├── internal-transfer.jpg
│   └── moneygraph.jpg
│
├── .gitignore
└── README.md
```

---

# HackAlem AI

**Track 02 — Finance**

Project:

**QazLedger MoneyGraph**

Built as an extension of QazLedger AI for transaction-network and AML analysis.
