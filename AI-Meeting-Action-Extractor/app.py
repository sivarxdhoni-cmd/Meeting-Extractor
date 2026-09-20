import streamlit as st
import os
import json
from dotenv import load_dotenv
from google import genai

# --------------------------------------------------
# Load environment variables
# --------------------------------------------------

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("GEMINI_API_KEY not found. Please check your .env file.")
    st.stop()

# Gemini client
client = genai.Client(api_key=api_key)


# --------------------------------------------------
# Streamlit Page Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="AI Meeting Action-Item Extractor",
    page_icon="📋",
    layout="wide"
)


# --------------------------------------------------
# Application Title
# --------------------------------------------------

st.title("📋 AI Meeting Action-Item Extractor")

st.write(
    "Upload a meeting transcript and automatically extract "
    "action items, owners, deadlines, status, and confidence."
)


# --------------------------------------------------
# File Upload
# --------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload Meeting Transcript",
    type=["txt"]
)


# --------------------------------------------------
# Process Uploaded File
# --------------------------------------------------

if uploaded_file is not None:

    # Read transcript
    transcript = uploaded_file.read().decode("utf-8")

    # Display transcript
    st.subheader("📝 Meeting Transcript")

    st.text_area(
        "Transcript",
        transcript,
        height=300
    )


    # --------------------------------------------------
    # Extract Action Items Button
    # --------------------------------------------------

    if st.button("🤖 Extract Action Items"):

        if not transcript.strip():
            st.warning("Please upload a transcript containing some text.")
            st.stop()


        # --------------------------------------------------
        # AI Prompt
        # --------------------------------------------------

        prompt = f"""
You are an AI meeting action-item extraction assistant.

Analyze the following meeting transcript.

Your task is to identify ALL actionable tasks mentioned
during the meeting.

For every action item, extract these fields:

1. task
2. owner
3. deadline
4. status
5. confidence

Rules:

- "task" = clear description of what needs to be done.
- "owner" = person responsible for the task.
- "deadline" = deadline mentioned in the meeting.
- "status" = Pending, In Progress, Completed, or Not mentioned.
- "confidence" = number between 0 and 1.
- If owner is not mentioned, use "Not mentioned".
- If deadline is not mentioned, use "Not mentioned".
- Do not invent information.
- Extract only real actionable tasks.
- Return ONLY valid JSON.
- Do not use Markdown.
- Do not put the JSON inside ```json blocks.

Use exactly this format:

[
    {{
        "task": "Complete login page",
        "owner": "Rahul",
        "deadline": "Friday",
        "status": "In Progress",
        "confidence": 0.95
    }}
]

Meeting Transcript:

{transcript}
"""


        # --------------------------------------------------
        # Call Gemini
        # --------------------------------------------------

        try:

            with st.spinner("🤖 Gemini is analyzing the meeting..."):

                response = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=prompt
                )

                result = response.text


        except Exception as e:

            st.error("❌ Gemini API Error")

            st.code(str(e))

            st.info(
                "Please try again after some time if the Gemini model "
                "is temporarily unavailable."
            )

            st.stop()


        # --------------------------------------------------
        # Clean AI Response
        # --------------------------------------------------

        result = result.strip()

        # Remove Markdown JSON block if Gemini adds it
        if result.startswith("```json"):
            result = result.replace("```json", "", 1)

        if result.startswith("```"):
            result = result.replace("```", "", 1)

        if result.endswith("```"):
            result = result[:-3]

        result = result.strip()


        # --------------------------------------------------
        # Convert JSON
        # --------------------------------------------------

        try:

            action_items = json.loads(result)


        except json.JSONDecodeError:

            st.error("❌ Gemini returned an unexpected format.")

            st.write("Gemini Response:")

            st.code(result)

            st.stop()


        # --------------------------------------------------
        # Display Results
        # --------------------------------------------------

        st.subheader("✅ Extracted Action Items")


        if not action_items:

            st.info("No action items were found in the meeting.")

        else:

            # Display table
            st.dataframe(
                action_items,
                use_container_width=True
            )


            # --------------------------------------------------
            # Summary
            # --------------------------------------------------

            st.subheader("📊 Meeting Action Summary")

            total_tasks = len(action_items)

            completed_tasks = sum(
                1
                for item in action_items
                if item.get("status", "").lower() == "completed"
            )

            pending_tasks = sum(
                1
                for item in action_items
                if item.get("status", "").lower() == "pending"
            )

            in_progress_tasks = sum(
                1
                for item in action_items
                if item.get("status", "").lower() == "in progress"
            )


            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Total Tasks",
                    total_tasks
                )

            with col2:
                st.metric(
                    "Completed",
                    completed_tasks
                )

            with col3:
                st.metric(
                    "Pending",
                    pending_tasks
                )

            with col4:
                st.metric(
                    "In Progress",
                    in_progress_tasks
                )


            # --------------------------------------------------
            # Download JSON
            # --------------------------------------------------

            json_data = json.dumps(
                action_items,
                indent=4
            )

            st.download_button(
                label="⬇️ Download Action Items (JSON)",
                data=json_data,
                file_name="meeting_action_items.json",
                mime="application/json"
            )