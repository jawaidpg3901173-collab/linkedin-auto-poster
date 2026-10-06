# 🚀 Automated Daily LinkedIn Poster with Gemini AI & GitHub Actions

An automated Python project that generates engaging, high-value LinkedIn posts about **business task automation** using Google Gemini AI and publishes them directly to your personal LinkedIn profile using the LinkedIn Posts API (`/rest/posts`).

The project is fully automated via **GitHub Actions**, scheduled to run every day at **9:00 AM UTC** without needing any hosted server.

---

## 📁 Project Structure

```text
├── .github/
│   └── workflows/
│       └── schedule.yml     # GitHub Actions workflow running daily at 09:00 UTC
├── .env.example             # Template for local environment variables
├── .gitignore               # Ignores venv, pycache, and secrets
├── main.py                  # Core script: calls Gemini & posts to LinkedIn
├── requirements.txt         # Dependencies (google-generativeai, requests, python-dotenv)
└── README.md                # Complete setup and credential instructions
```

---

## 🔑 Step-by-Step Guide: Getting API Keys & Credentials

You need 3 secrets to run this automation:
1. `GEMINI_API_KEY`
2. `LINKEDIN_ACCESS_TOKEN`
3. `PERSON_URN`

Follow the instructions below to obtain each one.

---

### Step 1: Get Your Google Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your Google account.
3. Click the **Get API key** button on the left sidebar.
4. Click **Create API key** (choose a Google Cloud project or create a default one).
5. Copy your API key and keep it safe.

---

### Step 2: Get Your LinkedIn Developer Credentials

Posting directly to a personal LinkedIn profile via API requires an active LinkedIn Developer App and an OAuth 2.0 user access token.

