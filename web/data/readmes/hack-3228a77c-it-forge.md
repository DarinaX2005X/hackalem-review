<div align="center">

# AI Sana Challenge Hub

**Business challenges. Student talent. Real project experience.**

A Flutter workspace that takes a business idea from a clear brief to a student proposal and project delivery.

[![Flutter](https://img.shields.io/badge/Flutter-UI-02569B?logo=flutter&logoColor=white)](pubspec.yaml)
[![Dart](https://img.shields.io/badge/Dart-%5E3.11.4-0175C2?logo=dart&logoColor=white)](pubspec.yaml)
[![Android](https://img.shields.io/badge/Android-Work.ai-0037B0?logo=android&logoColor=white)](android/)
[![OpenAI](https://img.shields.io/badge/OpenAI-optional_server_integration-131B2E)](docs/openai-setup.md)

[Quick start](#quick-start) · [Product flows](#product-flows) · [OpenAI setup](docs/openai-setup.md) · [Verification](#verification)

</div>

---

## The experience

Work.ai connects business problems with students who can solve them. Its Kazakh-language interface follows the updated design in [designappwai2](designappwai2/): blue brand accents, light surfaces, focused project cards, student/business workspaces and a guided challenge studio.

The Flutter implementation adds bundled **Manrope** typography, **Lucide** icons, tactile buttons, staged entrances and short page transitions. It respects reduced-motion settings, keeps tab state alive and adapts to a navigation rail on wider screens.

## Product flows

| Discover | Create | Collaborate |
| --- | --- | --- |
| Search titles, companies and skills. | Set the title, problem, budget and duration. | Submit a validated proposal with contact details. |
| Filter categories, sort and save projects. | Answer three questions with multiple selections and custom requirements. | Review applications and accept, invite or decline them in business mode. |
| Open each project's own brief. | Review and edit the actual specification that will be published. | Send messages, submit a solution URL and review delivery. |

### From idea to published challenge

~~~mermaid
flowchart LR
  A[Business problem] --> B[Title, budget, duration]
  B --> C[Three clarification steps]
  C --> D[Multiple choices + custom answers]
  D --> E[Editable specification]
  E --> F[Confirm publication]
  F --> G[Discovery + business workspace]
~~~

Drafts are saved between visits. Publishing keeps the entered budget, duration, selections and edited specification. Student applications are linked to the correct project; accepting an application creates a task, and submitting a solution changes its status.

### What is local, and what connects to OpenAI?

| Capability | Current boundary |
| --- | --- |
| Projects, bookmarks, profiles, applications, task decisions and chat | One local workspace, saved on the device with SharedPreferences |
| Guided questions without a server | Topic-based templates; the flower project includes catalog/3D/AR, delivery and AI choices from the reference |
| Optional OpenAI assistance | A companion Node server calls the Responses API for structured questions and editable specifications |
| Authentication and company delivery | Not connected; local role switching is not server authentication |
| Payments and escrow | Not connected; no real balances or transfers |
| Example companies, projects and conversations | Demonstration data; no live company communication is implied |

The readiness indicator on newly published projects measures completion of the brief, not independent AI verification. With OpenAI enabled, the builder explains what project data will be sent, handles connection errors and lets the user explicitly continue with local questions.

## Quick start

Requirements: Flutter compatible with Dart **^3.11.4**, an Android SDK/device or Chrome. OpenAI integration additionally needs Node.js **22+**.

~~~bash
git clone https://github.com/BAITC-Hacks/hack-3228a77c-it-forge.git
cd hack-3228a77c-it-forge
flutter pub get
flutter devices
flutter run -d <device-id>
~~~

For web:

~~~bash
flutter run -d chrome
~~~

For live AI, follow [OpenAI setup](docs/openai-setup.md). The key belongs in the ignored server environment file. It is never compiled into the Flutter application.

## Architecture

~~~mermaid
flowchart TD
  UI[Flutter feature screens] <--> S[WorkspaceStore]
  S <--> P[Device persistence]
  B[Challenge studio] --> L[Local clarification service]
  B --> C[Optional HTTP client]
  C --> N[Loopback Node companion]
  N --> O[OpenAI Responses API]
~~~

~~~text
lib/
├── app/                  App shell, theme, responsive navigation
├── core/
│   ├── services/         Local questions and optional AI client
│   └── state/            Shared workspace and persistence
├── features/
│   ├── challenges/       Builder, detail and application
│   ├── home/             Discovery, search and filters
│   └── workspace/        Responses, tasks, chat and profiles
├── shared/               Models, demo data and reusable UI
└── main.dart

assets/fonts/             Bundled Manrope and its OFL license
server/                   Local OpenAI adapter and tests
test/                     State, persistence and UI workflow tests
designappwai2/             Updated reference design; not app runtime
~~~

Flutter uses Material widgets and local state primitives with a shared ChangeNotifier store. Tabs retain their state. Writes are serialized, persistence errors are surfaced and damaged stored data is not automatically overwritten.

## Verification

~~~bash
flutter analyze
flutter test
node --test server/server.test.mjs
flutter build apk --debug --target-platform android-arm64
~~~

Tests cover saved data round trips, duplicate applications, task status transitions, malformed storage, relevant clarification questions, search, mobile navigation, retained chat, edited specification publication and wide-screen layout. Server tests use mocked responses and make no paid API calls.

A practical walkthrough:

1. Open **Profile → Кәсіпкер → Жаңа тапсырма**.
2. Enter a flower-delivery project, a problem, a budget and a duration.
3. Select multiple catalog options and add a custom requirement.
4. Complete the other steps, edit the final specification and publish.
5. Open the published card from discovery.
6. Switch to the student role, apply and inspect **Жауаптар**.
7. Return to business mode and accept the application.
8. Submit a solution from **Тапсырмалар**, then review it in business mode.
9. Send a message, switch tabs and restart the app to check retention.

## Before a public release

The local demo needs authenticated server accounts, a shared database, authorized company messaging, attachment storage and a deployed HTTPS AI backend before supporting real independent users. The included Node server is loopback-only development infrastructure. Android still uses the example application ID and development signing.

The design reference is preserved separately. Its web code and example API configuration are not consumed by Flutter.

---

Built for the **AI SANA** practical hackathon case. The product is **Work.ai**.
