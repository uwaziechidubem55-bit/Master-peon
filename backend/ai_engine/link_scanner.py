import re
import json
import html as html_mod
import httpx
from urllib.parse import urljoin, quote
from config.settings import settings

GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", re.I)
GITLAB_RE = re.compile(r"(?:https?://)?(?:www\.)?gitlab\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", re.I)
OWNER_REPO_RE = re.compile(r"\b([A-Za-z0-9][A-Za-z0-9_.-]{0,38})/([A-Za-z0-9][A-Za-z0-9_.-]{0,38})\b")
URL_RE = re.compile(r"https?://[^\s]+")
BARE_DOMAIN_RE = re.compile(r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}(?::\d+)?\b", re.I)
SCAN_INTENT = [
    "scan", "inspect", "analyze", "review", "look at", "check",
    "read", "open", "fetch", "summarize", "summary", "what is in",
    "visit", "browse", "go to", "check out", "see",
]
WEB_WORDS = ["website", "site", "web page", "webpage", "page", "url", "link", "online", "browser"]
TOOL_NAMES = [
    "nmap", "nikto", "sqlmap", "hydra", "hashcat", "tcpdump", "dirb", "ffuf",
    "whatweb", "sublist3r", "netcat", "tshark", "whois", "medusa", "crunch",
    "routersploit", "burp", "metasploit", "netdiscover", "linpeas", "winpeas",
    "pspy", "chisel", "ligolo", "john", "gobuster", "nuclei", "wpscan", "masscan",
]
KEY_FILES = [
    "README.md", "README", "requirements.txt", "package.json",
    "docker-compose.yml", "Dockerfile", ".env.example", "pyproject.toml",
    "setup.py", "main.py", "app.py", "manage.py", "index.js",
    "Caddyfile", "nginx.conf", "LICENSE",
]
MAX_FILE_CHARS = 1200
MAX_KEY_FILES = 8
MAX_TREE_ITEMS = 60
MAX_TEXT_CHARS = 1800
MAX_JSON_CHARS = 2500

def detect(message: str) -> bool:
    low = message.lower()
    if any(t in low for t in TOOL_NAMES):
        return False
    if GITHUB_RE.search(message) or GITLAB_RE.search(message):
        return True
    if ("github" in low or "gitlab" in low or "repo" in low or "repository" in low) and OWNER_REPO_RE.search(message):
        return True
    urls = URL_RE.findall(message)
    if urls and any(i in low for i in SCAN_INTENT):
        return True
    if urls and _mostly_url(message):
        return True
    if BARE_DOMAIN_RE.search(message) and any(w in low for w in WEB_WORDS) and any(i in low for i in SCAN_INTENT):
        return True
    return False

def _mostly_url(message: str) -> bool:
    rest = URL_RE.sub("", message)
    rest = re.sub(r"\s+", "", rest)
    return len(rest) < 10

def _strip_html(text: str) -> str:
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html_mod.unescape(text)
    return re.sub(r"[ \t]+", " ", text)

def _headers():
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "master-peon"}
    if settings.github_token:
        headers["Authorization"] = "Bearer " + settings.github_token
    return headers

def _parse_github(message: str):
    m = GITHUB_RE.search(message)
    if not m:
        return None
    owner, repo = m.group(1), m.group(2).rstrip("/")
    branch, path = None, None
    blob = re.search(r"/blob/([^/\s]+)/([^\s]+)", message)
    if blob:
        branch, path = blob.group(1), blob.group(2)
    return {"owner": owner, "repo": repo, "branch": branch, "path": path}

