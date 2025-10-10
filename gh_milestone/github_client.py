"""
GitHub API client module for issue creation and management.
"""

import os
import sys
import subprocess
from typing import List, Tuple
from github import Github, Auth
from .config import Config


class GitHubClient:
    """Client for interacting with GitHub API."""
    
    def __init__(self, explicit_repo: str = None):
        """Initialize GitHub client with authentication."""
        self.client = self._get_authenticated_client()
        self.explicit_repo = explicit_repo
    
    def _get_authenticated_client(self) -> Github:
        """Get authenticated GitHub client."""
        # Try to get token from environment variable first
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            # Try to get token from gh CLI config
            try:
                result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True)
                token = result.stdout.strip()
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("❌ GitHub authentication required.")
                print("Please set GITHUB_TOKEN environment variable or authenticate with 'gh auth login'")
                sys.exit(1)

        # Ensure we have a valid token
        if not token:
            print("❌ GitHub authentication required.")
            print("Please set GITHUB_TOKEN environment variable or authenticate with 'gh auth login'")
            sys.exit(1)

        auth = Auth.Token(token)
        return Github(auth=auth)
    
    def create_issue(self, title: str, body: str = "", labels: List[str] = None) -> Tuple[str, int]:
        """Create a GitHub issue and return its URL and issue number."""
        repo_name = Config.get_repo_name(self.explicit_repo)
        if not repo_name:
            print("❌ Repository name could not be determined. Please provide --repo option or run within a git repository with a GitHub remote.")
            sys.exit(1)

        repo = self.client.get_repo(repo_name)

        # Create the issue
        issue = repo.create_issue(
            title=title,
            body=body,
            labels=labels or []
        )

        print(f"Created issue: {title} (#{issue.number})")
        return issue.html_url, issue.number
    
    def delete_issue(self, issue_number: int):
        """Delete a GitHub issue by issue number."""
        repo_name = Config.get_repo_name(self.explicit_repo)
        if not repo_name:
            print("❌ Repository name could not be determined. Please provide --repo option or run within a git repository with a GitHub remote.")
            sys.exit(1)

        # Use the GitHub REST API directly to delete issue
        # DELETE /repos/{owner}/{repo}/issues/{issue_number}
        try:
            self.client._Github__requester.requestJsonAndCheck(
                "DELETE",
                f"/repos/{repo_name}/issues/{issue_number}"
            )
            print(f"Deleted issue #{issue_number}")
        except Exception as e:
            print(f"Error deleting issue #{issue_number}: {e}")
            sys.exit(1)
    
    def link_sub_issue(self, parent_issue_num: int, sub_issue_num: int):
        """Link a sub-issue to its parent issue using the GitHub sub-issues API."""
        repo_name = Config.get_repo_name(self.explicit_repo)
        if not repo_name:
            print("❌ Repository name could not be determined. Please provide --repo option or run within a git repository with a GitHub remote.")
            sys.exit(1)

        # Use the GitHub REST API directly to add sub-issue
        # POST /repos/{owner}/{repo}/issues/{issue_number}/sub_issues
        try:
            # First get the issues to obtain their IDs (required for linking)
            repo = self.client.get_repo(repo_name)
            parent_issue = repo.get_issue(parent_issue_num)
            sub_issue = repo.get_issue(sub_issue_num)
            
            # Use the correct endpoint with issue IDs
            self.client._Github__requester.requestJsonAndCheck(
                "POST",
                f"/repos/{repo_name}/issues/{parent_issue.number}/sub_issues",
                input={"sub_issue_id": sub_issue.id}
            )
            print(f"Linked issue #{sub_issue_num} to parent #{parent_issue_num}")
        except Exception as e:
            print(f"Error linking sub-issue #{sub_issue_num} to parent #{parent_issue_num}: {e}")
            sys.exit(1)
    
    def unlink_sub_issue(self, parent_issue_num: int, sub_issue_num: int):
        """Unlink a sub-issue from its parent issue using the GitHub sub-issues API."""
        repo_name = Config.get_repo_name(self.explicit_repo)
        if not repo_name:
            print("❌ Repository name could not be determined. Please provide --repo option or run within a git repository with a GitHub remote.")
            sys.exit(1)

        # Use the GitHub REST API directly to remove sub-issue relationship
        # DELETE /repos/{owner}/{repo}/issues/{issue_number}/sub_issues/{sub_issue_number}
        try:
            self.client._Github__requester.requestJsonAndCheck(
                "DELETE",
                f"/repos/{repo_name}/issues/{parent_issue_num}/sub_issues/{sub_issue_num}"
            )
            print(f"Unlinked issue #{sub_issue_num} from parent #{parent_issue_num}")
        except Exception as e:
            print(f"Error unlinking sub-issue #{sub_issue_num} from parent #{parent_issue_num}: {e}")
            sys.exit(1)
    
    def update_issue(self, issue_number: int, title: str = None, body: str = None, labels: List[str] = None):
        """Update a GitHub issue's title, body, and/or labels."""
        repo_name = Config.get_repo_name(self.explicit_repo)
        if not repo_name:
            print("❌ Repository name could not be determined. Please provide --repo option or run within a git repository with a GitHub remote.")
            sys.exit(1)

        # Prepare update parameters - only include non-None values
        update_params = {}
        if title is not None:
            update_params['title'] = title
        if body is not None:
            update_params['body'] = body
        if labels is not None:
            update_params['labels'] = labels

        # If no parameters to update, exit early
        if not update_params:
            print(f"No updates provided for issue #{issue_number}")
            return

        try:
            repo = self.client.get_repo(repo_name)
            issue = repo.get_issue(issue_number)
            issue.edit(**update_params)
            print(f"Updated issue #{issue_number}")
        except Exception as e:
            print(f"Error updating issue #{issue_number}: {e}")
            sys.exit(1)
    
    def get_issue(self, issue_number: int):
        """Retrieve a GitHub issue by its number."""
        repo_name = Config.get_repo_name(self.explicit_repo)
        if not repo_name:
            print("❌ Repository name could not be determined. Please provide --repo option or run within a git repository with a GitHub remote.")
            sys.exit(1)

        try:
            repo = self.client.get_repo(repo_name)
            issue = repo.get_issue(issue_number)
            return issue
        except Exception as e:
            print(f"Error retrieving issue #{issue_number}: {e}")
            sys.exit(1)
