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
│   ├── .gitignore                      Backend files Git must ignore (.env, pipeline_data/, coverage…)
│   ├── .env.example                  ★ The settings the backend needs (copy to .env and fill in)
│   ├── requirements.txt                Python packages for the application
│   ├── requirements-test.txt           Python packages for the tests (used by the CI)
│   ├── pipeline_data/                  (not in Git) Pipeline working folder: SIRENE file, outputs, logs
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
│   │   │   ├── company.py              companies: the company diagnosed (name, SIREN, contact, status, dates…)
│   │   │   ├── company_public_data.py  company_public_data: official data collected by the pipeline
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
│   │   │   ├── reports.py              The diagnostic report of a company
│   │   │   └── user.py                 users: consultants and admins (password stored as an Argon2 hash)
│   │   │
│   │   ├── schemas/                    The shape of the data the API receives and returns (Pydantic): one file per topic
│   │   │                               e.g. company.py checks the SIREN, auth.py defines the login request and answer
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
│   │   │   ├── reports.py            ★ Generate the report with Azure OpenAI, edit it, export the PowerPoint
│   │   │   └── public_data.py          Public data of a company, full list, live search in the official register
│   │   │
│   │   ├── services/                   The business logic used by the routers
│   │   │   ├── security.py           ★ Password hashing (Argon2) and JWT token creation
│   │   │   ├── azure_openai_service.py ★ The single place that calls Azure OpenAI (timed and counted for monitoring)
│   │   │   ├── swot_context.py         Gathers the answers, scores and profile of a company for the SWOT
│   │   │   ├── swot_ai_payload.py      Prepares what is sent to the AI for the SWOT, with names and contacts masked
│   │   │   ├── swot_ai_service.py      The SWOT prompt and the call to the AI
│   │   │   ├── swot_generation_service.py  Checks the AI's SWOT before saving it
│   │   │   ├── report_context.py       Gathers what the report needs (company, scores, SWOT)
│   │   │   ├── report_ai_payload.py  ★ Prepares the report payload; redact_text() hides company and contact details
│   │   │   ├── report_ai_service.py    The report prompt and the call to the AI
│   │   │   ├── powerpoint_report_service.py      Builds the PowerPoint file (python-pptx)
│   │   │   ├── boost_powerpoint_content_service.py  Decides what goes on each slide
│   │   │   ├── company_details_service.py  Read-only export of everything saved about a company
│   │   │   ├── diagnostic_scope_service.py Retires the Finance axis without deleting old data
│   │   │   └── siren.py                Checks a SIREN: 9 digits + checksum
│   │   │
│   │   ├── pipeline/                 ★ The public-data pipeline (E1): 5 sources -> clean dataset -> PostgreSQL
│   │   │   ├── README.md               Full documentation: sources, cleaning rules, SQL, Merise models, RGPD
│   │   │   ├── run.py                ★ Launch point: python -m app.pipeline.run --input companies.csv
│   │   │   ├── config.py               All settings: URLs, delays, folders, headcount labels
│   │   │   ├── extract_file.py         Source 1: reads the CSV of companies
│   │   │   ├── extract_database.py     Source 2: SQL query on the app's PostgreSQL
│   │   │   ├── extract_api.py          Source 3: government API "Recherche d'entreprises" (+ live search)
│   │   │   ├── extract_scraping.py     Source 4: description of each company's homepage
│   │   │   ├── extract_bigdata.py      Source 5: the 30-million-row SIRENE file, queried with DuckDB
│   │   │   ├── aggregate.py          ★ Cleans, merges and normalises the 5 sources into one dataset
│   │   │   ├── load.py                 Imports the dataset into PostgreSQL (insert or update)
│   │   │   └── companies_example.csv   Example input file
│   │   │
│   │   └── assets/                     Images used on the PowerPoint slides (SWOT backgrounds…)
│   │
│   └── tests/                          Automated tests (pytest), run by the CI on every push
│       ├── conftest.py                 Gives each test a fresh, empty in-memory database
│       ├── test_six_axes.py            The 6 axes, the Finance retirement, scores and radar
│       ├── test_monitoring.py          Logs and metrics, with a fake Azure OpenAI
│       ├── test_setup_database.py      The first-install script
│       └── test_pipeline.py            Every pipeline source, the cleaning, the import, the routes, a full run
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
        │   ├── CompanyDetailsPage.jsx  /companies/:id: company information, SIREN, public data, profile
        │   ├── DiagnosticPage.jsx      /companies/:id/diagnostic: choose the axes, see progress
        │   ├── AxisQuestionnairePage.jsx  /companies/:id/diagnostic/:axisId: answer the questions of one axis
        │   ├── ScoresPage.jsx          /companies/:id/scores: scores per axis and radar chart
        │   ├── AnalysisPage.jsx        /companies/:id/analysis: the SWOT (generate with AI, edit, validate)
        │   ├── ReportsPage.jsx         /companies/:id/reports: the report (generate, edit, PowerPoint)
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
