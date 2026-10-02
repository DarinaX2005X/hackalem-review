# hack-fa4ed5d3-agroinovators
Hackathon team repository for Agroinovators


# TaskBridge

**TaskBridge AI** is an AI-powered agricultural workforce and opportunity platform that connects agricultural organizations with students, specialists, and project teams.

The platform helps farms, agricultural companies, laboratories, veterinary organizations, and other agricultural employers clearly describe their workforce needs, improve the quality of those requests with AI, publish them on an interactive regional map, and receive applications from relevant specialists.

The current MVP focuses on the **North Kazakhstan Region**.

---

# Project Idea

Agricultural organizations often know that they need help, but their initial request may be incomplete.

For example:

> "We need an agronomist in our village."

This statement does not tell a potential candidate:

- how many specialists are required;
- what skills are needed;
- where exactly the organization is located;
- what employment format is offered;
- what salary or compensation is available;
- whether accommodation is provided;
- how long the work will last;
- who the contact person is;
- how to apply.

TaskBridge AI helps transform this incomplete request into a structured agricultural demand card.

Example:

```text
Location: Sovetskoye, North Kazakhstan
Organization: Agricultural enterprise
Specialist: Agronomist
Required: 3 specialists
Type: Seasonal
Skills: Crop protection, soil analysis, GIS
Salary: 250,000–350,000 KZT
Accommodation: Available
Contact: agro@example.kz
Readiness: 90/100
```

# Current Limitation: AI Assistant

Due to the limited hackathon development time, we were not able to fully complete and stabilize the AI assistant before the submission deadline.

We implemented the main technical structure for the AI integration:

- a dedicated AI module in the NestJS backend;
- a `POST /ai/chat` API endpoint;
- frontend AI chat interface;
- Gemini API integration through `@google/genai`;
- environment-based API key configuration;
- frontend-to-backend communication architecture.

The intended workflow was:

```text
User
  ↓
TaskBridge AI Chat
  ↓
Next.js Frontend
  ↓
NestJS /ai/chat
  ↓
Google Gemini API
  ↓
AI clarification questions
  ↓
Structured agricultural demand
```

The current MVP focuses on the **North Kazakhstan Region of Kazakhstan**.

---

# Project Idea

Agricultural organizations often know that they need specialists, but their initial request may be incomplete.

For example:

> "We need an agronomist in our village."

This statement does not provide enough information for a potential candidate.

A student or specialist may still need to know:

- how many specialists are required;
- what skills are needed;
- where exactly the organization is located;
- what employment format is offered;
- what salary or compensation is available;
- whether accommodation is provided;
- how long the work will last;
- who the contact person is;
- how to apply.

TaskBridge AI is designed to transform this incomplete request into a structured agricultural demand card.

Example:

```text
Location: Sovetskoye, North Kazakhstan
Organization: Agricultural enterprise
Specialist: Agronomist
Required: 3 specialists
Type: Seasonal
Skills: Crop protection, soil analysis, GIS
Salary: 250,000–350,000 KZT
Accommodation: Available
Contact: agro@example.kz
Readiness: 90/100
```

The completed demand can then be published in the agricultural opportunity catalog and displayed on the interactive map.

---

# Problem

Agricultural organizations, especially those located outside major cities, may experience difficulties finding appropriate specialists.

At the same time, students and young professionals may not know:

- where agricultural specialists are currently needed;
- which villages or districts have workforce shortages;
- what exact skills employers expect;
- whether internships are available;
- whether accommodation is provided;
- what employment conditions are offered;
- how to contact the organization;
- what agricultural projects they can participate in.

Another problem is the quality of employer requests.

An agricultural organization may publish something very general, such as:

> "We need people who understand wheat diseases."

This description is not sufficient for candidates to understand whether they are suitable for the opportunity.

---

# Our Solution

TaskBridge AI provides a structured workflow for agricultural organizations and specialists.

```text
Agricultural organization
        ↓
Describes its workforce need
        ↓
System analyzes completeness
        ↓
Missing information is identified
        ↓
Organization provides additional details
        ↓
Agricultural Demand Readiness increases
        ↓
Organization confirms the information
        ↓
Demand is published
        ↓
Demand appears in catalog and map
        ↓
Student / specialist discovers the opportunity
        ↓
Candidate submits an application
        ↓
Organization reviews applications
        ↓
Accept / Contact / Reject
```

TaskBridge AI does not automatically assign candidates to organizations.

The final decision always remains with the organization.

---

# Main User Roles

## 1. Agricultural Organization

Possible organizations include:

- farms;
- agricultural enterprises;
- agricultural laboratories;
- veterinary organizations;
- biotechnology laboratories;
- food-processing companies;
- agricultural cooperatives;
- research institutions.

The organization creates a workforce demand.

Example:

> "Our farm in North Kazakhstan needs people who understand wheat diseases. We have 500 hectares."

The system helps structure the information into a complete demand card.

Important information includes:

- organization;
- location;
- production type;
- required specialist;
- number of specialists;
- required skills;
- employment type;
- employment period;
- salary or compensation;
- accommodation;
- contact information;
- application procedure.

---

## 2. Student / Specialist

Students and professionals can explore agricultural opportunities through the catalog and interactive map.

Supported specialty categories include:

- Agronomist
- Biotechnologist
- Veterinarian
- Agricultural Engineer
- Soil Scientist
- Plant Protection Specialist
- Food Technologist
- Laboratory Specialist

Supported employment formats include:

- Internship
- Full-time
- Part-time
- Seasonal
- Research project

Users can open a demand card and see:

- organization;
- location;
- required specialty;
- number of specialists;
- employment type;
- employment period;
- required skills;
- salary;
- accommodation;
- contact information;
- readiness score;
- application instructions.

A candidate can then submit an application.

---

## 3. Agricultural Organization Dashboard

Organizations can review applications submitted by students and specialists.

Example:

```text
Applicant:
Aruzhan Tolebay

Profile:
Biotechnology student

Skills:
PCR
Laboratory analysis
Plant biology

Availability:
June–August

Proposal:
I can assist with plant disease diagnostics,
laboratory analysis and biological sample preparation.
```

The organization can manually choose:

```text
Accept
Contact
Reject
```

This is an important principle of the platform:

> Technology helps organize information, but the organization makes the final hiring or collaboration decision.

---

# Agricultural Demand Readiness

One of the central features of TaskBridge AI is the **Agricultural Demand Readiness Score**.

Every agricultural workforce request receives a score between:

```text
0 – 100
```

The score shows how complete and useful the request is for potential candidates.

The current MVP scoring model is:

| Information | Points |
|---|---:|
| Location clearly specified | +15 |
| Number of specialists | +15 |
| Required specialty | +15 |
| Required skills | +15 |
| Job / internship conditions | +10 |
| Salary / compensation | +10 |
| Accommodation | +5 |
| Contact person | +10 |
| Application procedure | +5 |
| **Total** | **100** |

---

# Readiness Levels

The Readiness Score is divided into four levels.

## Draft

```text
0–39
```

The request does not contain enough information.

## Working

```text
40–69
```

The organization has added useful information, but some important details are still missing.

## Ready

```text
70–89
```

The request contains enough information to be useful for candidates.

## Priority

```text
90–100
```

The request is highly complete and clear.

---

# Example Demand Workflow

Initial request:

```text
"We need an agronomist in our village."
```

Possible initial Readiness:

```text
25/100
```

The system identifies missing information.

Example:

```text
Missing:

- number of specialists;
- required skills;
- employment period;
- salary;
- accommodation;
- contact information;
- application procedure.
```

The organization completes the form:

```text
Location:
Sovetskoye

Specialist:
Agronomist

Required:
3 specialists

Skills:
Crop protection
Soil analysis
GIS
Crop monitoring

Employment:
Seasonal

Salary:
250,000–350,000 KZT

Accommodation:
Available

Contact:
agro@example.kz
```

The Readiness Score increases:

```text
90/100
```

The organization then confirms the information and publishes the demand.

---

# Human Confirmation

TaskBridge AI follows a human confirmation principle.

The organization must confirm that the information is correct before publication.

The platform should not silently invent important information such as:

- salary;
- number of specialists;
- location;
- contact information;
- accommodation;
- employment conditions.

This is especially important for future AI functionality.

---

# AI Assistant Concept

TaskBridge AI was designed to include an agricultural AI assistant that helps organizations improve incomplete workforce requests.

Example intended conversation:

```text
User:
Our farm in Bishkul needs agronomists.

TaskBridge AI:
Please clarify:

1. How many agronomists do you need?
2. What crops does your farm produce?
3. Which skills are required?
4. What is the employment period?
5. Is accommodation provided?
6. What salary or compensation is offered?
7. How can candidates contact your organization?
```

The AI assistant was intended to:

- analyze agricultural workforce requests;
- identify missing information;
- generate clarification questions;
- suggest possible specialist categories;
- help structure demand cards;
- respond in the same language as the user;
- avoid inventing unknown information.

---

# AI Assistant Implementation Status

Due to the limited hackathon development time, we were not able to fully complete and stabilize the AI assistant before the submission deadline.

We implemented the main technical architecture for the AI functionality:

- dedicated AI module in the NestJS backend;
- `POST /ai/chat` API endpoint;
- frontend AI chat interface;
- Google Gemini API integration architecture;
- environment-based API key configuration;
- frontend-to-backend communication;
- agricultural system instructions for the AI assistant.
- 
# How to Run

After cloning the repository and installing dependencies with:

```bash
npm install
npm run dev
```

