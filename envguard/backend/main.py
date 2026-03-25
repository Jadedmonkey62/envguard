import re
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_keys(content: str) -> set:
    keys = set()
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            key = line.split('=', 1)[0].strip()
            keys.add(key)
    return keys

def fetch_github_blueprint(url: str) -> str:
    """Intelligently hunts for the blueprint file from a repo or direct URL."""
    url = url.strip().rstrip("/")
    
    # 1. If it's already a direct raw link, just grab it.
    if "raw.githubusercontent.com" in url:
        resp = requests.get(url)
        if resp.status_code == 200: return resp.text
        raise Exception("Could not fetch the raw file.")
        
    # 2. If it's a direct GitHub file link, convert to raw and grab it.
    if "/blob/" in url:
        raw_url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        resp = requests.get(raw_url)
        if resp.status_code == 200: return resp.text
        raise Exception("Could not fetch the file from the provided GitHub link.")

    # 3. DISCOVERY MODE: If it's just a base repository link
    match = re.match(r"https?://(?:www\.)?github\.com/([^/]+)/([^/]+)", url)
    if match:
        owner = match.group(1)
        repo = match.group(2).replace(".git", "") # Clean up if they pasted a clone link
        
        # We will check the two standard branches and standard filenames
        branches = ["main", "master"]
        filenames = [".env.example", ".env.template", ".env.sample", "env.example"]
        
        for branch in branches:
            for filename in filenames:
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{filename}"
                response = requests.get(raw_url)
                
                # If we get a 200 OK, we found the file! Return it immediately.
                if response.status_code == 200:
                    return response.text
                    
        raise Exception(f"Searched repository '{repo}' but could not find a .env.example or .env.template on 'main' or 'master' branches.")
        
    raise Exception("Invalid GitHub URL format. Please paste a valid repository link.")

@app.post("/api/scan")
async def scan_env_files(
    env_file: UploadFile = File(...),
    template_file: Optional[UploadFile] = File(None),
    github_url: Optional[str] = Form(None)
):
    try:
        template_content = ""
        
        # Use our new Discovery Mode if a URL is provided
        if github_url:
            try:
                template_content = fetch_github_blueprint(github_url)
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        elif template_file and template_file.filename:
            template_content = (await template_file.read()).decode("utf-8")
        else:
            raise HTTPException(status_code=400, detail="You must provide either a blueprint file or a GitHub URL.")

        env_content = (await env_file.read()).decode("utf-8")
        
        required_keys = extract_keys(template_content)
        provided_keys = extract_keys(env_content)
        
        results = []
        missing_count = 0
        
        for key in required_keys:
            if key in provided_keys:
                results.append({"key": key, "status": "✅ Found", "color": "text-green-500"})
            else:
                results.append({"key": key, "status": "❌ Missing", "color": "text-red-500"})
                missing_count += 1
                
        return {
            "is_deployable": missing_count == 0,
            "missing_count": missing_count,
            "scan_results": results
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))