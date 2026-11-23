# Project structure

What every folder and file of UIMM Boost does. Files marked ★ are the ones to know first.

```
UIMM_app/
├── README.md                         ★ Presentation of the project: features, architecture, install, tests, CI/CD
├── PROJECT_STRUCTURE.md                This file
├── .gitignore                          Files Git must never save (secrets, venv, node_modules, local data)
├── compose.production.yml            ★ Production stack on the OVH server: PostgreSQL + backend + frontend (Docker Compose)
│
├── .github/workflows/
│   └── ci.yml                        ★ CI/CD pipeline: tests + frontend build on every push, then deploy to OVH
│
├── monitoring/                         Monitoring, run locally with Docker
│   ├── docker-compose.monitoring.yml   Starts Prometheus (collects metrics) and Grafana (dashboards)
│   ├── prometheus.yml                  Tells Prometheus to read the API's /metrics every 15 seconds
│   ├── alert_rules.yml                 The 4 alerts: API down, >5 % errors, AI failures, AI too slow
│   ├── grafana-datasource.yml          Connects Grafana to Prometheus automatically
│   ├── grafana-dashboard.json          The exported Grafana dashboard (import it in Grafana)
│   └── README.md                       How to start the monitoring and test an alert
│
├── Backend/                            The API, written in Python with FastAPI
│   ├── Dockerfile                      How to build the backend Docker image
│   ├── .dockerignore                   Files left out of the Docker image
│   ├── .gitignore                      Backend files Git must ignore (.env, coverage…)
│   ├── .env.example                  ★ The settings the backend needs (copy to .env and fill in)
│   ├── requirements.txt                Python packages for the application
│   ├── requirements-test.txt           Python packages for the tests (used by the CI)
│   │
│   ├── app/
│   │   ├── main.py                   ★ Starts the API: CORS, monitoring, database updates at startup, all routers
│   │   ├── database.py                 Connection to PostgreSQL (DATABASE_URL) and the session used by every route
│   │   ├── monitoring.py               JSON logs + Prometheus metrics (requests, AI calls, tokens, feedback loop)
│   │   ├── setup_database.py         ★ First install: creates the 6 axes, their scoring scales and the first admin
│   │   │
│   │   ├── dependencies/
│   │   │   └── auth.py               ★ Reads the JWT token of each request; checks the user is active and has the right role
│   │   │
│   │   ├── models/                     Database tables (SQLAlchemy): one file = one table
│   │   │   ├── company.py              companies: the company diagnosed (name, contact, status, dates…)
│   │   │   ├── axis.py                 axes: the 6 diagnostic axes (Stratégie, Performance, Marketing, RH, Digitalisation, RSE)
│   │   │   ├── axis_question_category.py  Categories that group the questions inside an axis
│   │   │   ├── question.py             questions: the diagnostic questions of each axis
│   │   │   ├── answer.py               answers: a company's answer to a question (+ score and comment)
│   │   │   ├── score.py                scores: the calculated score of a company on an axis
│   │   │   ├── scoring_scale.py        The scoring scale of an axis (0–5, or SO/0–3 for RSE)
│   │   │   ├── scoring_level.py        The levels of a scale (e.g. 3 = "En place mais partiel")
│   │   │   ├── company_axis.py         Which axes are selected for a company's diagnostic
│   │   │   ├── company_profile_section.py   Sections of the company profile questionnaire
│   │   │   ├── company_profile_question.py  Questions of the company profile
│   │   │   ├── company_profile_answer.py    Answers of a company to its profile questions
│   │   │   ├── swot.py                 The SWOT of a company (AI draft or manual, draft or validated)
│   │   │   └── user.py                 users: consultants and admins (password stored as an Argon2 hash)
│   │   │
│   │   ├── schemas/                    The shape of the data the API receives and returns (Pydantic): one file per topic
│   │   │                               e.g. auth.py defines the login request and answer
│   │   │
│   │   ├── routers/                    The API routes (URLs), grouped by topic
│   │   │   ├── auth.py               ★ POST /auth/login: checks the password, returns a JWT token
│   │   │   ├── users.py                Create, edit, deactivate users (admin only)
│   │   │   ├── companies.py          ★ Create, read, edit, archive, delete companies
│   │   │   ├── company_profile.py      Company profile questionnaire: sections, questions, answers
│   │   │   ├── company_axes.py         Choose which axes a company's diagnostic covers
│   │   │   ├── axes.py                 List and edit the diagnostic axes
│   │   │   ├── axis_question_categories.py  Categories of questions inside an axis
│   │   │   ├── admin_axis_questions.py Create, edit and reorder the diagnostic questions (admin)
│   │   │   ├── answers.py              Save a company's answer to a question
│   │   │   ├── scoring.py              Edit the scoring scales and levels
│   │   │   ├── scores.py               Calculate and read a company's scores per axis, and the average of archived diagnostics
│   │   │   ├── swots.py              ★ Generate the SWOT with Azure OpenAI, edit it, validate it
│   │   │
│   │   ├── services/                   The business logic used by the routers
│   │   │   ├── security.py           ★ Password hashing (Argon2) and JWT token creation
│   │   │   ├── azure_openai_service.py ★ The single place that calls Azure OpenAI (timed and counted for monitoring)
│   │   │   ├── swot_context.py         Gathers the answers, scores and profile of a company for the SWOT
│   │   │   ├── swot_ai_payload.py    ★ Prepares what is sent to the AI for the SWOT; redact_text() hides company and contact details
│   │   │   ├── swot_ai_service.py      The SWOT prompt and the call to the AI
│   │   │   ├── swot_generation_service.py  Checks the AI's SWOT before saving it
│   │   │   ├── diagnostic_scope_service.py Deletes the old seventh axis (and its data) from older databases
│   │   │
│   │
│   └── tests/                          Automated tests (pytest), run by the CI on every push
│       ├── conftest.py                 Gives each test a fresh, empty in-memory database
│       ├── test_six_axes.py            The 6 axes, the clean-up of the old seventh axis, scores and radar
│       ├── test_monitoring.py          Logs and metrics, with a fake Azure OpenAI
│       └── test_setup_database.py      The first-install script
│
└── Frontend/                           The web interface, written in React with Vite
    ├── Dockerfile                      Builds the site and serves it with nginx
    ├── nginx.conf                      Production web server: serves the pages, sends /api to the backend, hides /api/metrics
    ├── index.html                      The single HTML page React fills in
    ├── package.json                    JavaScript packages and commands (npm run dev, npm run build)
    ├── vite.config.js                  Vite settings (development server and build)
    ├── eslint.config.js                Code style rules for JavaScript
    └── src/
        ├── main.jsx                    Starts React and loads App
        ├── App.jsx                   ★ All the pages and their URLs; protects pages that need a login
        ├── App.css, index.css          Styles shared by every page
        ├── api/api.js                ★ Axios client: the API address + adds the JWT token to every request
        ├── utils/french.js             French labels for values stored in English (draft -> Brouillon…)
        ├── components/
        │   ├── AppHeader.jsx           Top bar shown on every page (menu, logout)
        │   ├── PageBackButton.jsx      "Back" button
        │   └── PortfolioHero.jsx       Header block of the companies page
        ├── pages/                      One file = one screen
        │   ├── LoginPage.jsx           /login: sign in
        │   ├── DashboardPage.jsx       /dashboard: home with the shortcuts (admin cards for admins)
        │   ├── CompaniesPage.jsx     ★ /companies: list, filters, "Créer une société" with the registry search
        │   ├── CompanyDetailsPage.jsx  /companies/:id: company information and profile
        │   ├── DiagnosticPage.jsx      /companies/:id/diagnostic: choose the axes, see progress
        │   ├── AxisQuestionnairePage.jsx  /companies/:id/diagnostic/:axisId: answer the questions of one axis
        │   ├── ScoresPage.jsx          /companies/:id/scores: scores per axis and radar chart
        │   ├── AnalysisPage.jsx        /companies/:id/analysis: the SWOT (generate with AI, edit, validate)
        │   ├── AdminAxesPage.jsx       /admin/axes: edit the axes
        │   ├── AdminAxisQuestionsPage.jsx    /admin/axis-questions: manage the diagnostic questions
        │   ├── AdminProfileQuestionsPage.jsx /admin/profile-questions: manage the profile questions
        │   └── AdminUsersPage.jsx      /admin/users: manage the users
        └── styles/                     One stylesheet per page or topic (companies.css, forms.css…)
```

## How a request travels

```
Browser (React page)
  -> api/api.js adds the JWT token
  -> nginx (production) or Vite (local) forwards to the API
  -> main.py: monitoring middleware logs and counts the request
  -> routers/<topic>.py: the route
       -> dependencies/auth.py checks the token and the role
       -> services/<topic>.py does the work (and calls Azure OpenAI if needed)
       -> models/<table>.py reads or writes PostgreSQL
       -> schemas/<topic>.py shapes the answer
  -> JSON answer back to the page
```
