import os
import subprocess
import requests
import json

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AZURE_API_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT") 

HEADERS = {
    "Content-Type": "application/json",
    "api-key": OPENAI_API_KEY
}

# Comparing the diff between the base and head branches
# Return the diff in the two branches
def get_diff(base_branch, head_branch):
    try:
        diff = subprocess.check_output(
            ["git", "diff", f"origin/{base_branch}...origin/{head_branch}", "--name-status", "--no-color"]
        ).decode("utf-8")

        #Debugging output
        print("*** Diff : ", diff)

        return diff.strip()
    except subprocess.CalledProcessError as e:
        print("Error fetching diff:", e)
        return ""


prompt_text = """

Write a professional GitHub Pull Request description for a code change comparing 
the current branch to base branch you will get the differents in git diff to analyze 
place, using the provided git diff output, and adhering to the following guidelines:

* Clearly explain the changes made, including the purpose and impact of each change.
* Identify and list the **files changed**.
* Highlight the **impacted areas or modules**.
* Organize changes by purpose (e.g., bug fix, refactor, optimization).
* Use markdown formatting (e.g., bullet points, bold headers).
* Follow the provided structure:

### Description
In this PR, I [Clearly describe the changes, including their purpose and impact].

* [List changes by purpose, using bullet points]

### Files Changed
* [List the files changed]

Git Diff to Analyze:

"""

# Generate a description for the PR using the OpenAI API
def generate_description(diff):
    prompt = f""" {prompt_text} {diff} Please provide the git diff output to analyze."""
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that writes GitHub PR descriptions."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 700
    }
    print("Headers: ", HEADERS)
    response = requests.post(AZURE_API_ENDPOINT, headers=HEADERS, data=json.dumps(payload))
    return response.json()["choices"][0]["message"]["content"].strip() if response.status_code == 200 else ""


# Update the GitHub PR description using the GitHub API
def update_github_pr(pr_number, body):

    github_token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("REPO_NAME")
    
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    payload = {"body": body}
    
    response = requests.patch(
        url, headers=headers, 
        data=json.dumps(payload)
    )
    
    if response.status_code == 200:
        print("PR description updated successfully.")
    else:
        print(f"Failed to update PR description: {response.status_code} - {response.text}")
    



# Main function to execute the script
if __name__ == "__main__":
    base = os.getenv("BASE_BRANCH")
    head = os.getenv("HEAD_BRANCH")
    pr_number = os.getenv("PR_NUMBER")

    # Check and store the diff between the base and head branches in diff variable
    diff = get_diff(base, head)

    # If diff is not empty, generate the description and update the PR
    # Otherwise, print a message indicating no diff was found
    if diff:
        description = generate_description(diff)
        update_github_pr(pr_number, description)
    else:
        print("No diff found.")