#### 2.1. Create a LinkedIn App
1. Go to the [LinkedIn Developer Portal](https://developer.linkedin.com/).
2. Click **My Apps** in the top navigation, then click **Create app**.
3. Fill in the required fields:
   - **App name**: (e.g., `Daily Post Automation`)
   - **LinkedIn Page**: Link an existing LinkedIn company/business page. If you don't have one, [create a free LinkedIn Page](https://www.linkedin.com/company/setup/new/) in 2 minutes (LinkedIn requires an app to be tied to a page).
   - **Privacy policy URL**: Enter your repository URL or a placeholder webpage.
   - **App logo**: Upload any square image.
4. Check the legal terms and click **Create app**.

#### 2.2. Request Required Products
In your app's dashboard:
1. Navigate to the **Products** tab.
2. Find and request access to:
   - **Share on LinkedIn** (Provides `w_member_social` permission to publish posts to your personal profile).
   - **Sign In with LinkedIn using OpenID Connect** (Provides `openid`, `profile`, and `email` permissions to fetch your personal account URN).
3. These permissions are typically approved automatically within a few moments.

#### 2.3. Generate an OAuth 2.0 Access Token
The quickest and easiest way to get an access token without building an OAuth server is using LinkedIn's official **OAuth 2.0 Tools**:

1. In the LinkedIn Developer Portal, go to **Tools** > **OAuth 2.0 Tools** (or visit [linkedin.com/developers/tools/oauth](https://www.linkedin.com/developers/tools/oauth)).
2. Click **Create token**.
3. Select the App you just created from the dropdown.
4. Select the following scopes:
   - `w_member_social`
   - `openid`
   - `profile`
5. Click **Request access token**.
6. A popup window will prompt you to authorize your app with your personal LinkedIn account. Click **Allow**.
7. Once authorized, copy the generated **Access Token**.

> [!NOTE]  
> LinkedIn OAuth 2.0 user tokens generated this way are valid for **60 days**. When your token expires, simply generate a new token via the OAuth 2.0 tool and update the GitHub secret.

#### 2.4. Find Your `PERSON_URN`
Your Person URN is your unique LinkedIn profile identifier. With your new Access Token, retrieve it by making a quick API request:

##### Option A: Using cURL (Terminal / macOS / Linux / Git Bash)
```bash
curl -X GET "https://api.linkedin.com/v2/userinfo" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

##### Option B: Using Windows PowerShell
```powershell
$token = "YOUR_ACCESS_TOKEN"
Invoke-RestMethod -Uri "https://api.linkedin.com/v2/userinfo" -Headers @{ Authorization = "Bearer $token" }
```

##### Option C: Using Python
```python
import requests
res = requests.get("https://api.linkedin.com/v2/userinfo", headers={"Authorization": "Bearer YOUR_ACCESS_TOKEN"})
print("Your Person ID is:", res.json().get("sub"))
```

In the JSON response, look for the `"sub"` field:
```json
{
  "sub": "abc123XYZ",
  "name": "Jane Doe",
  "email": "jane@example.com"
}
```
The value of `sub` (e.g. `abc123XYZ`) is your LinkedIn Person identifier. You can supply either:
- The raw ID: `abc123XYZ`
- Or the full URN: `urn:li:person:abc123XYZ`

`main.py` automatically handles either format.

---

## 🔒 Step 3: Add Credentials to GitHub Repository Secrets

Now connect your keys to GitHub so the automated workflow can read them securely:

1. Push this project to your GitHub repository (either public or private).
2. Go to your repository page on GitHub.
3. Click on the **Settings** tab (gear icon at the top right of the repo).
4. In the left-hand sidebar, navigate to **Secrets and variables** > **Actions**.
5. Under **Repository secrets**, click the green **New repository secret** button.
6. Create the following three secrets one by one:

| Secret Name | Value |
| :--- | :--- |
| `GEMINI_API_KEY` | Your Google Gemini API key from Google AI Studio |
| `LINKEDIN_ACCESS_TOKEN` | The 60-day OAuth 2.0 user access token |
| `PERSON_URN` | Your LinkedIn Person ID from the `sub` field (e.g., `abc123XYZ` or `urn:li:person:abc123XYZ`) |

Click **Add secret** for each.

---

## ⚙️ Step 4: Verify and Run the Automation

### 1. Manual Test Run via GitHub Actions
Before waiting for the schedule, you can test immediately:
1. Go to the **Actions** tab in your GitHub repository.
2. In the left sidebar, click **Daily LinkedIn Post**.
3. Click the **Run workflow** dropdown on the right side and select **Run workflow**.
4. Click on the running job to watch real-time logs:
   - Gemini generating the post.
   - A preview of the post in the console logs.
   - Successful publication to LinkedIn (`Status Code: 201`).
5. Open your LinkedIn feed to see your new post live!

### 2. Scheduled Daily Execution
The workflow is configured in `.github/workflows/schedule.yml`:
```yaml
on:
  schedule:
    - cron: '0 9 * * *' # Every day at 9:00 AM UTC
```
GitHub Actions will automatically wake up and publish your post every day at **9:00 AM UTC**.

---

## 💻 Local Development & Testing

If you want to test or run the script on your local machine:

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd linkedin-auto-poster
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up `.env` file:**
   Create a `.env` file in the root directory (based on `.env.example`):
   ```env
   GEMINI_API_KEY="your-gemini-api-key"
   LINKEDIN_ACCESS_TOKEN="your-access-token"
   PERSON_URN="your-person-urn-id"
   ```

5. **Run the script:**
   ```bash
   python main.py
   ```

---

## 🛠 Troubleshooting

- **Error: `Invalid access token` (Status Code 401)**:
  - Your access token may have expired or was copied with trailing whitespace. Generate a new token using LinkedIn OAuth 2.0 Tools and update `LINKEDIN_ACCESS_TOKEN`.
- **Error: `Not enough permissions to access: POST /rest/posts` (Status Code 403)**:
  - Verify that your token has the `w_member_social` scope checked.
- **Error: `author: urn:li:person:... is invalid` (Status Code 400/422)**:
  - Make sure the `PERSON_URN` is the `sub` ID belonging to the user account that authorized the access token.
- **Scheduled workflow not running on GitHub**:
  - GitHub disables scheduled workflows on inactive repositories after 60 days of no commits. Simply trigger a manual run to keep it active.
