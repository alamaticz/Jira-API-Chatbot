# Jira API Chatbot

A FastAPI-based application that interacts with the Jira API to fetch issue details, search for issues, and render Jira ADF (Atlassian Document Format) content into HTML.

## Features

- **Fetch Issue Details**: Retrieve comprehensive details about a Jira issue, including summary, description, status, priority, assignee, subtasks, attachments, and comments.
- **ADF Rendering**: Converts Jira's complex Atlassian Document Format (ADF) into clean, readable HTML.
- **Attachment Download**: Securely download attachments from Jira issues through the API.
- **Web Interface**: Simple web interface (served via Jinja2 templates) to interact with the API.

## Prerequisites

- Python 3.8+
- A Jira account (Cloud)
- Jira API Token

## Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/alamaticz/Jira-API-Chatbot.git
    cd Jira-API-Chatbot
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Variables:**

    Create a `.env` file in the root directory and add your Jira credentials:

    ```env
    JIRA_DOMAIN=https://your-domain.atlassian.net
    JIRA_EMAIL=your-email@example.com
    JIRA_API_TOKEN=your-jira-api-token
    ```

## Usage

1.  **Run the application:**

    ```bash
    uvicorn app:app --reload
    ```

    The application will proceed to start on `http://127.0.0.1:8000`.

2.  **API Endpoints:**

    -   `GET /`: Renders the home page.
    -   `GET /api/issue/{issue_key}`: Fetches details for a specific issue (e.g., `KAN-15`).
    -   `GET /api/attachment`: Proxy endpoint to download attachments.

## Project Structure

-   `app.py`: Main FastAPI application logic.
-   `templates/`: Directory for HTML templates (Jinja2).
-   `requirements.txt`: Python dependencies.
-   `.env`: Configuration file (excluded from version control).