async def _scan_github(owner: str, repo: str) -> dict:
    api = "https://api.github.com"
    async with httpx.AsyncClient(timeout=30.0, headers=_headers(), follow_redirects=True) as client:
        try:
            meta_r = await client.get(api + "/repos/" + owner + "/" + repo)
            meta_r.raise_for_status()
            meta = meta_r.json()
        except Exception as e:
            return {"reply": "GitHub repo scan failed: " + str(e)}
        branch = meta.get("default_branch") or "main"
        tree = []
        try:
            tree_r = await client.get(api + "/repos/" + owner + "/" + repo + "/git/trees/" + branch,
                                      params={"recursive": "1"})
            tree_r.raise_for_status()
            tree = tree_r.json().get("tree", [])
        except Exception:
            tree = []
    files = [t["path"] for t in tree if t.get("type") == "blob"]
    dirs = [t["path"] for t in tree if t.get("type") == "tree"]
    ext_count = {}
    for f in files:
        leaf = f.rsplit("/", 1)[-1]
        if "." in leaf:
            ext = leaf.rsplit(".", 1)[-1].lower()
            ext_count[ext] = ext_count.get(ext, 0) + 1
    top_ext = ", ".join(k + " (" + str(v) + ")" for k, v in sorted(ext_count.items(), key=lambda x: -x[1])[:6])
    key_files = [f for f in KEY_FILES if f in files]
    if len(key_files) < 3:
        for f in files:
            if f not in key_files and len(key_files) < MAX_KEY_FILES:
                key_files.append(f)
    key_files = key_files[:MAX_KEY_FILES]
    snippets = []
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for kf in key_files:
            try:
                raw_r = await client.get("https://raw.githubusercontent.com/" + owner + "/" + repo + "/" + branch + "/" + kf)
                if raw_r.status_code == 200:
                    content = raw_r.text
                    if len(content) > MAX_FILE_CHARS:
                        content = content[:MAX_FILE_CHARS] + "\n...truncated"
                    snippets.append(kf + ":\n" + content)
            except Exception:
                continue
    lines = [
        "GitHub repo scan: " + owner + "/" + repo,
        "Branch: " + branch,
        "Description: " + (meta.get("description") or "none"),
        "Language: " + (meta.get("language") or "unknown"),
        "Stars: " + str(meta.get("stargazers_count", 0)),
        "Size: " + str(round((meta.get("size") or 0) / 1024, 2)) + " MB",
        "Total files: " + str(len(files)),
        "Total folders: " + str(len(dirs)),
        "Top extensions: " + (top_ext or "none"),
    ]
    tree_lines = [t["path"] for t in tree][:MAX_TREE_ITEMS]
    if tree_lines:
        lines.append("File tree (first " + str(len(tree_lines)) + "):")
        lines.extend(tree_lines)
    if snippets:
        lines.append("Key files:")
        lines.extend(snippets)
    return {"reply": "\n".join(lines)}

async def _scan_github_file(owner: str, repo: str, branch: str, path: str) -> dict:
    url = "https://raw.githubusercontent.com/" + owner + "/" + repo + "/" + branch + "/" + path
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=_headers()) as client:
            r = await client.get(url)
            r.raise_for_status()
            content = r.text
    except Exception as e:
        return {"reply": "GitHub file scan failed: " + str(e)}
    if len(content) > MAX_FILE_CHARS:
        content = content[:MAX_FILE_CHARS] + "\n...truncated"
    return {"reply": "GitHub file scan: " + owner + "/" + repo + "/" + path + "\n" + content}

async def _scan_gitlab(owner: str, repo: str) -> dict:
    api = "https://gitlab.com/api/v4"
    proj = quote(owner + "/" + repo, safe="")
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            meta_r = await client.get(api + "/projects/" + proj)
            meta_r.raise_for_status()
            meta = meta_r.json()
            branch = meta.get("default_branch") or "main"
            tree_r = await client.get(api + "/projects/" + proj + "/repository/tree",
                                      params={"ref": branch, "recursive": "true", "per_page": "100"})
            tree = tree_r.json() if tree_r.status_code == 200 else []
            readme_r = await client.get("https://gitlab.com/" + owner + "/" + repo + "/-/raw/" + branch + "/README.md")
            readme = readme_r.text if readme_r.status_code == 200 else ""
    except Exception as e:
        return {"reply": "GitLab scan failed: " + str(e)}
    files = [t["path"] for t in tree if t.get("type") == "blob"]
    lines = [
        "GitLab repo scan: " + owner + "/" + repo,
        "Branch: " + branch,
        "Description: " + (meta.get("description") or "none"),
        "Language: " + (meta.get("name_with_namespace") or "unknown"),
        "Stars: " + str(meta.get("star_count", 0)),
        "Total files listed: " + str(len(files)),
    ]
    tree_lines = [t["path"] for t in tree][:MAX_TREE_ITEMS]
    if tree_lines:
        lines.append("File tree (first " + str(len(tree_lines)) + "):")
        lines.extend(tree_lines)
    if readme:
        if len(readme) > MAX_FILE_CHARS:
            readme = readme[:MAX_FILE_CHARS] + "\n...truncated"
        lines.append("README.md:")
        lines.append(readme)
    return {"reply": "\n".join(lines)}

