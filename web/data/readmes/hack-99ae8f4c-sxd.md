```text
██████╗  █████╗  ██████╗ ███████╗██╗ ██████╗ ██╗  ██╗████████╗
██╔════╝ ██╔══██╗██╔══██╗██╔════╝██║██╔════╝ ██║  ██║╚══██╔══╝
█████╗   ███████║██████╔╝███████╗██║██║  ███╗███████║   ██║
██╔══╝   ██╔══██║██╔══██╗╚════██║██║██║   ██║██╔══██║   ██║
██║      ██║  ██║██║  ██║███████║██║╚██████╔╝██║  ██║   ██║
╚═╝      ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝

        Future Akim Strategy & Impact Governance Tool
                   ASTANA · KAZAKHSTAN
```

# FARSIGHT

Future Akim Strategy & Impact Governance Tool

FARSIGHT is an AI-powered urban strategy simulator for Astana.

The main goal is to provide a clear short-term view first, then allow users to explore the same strategy over a longer horizon. The optional long-term layer extends the two-year result into scenario planning under different assumptions and external pressures. It is not presented as an exact forecast. This connects naturally with the Kazakhstan-2050 planning horizon and the idea of evaluating today’s decisions from a longer strategic perspective.

FARSIGHT allows users to compare different strategies side by side, ask why one scenario performs better than another, explore trade-offs between districts and sectors, and request suggestions on how a strategy could be improved. Users can also ask follow-up questions about calculated results and examine how changing individual initiatives affects the overall outcome.

FARSIGHT uses three AI agents.

The Strategy Agent turns natural-language goals such as “Green Growth” or “Industrial-Mobility First” into a valid set of five initiatives.

The Future Research Agent gathers long-term factors such as population growth, water stress, transport demand, infrastructure aging and climate pressure.

The Analysis Agent explains results, compares strategies, highlights trade-offs, answers questions about the simulation and suggests possible improvements.

All official numerical results are calculated by deterministic code, not by the LLM. The long-term scenario model is kept separate from the official two-year simulation and starts from its final state.

The project is built with Next.js, TypeScript, Tailwind CSS, shadcn/ui and Recharts. AI functionality uses OpenAI models and optional web research through OpenAI Search or Tavily. The official simulation, validation and scoring layers run locally and deterministically.

Requirements:

- Node.js 24+
- pnpm 11.25.0

Run locally:

```bash
pnpm install --frozen-lockfile
pnpm dev
```

Optional AI and live research settings are documented in `.env.example`. The application can still run without API keys using local fallback behavior.

Verify the project:

```bash
pnpm test
pnpm typecheck
pnpm build
```
