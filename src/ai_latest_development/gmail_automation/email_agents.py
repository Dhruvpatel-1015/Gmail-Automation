"""
email_agents.py
----------------
Automated Gmail handling using CrewAI + Groq:
1. ReaderAgent - reads and summarizes emails.
2. DecisionAgent - decides response type (includes "no reply needed").
3. DraftAgent - drafts reply and saves it to Gmail Drafts.
"""
import os
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from ai_latest_development.gmail_automation.gmail_client import GmailClient
from crewai import LLM  # ✅ correct import
import sys
import io

load_dotenv()

# -----------------------------
# ✅ Initialize Groq LLM
# -----------------------------
llm = LLM(
    model="groq/llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY")
)

# -----------------------------
# ✅ Gmail Setup
# -----------------------------
#BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
#TOKEN_PATH = os.path.join(BASE_DIR, "token.json")

#gmail = GmailClient(
#    credentials_path=CREDENTIALS_PATH,
#    token_path=TOKEN_PATH
#)
gmail = GmailClient()
gmail.authenticate()

# -----------------------------
# ✅ Define AI Agents
# -----------------------------
reader_agent = Agent(
    role="Email Reader",
    goal="Read recent emails and summarize key points clearly and concisely.",
    backstory="An AI assistant that reviews emails and extracts important insights from them.",
    llm=llm,
)

decision_agent = Agent(
    role="Response Decider",
    goal=(
        "Determine whether this email requires a reply. "
        "If it does, classify the response type such as 'follow-up', 'thank you', or 'information request'. "
        "If it does NOT require a reply (e.g., promotions, confirmations, newsletters, receipts), "
        "simply return 'no reply needed'."
    ),
    backstory="A logical decision-maker that categorizes emails and determines whether a response is necessary.",
    llm=llm,
)

draft_agent = Agent(
    role="Email Drafter",
    goal="Write a polite, context-aware draft reply ONLY if a reply is needed.",
    backstory="An AI writer that crafts natural, professional responses to real emails.",
    llm=llm,
)

# -----------------------------
# ✅ Helper function: Fetch latest email
# -----------------------------
def get_latest_email():
    """Fetch the latest email message."""
    messages = gmail.list_messages(1)
    if not messages:
        print("📭 No new messages found.")
        return None

    msg = gmail.read_message(messages[0]["id"])

    # Validate structure
    if not isinstance(msg, dict) or "body" not in msg:
        print("⚠️ Unexpected email format or empty body.")
        return None

    return msg

# -----------------------------
# ✅ Main Execution (Smart Handling)
# -----------------------------
def run_email_automation():
    print(f"\n🚀 Starting automated email handling at {datetime.now()}")

    email_data = get_latest_email()
    if not email_data:
        print("❌ No email data to process.")
        return

    email_text = email_data.get("body", "").strip()
    if not email_text:
        print("⚠️ Empty email body. Skipping...")
        return

    print("\n📩 Processing latest email...")

    # --- Step 1: Reader + Decision tasks ---
    read_task = Task(
        description=f"Summarize this email:\n\nSubject: {email_data.get('subject', '')}\nFrom: {email_data.get('sender', '')}\n\nBody:\n{email_text}",
        agent=reader_agent,
        expected_output="A short summary of the latest email in plain English.",
    )

    decide_task = Task(
        description=f"Based on this email content:\n\n{email_text}\n\nDecide what type of response is appropriate — e.g., 'follow-up', 'thank you', 'information request', or 'no reply needed'.",
        agent=decision_agent,
        expected_output="One of: follow-up, thank you, information request, or no reply needed.",
    )

    decision_crew = Crew(
        agents=[reader_agent, decision_agent],
        tasks=[read_task, decide_task],
    )

    try:
        result = decision_crew.kickoff()
        reader_summary, decision = None, None

        if hasattr(result, "tasks_output"):
            for i, task_output in enumerate(result.tasks_output):
                output_value = getattr(task_output, "output_text", None) \
                    or getattr(task_output, "raw_output", None) \
                    or getattr(task_output, "final_output", None) \
                    or str(task_output)

                if i == 0:
                    reader_summary = output_value
                elif i == 1:
                    decision = str(output_value).lower()

        print("\n📘 Reader Summary:", reader_summary)
        print("⚖️ Decision:", decision)

        if decision and "no reply" in decision:
            print("ℹ️ No reply needed for this email (e.g., promotion, newsletter, purchase receipt). Skipping draft creation.")
            return

        # --- Step 2: Generate Draft Reply ---
        print("\n✍️ Generating draft reply...")

        draft_task = Task(
            description=f"Using this email content:\n\n{email_text}\n\nand the decision result ({decision}), write a polite, professional email draft. DO NOT send it, just return the draft text.",
            agent=draft_agent,
            expected_output="A professional email draft based on the decision above.",
        )

        draft_crew = Crew(
            agents=[draft_agent],
            tasks=[draft_task],
        )

        buffer = io.StringIO()
        sys_stdout = sys.stdout
        sys.stdout = buffer
        
        draft_result = draft_crew.kickoff()
        
        sys.stdout = sys_stdout  # restore
        streamed_output = buffer.getvalue().strip()
        buffer.close()
        
        draft_reply = None
        
        # ✅ Try structured CrewAI outputs
        if hasattr(draft_result, "tasks_output") and draft_result.tasks_output:
            first_output = draft_result.tasks_output[0]
            draft_reply = (
                getattr(first_output, "output_text", None)
                or getattr(first_output, "raw_output", None)
                or getattr(first_output, "final_output", None)
            )
        
        # ✅ If still empty, use CrewOutput’s string representation
        if (not draft_reply or not draft_reply.strip()):
            try:
                # CrewAI often returns the actual reply text via __str__
                draft_reply = str(draft_result).strip()
            except Exception:
                pass
            
        # ✅ Fallback to streamed stdout (printed output)
        if (not draft_reply or not draft_reply.strip()) and streamed_output:
            draft_reply = streamed_output
        
        # 🧹 Final cleanup — remove any debug junk if present
        if "Type of draft_result:" in draft_reply:
            draft_reply = draft_reply.split("Type of draft_result:")[0].strip()
        
        print("\n📝 Draft Reply:\n", draft_reply)



        if draft_reply and isinstance(draft_reply, str) and draft_reply.strip():
            sender = email_data.get("sender", "")
            subject = f"Re: {email_data.get('subject', '')}"
            gmail.create_draft(to=sender, subject=subject, body=draft_reply)
            print("📤 Draft successfully created in Gmail!")
        else:
            print("⚠️ No valid draft generated.")

    except Exception as e:
        print(f"❌ Error during email automation: {e}")


if __name__ == "__main__":
    run_email_automation()