def _parse_html(r, url: str) -> dict:
    body = r.text
    title_m = re.search(r"(?is)<title[^>]*>(.*?)</title>", body)
    title = re.sub(r"\s+", " ", title_m.group(1)).strip() if title_m else "none"
    desc_m = re.search(r'(?is)<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', body)
    desc = re.sub(r"\s+", " ", desc_m.group(1)).strip() if desc_m else "none"
    headings = re.findall(r"(?is)<h[1-3][^>]*>(.*?)</h[1-3]>", body)
    headings = [re.sub(r"(?s)<[^>]+>", "", h).strip() for h in headings]
    headings = [re.sub(r"\s+", " ", h) for h in headings if h.strip()][:10]
    text = _strip_html(body)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) > MAX_TEXT_CHARS:
        text = text[:MAX_TEXT_CHARS] + "\n...truncated"
    links = re.findall(r'(?is)<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', body)
    out_links = []
    seen = set()
    for href, anchor in links:
        href = href.strip()
        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        abs_url = urljoin(url, href)
        if abs_url in seen:
            continue
        seen.add(abs_url)
        a = re.sub(r"(?s)<[^>]+>", "", anchor).strip()
        a = re.sub(r"\s+", " ", a)[:60]
        out_links.append((a or abs_url, abs_url))
        if len(out_links) >= 15:
            break
    parts = [
        "Link scan: " + str(r.url),
        "Status: " + str(r.status_code),
        "Content-Type: " + (r.headers.get("content-type") or "unknown"),
        "Title: " + title,
        "Description: " + desc[:300],
    ]
    if headings:
        parts.append("Headings:")
        parts.extend("  " + h[:120] for h in headings)
    parts.append("Page text preview:")
    parts.append(text)
    if out_links:
        parts.append("Links found (" + str(len(out_links)) + "):")
        parts.extend("  " + (a + " -> " + u if a and a != u else u) for a, u in out_links)
    return {"reply": "\n".join(parts)}

async def _scan_url(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            r = await client.get(url)
            ctype = (r.headers.get("content-type") or "").lower()
    except Exception as e:
        return {"reply": "Link scan failed: " + str(e)}
    size = len(r.content)
    if r.status_code >= 400:
        return {"reply": "Link scan: " + url + "\nStatus: " + str(r.status_code) + "\nCould not fetch this link (error)."}
    if "text/html" in ctype:
        return _parse_html(r, url)
    if "application/json" in ctype or url.endswith(".json"):
        text = r.text
        try:
            parsed = json.loads(text)
            text = json.dumps(parsed, indent=2)
        except Exception:
            pass
        if len(text) > MAX_JSON_CHARS:
            text = text[:MAX_JSON_CHARS] + "\n...truncated"
        return {"reply": "Link scan: " + url + "\nContent-Type: " + ctype + "\nJSON preview:\n" + text}
    if "pdf" in ctype:
        return {"reply": "Link scan: " + url + "\nContent-Type: " + ctype + "\nSize: " + str(round(size / 1024)) + " KB\nPDF detected - text extraction needs extra packages, not installed."}
    if ctype.startswith("image/"):
        return {"reply": "Link scan: " + url + "\nContent-Type: " + ctype + "\nSize: " + str(round(size / 1024)) + " KB\nImage detected - cannot read image content."}
    text = r.text
    if len(text) > MAX_TEXT_CHARS:
        text = text[:MAX_TEXT_CHARS] + "\n...truncated"
    return {"reply": "Link scan: " + url + "\nContent-Type: " + ctype + "\nPreview:\n" + text}

async def scan_message(message: str):
    if not detect(message):
        return None
    gh = _parse_github(message)
    if gh:
        if gh["branch"] and gh["path"]:
            return await _scan_github_file(gh["owner"], gh["repo"], gh["branch"], gh["path"])
        return await _scan_github(gh["owner"], gh["repo"])
    gl = GITLAB_RE.search(message)
    if gl:
        return await _scan_gitlab(gl.group(1), gl.group(2).rstrip("/"))
    urls = URL_RE.findall(message)
    if urls:
        return await _scan_url(urls[0].rstrip(".,;:)]}\"'"))
    m = BARE_DOMAIN_RE.search(message)
    if m:
        return await _scan_url("https://" + m.group(0))
    return None

SEARCH_INTENT_RE = re.compile(r"^(?:search the web for|search online for|web search for|search for|search|google|look up|find online|find information about|find)\s*:?\s*(.+)$", re.I)

def detect_search(message: str) -> bool:
    if detect(message):
        return False
    return bool(SEARCH_INTENT_RE.match(message.strip()))

async def web_search(message: str) -> dict:
    if not settings.brave_api_key:
        return {"reply": "Web search not configured. Add a free Brave Search API key (BRAVE_API_KEY) to .env - https://api.search.brave.com"}
    m = SEARCH_INTENT_RE.match(message.strip())
    if not m:
        return {"reply": "Tell me what to search for, e.g. 'search the web for latest nmap cve'."}
    query = m.group(1).strip().strip("\"'").strip()
    if not query:
        return {"reply": "Tell me what to search for."}
    try:
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            r = await client.get("https://api.search.brave.com/res/v1/web/search",
                                 params={"q": query, "count": 5, "safesearch": "off"},
                                 headers={"X-Subscription-Token": settings.brave_api_key, "Accept": "application/json"})
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        return {"reply": "Web search failed: " + str(e)}
    results = data.get("web", {}).get("results", [])
    if not results:
        return {"reply": "No results for: " + query}
    lines = ["Web search results for: " + query]
    for i, res in enumerate(results[:5], 1):
        lines.append(str(i) + ". " + res.get("title", ""))
        lines.append("   " + res.get("url", ""))
        lines.append("   " + (res.get("description") or "")[:250])
    return {"reply": "\n".join(lines)}