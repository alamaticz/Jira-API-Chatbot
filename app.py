from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import os
import io

load_dotenv()

JIRA_DOMAIN = os.getenv("JIRA_DOMAIN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
headers = {"Accept": "application/json"}

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with specific Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/issue/{issue_key}")
def get_issue(issue_key: str):
    url = f"{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}"

    response = requests.get(url, headers=headers, auth=auth)

    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Issue not found or access denied")

    issue = response.json()
    fields = issue["fields"]

    data = {
        "key": issue["key"],
        "summary": fields.get("summary"),
        "description": render_adf_to_html(fields.get("description")),
        "status": fields["status"]["name"],
        "priority": fields["priority"]["name"] if fields.get("priority") else None,
        "assignee": fields["assignee"]["displayName"] if fields.get("assignee") else "Unassigned",
        "issue_type": fields["issuetype"]["name"],
        "created": fields["created"],
        "updated": fields["updated"],
        "subtasks": [
            {
                "key": s["key"],
                "summary": s["fields"]["summary"],
                "status": s["fields"]["status"]["name"]
            } for s in fields.get("subtasks", [])
        ],
        "attachments": [
            {
                "filename": a["filename"],
                "url": a["content"],
                "size": a["size"]
            } for a in fields.get("attachment", [])
        ],
        "comments": [
            {
                "author": c["author"]["displayName"],
                "body": render_adf_to_html(c["body"]),
                "created": c["created"]
            } for c in fields["comment"]["comments"]
        ]
    }

    return JSONResponse(data)


@app.get("/api/attachment")
def download_attachment(url: str, filename: str = None):
    """
    Downloads Jira attachment using backend credentials
    """
    response = requests.get(
        url,
        auth=auth,
        headers={"Accept": "*/*"},
        stream=True
    )

    if response.status_code != 200:
        raise HTTPException(status_code=403, detail="No permission to download attachment")

    file_stream = io.BytesIO(response.content)

    if not filename:
        filename = url.split("/")[-1]

    return StreamingResponse(
        file_stream,
        media_type=response.headers.get("Content-Type", "application/octet-stream"),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


def render_adf_to_html(adf_node):
    """
    Converts Jira ADF (Atlassian Document Format) to HTML
    """
    if not adf_node:
        return ""

    # If it's the root node (doc), just process its content
    if "version" in adf_node and "content" in adf_node:
        # This is likely the root 'doc' object
        return "".join(render_adf_to_html(c) for c in adf_node.get("content", []))

    node_type = adf_node.get("type")
    content = adf_node.get("content", [])
    
    # Process child content
    inner_html = "".join(render_adf_to_html(c) for c in content)

    if node_type == "paragraph":
        return f"<p>{inner_html}</p>"
    
    elif node_type == "heading":
        level = adf_node.get("attrs", {}).get("level", 3)
        return f"<h{level}>{inner_html}</h{level}>"
    
    elif node_type == "text":
        text = adf_node.get("text", "")
        for mark in adf_node.get("marks", []):
            m_type = mark.get("type")
            if m_type == "strong":
                text = f"<strong>{text}</strong>"
            elif m_type == "em":
                text = f"<em>{text}</em>"
            elif m_type == "code":
                text = f"<code>{text}</code>"
            elif m_type == "strike":
                text = f"<s>{text}</s>"
            elif m_type == "underline":
                text = f"<u>{text}</u>"
            elif m_type == "link":
                href = mark.get("attrs", {}).get("href", "#")
                text = f'<a href="{href}" target="_blank">{text}</a>'
            elif m_type == "textColor":
                color = mark.get("attrs", {}).get("color", "inherit")
                text = f'<span style="color: {color}">{text}</span>'
        return text

    elif node_type == "bulletList":
        return f"<ul>{inner_html}</ul>"
    
    elif node_type == "orderedList":
        return f"<ol>{inner_html}</ol>"
    
    elif node_type == "listItem":
        return f"<li>{inner_html}</li>"
    
    elif node_type == "codeBlock":
        code_text = ""
        # codeBlock usually contains text nodes directly or content
        for c in content:
            if c.get("type") == "text":
                code_text += c.get("text", "")
        return f"<pre><code>{code_text}</code></pre>"
    
    elif node_type == "blockquote":
        return f"<blockquote>{inner_html}</blockquote>"
        
    elif node_type == "rule":
        return "<hr/>"
    
    elif node_type == "hardBreak":
        return "<br/>"

    # Default fallback: return inner content if any, or empty string
    return inner_html
