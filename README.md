# 📧 AI Latest Development — Gmail Automation

A Python-based Gmail automation system using secure OAuth2 authentication and a modular architecture. Designed for AI agent workflows and email automation.

---

🚀 Features

- Gmail OAuth2 authentication
- Read/send/manage emails programmatically
- Secure environment variable handling
- Clean modular project structure

---
🗂 Project Structure

ai_latest_development/
│── src/
│ └── ai_latest_development/
│ ├── gmail_automation/
│ │ ├── email_agents.py
│ │ ├── gmail_client.py
│ │ ├── credentials.json (user provided)
│ │ ├── token.json (auto-generated)
│ ├── tools/
│ ├── config/
│ ├── crew.py
│ ├── main.py
│── .env
│── pyproject.toml
│── requirements.txt

🛠 Prerequisites

- Python 3.9+
- Google account
- Gmail API enabled in Google Cloud Console

---

⚙️ Installation

1️⃣ Clone Repository

```bash
git clone https://github.com/Dhruvpatel-1015/ai_latest_development.git
cd ai_latest_development

2️⃣ Create Virtual Environment
python -m venv .venv

Activate:

Windows (PowerShell)
.\.venv\Scripts\activate

Mac/Linux
source .venv/bin/activate

3️⃣ Install Dependencies
pip install -r requirements.txt


🔐 Gmail API Setup

1. Go to https://console.cloud.google.com/
2. Create a project
3. Enable Gmail API
4. Create OAuth Client ID → Desktop App
5. Download credentials.json


📂 Place Credentials File
Copy credentials.json into:
src/ai_latest_development/gmail_automation/


🔑 Environment Variables
Create .env in project root:
OPENAI_API_KEY=your_api_key_here



▶️ Run the Project
cd src
python -m ai_latest_development.gmail_automation.email_agents



🔄 First Run
A browser will open → Sign into Google → Grant permission → token.json will be created automatically.

Security
These files are intentionally ignored:

.env
token.json
credentials.json
.venv/
__pycache__/



🧪 Troubleshooting
1. dotenv error
pip install python-dotenv

2. OAuth timeout
Delete token.json and rerun.

3. PowerShell activation blocked
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

📄 License
MIT License

👨‍💻 Author

Dhruv Patel
Anand, Gujarat
AI & Automation Developer