# ArthaDrishti 🕵️‍♂️📈

An advanced, AI-powered Anti-Money Laundering (AML) Case Management System designed to streamline financial crime investigations, detect suspicious activities, and automate comprehensive reporting.

## 🌟 Key Features

- **Automated Statement Analysis:** Ingest and parse bank statements to automatically flag suspicious transaction patterns.
- **AI Investigator Summary:** Utilizes local LLMs (via Ollama) to instantly generate concise, actionable executive summaries detailing risk, confidence scores, and next steps for the investigator.
- **Advanced Graph & Network Analysis:** Deep transaction monitoring that detects complex typologies including:
  - *Layering & Circular Flow*
  - *Structuring (Smurfing)*
  - *Dormant Account Revival*
  - *High-Risk Beneficiary Bursts*
- **Evidence Locker & Auditing:** Immutable audit trails for all case actions, status changes, and evidence uploads, ensuring full regulatory compliance.
- **Digital Signatures & SIO Actions:** Secure case closure and escalation requiring investigator digital signatures.
- **Automated FIR & Dossier Generation:** One-click PDF report generation detailing the entire lifecycle of the investigation.

## 🛠️ Technology Stack

- **Backend:** Flask (Python), SQLAlchemy, PostgreSQL (Neon)
- **Frontend:** React.js, Vite
- **AI Engine:** Ollama (Local LLM Integration)
- **PDF Generation:** WeasyPrint / ReportLab

## 🚀 Getting Started

### Prerequisites
- Node.js & npm
- Python 3.9+
- PostgreSQL database
- Ollama (installed locally for AI features)

### Backend Setup
1. Navigate to the root directory and create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file and configure your database and JWT keys:
   ```env
   DATABASE_URL=postgresql://user:password@host/dbname
   JWT_SECRET_KEY=your_secret_key
   ```
4. Run migrations and start the server:
   ```bash
   flask db upgrade
   flask run
   ```

### Frontend Setup
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   npm install
   ```
2. Start the development server:
   ```bash
   npm run dev
   ```

## 🔒 Security & Privacy
All AI analysis is performed locally or through secure endpoints to ensure PII and sensitive financial data never leave the designated secure environment.
