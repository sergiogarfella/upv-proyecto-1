#!/usr/bin/env python3
"""
GitHub API Client for Gantt Chart Generator
Extracts issues and milestones from GitHub repositories, specifically querying for Projects V2 fields
"""

import os
import requests
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin


@dataclass
class GitHubIssue:
    """Represents a GitHub issue"""
    id: int
    number: int
    title: str
    state: str
    created_at: str
    updated_at: str
    closed_at: Optional[str]
    labels: List[str]
    assignees: List[str]
    milestone: Optional[str]
    body: Optional[str]
    url: str
    
    # Custom Projects V2 Fields
    priority: Optional[str] = None
    early_start: Optional[str] = None
    early_finish: Optional[str] = None
    late_start: Optional[str] = None
    late_finish: Optional[str] = None
    estimated_duration: Optional[float] = None
    parent_number: Optional[int] = None
    blocking: Optional[List[int]] = None
    blocked_by: Optional[List[int]] = None


@dataclass
class GitHubMilestone:
    """Represents a GitHub milestone (Sprint)"""
    id: int
    number: int
    title: str
    state: str
    description: Optional[str]
    due_on: Optional[str]
    created_at: str
    updated_at: str
    closed_at: Optional[str]
    open_issues: int
    closed_issues: int
    
    @property
    def total_issues(self) -> int:
        return self.open_issues + self.closed_issues


class GitHubAPI:
    """GitHub API client for repository data extraction"""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub API client
        
        Args:
            token: GitHub Personal Access Token (optional, but recommended for higher rate limits and required for GraphQL)
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        })
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """Make GET request to GitHub API"""
        url = urljoin(self.BASE_URL, endpoint)
        response = self.session.get(url, params=params)
        
        if response.status_code == 403:
            raise Exception("Rate limit exceeded. Please provide a GitHub token.")
        
        response.raise_for_status()
        return response.json()
    
    def get_issues(self, owner: str, repo: str, state: str = "all", 
                   per_page: int = 100, max_pages: int = 10) -> List[GitHubIssue]:
        """
        Fetch all issues from a repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state (open, closed, all)
            per_page: Items per page
            max_pages: Maximum pages to fetch
        """
        issues = []
        page = 1
        
        while page <= max_pages:
            params = {
                "state": state,
                "per_page": per_page,
                "page": page
            }
            
            data = self._get(f"/repos/{owner}/{repo}/issues", params)
            
            if not data:
                break
            
            for item in data:
                # Skip pull requests (they appear as issues in the API)
                if "pull_request" in item:
                    continue
                    
                issue = GitHubIssue(
                    id=item["id"],
                    number=item["number"],
                    title=item["title"],
                    state=item["state"],
                    created_at=item["created_at"],
                    updated_at=item["updated_at"],
                    closed_at=item.get("closed_at"),
                    labels=[label["name"] for label in item.get("labels", [])],
                    assignees=[a["login"] for a in item.get("assignees", [])],
                    milestone=item["milestone"]["title"] if item.get("milestone") else None,
                    body=item.get("body"),
                    url=item["html_url"]
                )
                issues.append(issue)
            
            if len(data) < per_page:
                break
            
            page += 1
        
        # Fetch project fields for these issues via GraphQL if token is available
        if self.token and issues:
            self._enrich_issues_with_project_fields(owner, repo, issues)
            
        return issues
        
    def _enrich_issues_with_project_fields(self, owner: str, repo: str, issues: List[GitHubIssue]):
        """Enrich existing issues with Projects V2 custom fields using GraphQL"""
        query = """
        query($owner: String!, $repo: String!, $cursor: String) {
          repository(owner: $owner, name: $repo) {
            issues(first: 100, after: $cursor) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                number
                parent {
                  number
                }
                projectItems(first: 10) {
                  nodes {
                    fieldValues(first: 20) {
                      nodes {
                        ... on ProjectV2ItemFieldDateValue {
                          date
                          field {
                            ... on ProjectV2FieldCommon { name }
                          }
                        }
                        ... on ProjectV2ItemFieldNumberValue {
                          number
                          field {
                            ... on ProjectV2FieldCommon { name }
                          }
                        }
                        ... on ProjectV2ItemFieldTextValue {
                          text
                          field {
                            ... on ProjectV2FieldCommon { name }
                          }
                        }
                        ... on ProjectV2ItemFieldSingleSelectValue {
                          name
                          field {
                            ... on ProjectV2FieldCommon { name }
                          }
                        }
                      }
                    }
                  }
                }
                trackedInIssues(first: 10) {
                  nodes {
                    number
                  }
                }
                blocking(first: 10) {
                  nodes {
                    number
                  }
                }
                blockedBy(first: 10) {
                  nodes {
                    number
                  }
                }
              }
            }
          }
        }
        """
        
        issue_map = {issue.number: issue for issue in issues}
        has_next_page = True
        cursor = None
        
        try:
            while has_next_page:
                variables = {"owner": owner, "repo": repo, "cursor": cursor}
                response = self.session.post(
                    "https://api.github.com/graphql",
                    json={"query": query, "variables": variables}
                )
                
                if response.status_code != 200:
                    print(f"Failed to fetch GraphQL project fields: {response.text}")
                    break
                    
                data = response.json()
                if "errors" in data:
                    print(f"GraphQL errors: {data['errors']}")
                    break
                    
                repo_data = data.get("data", {}).get("repository", {})
                if not repo_data:
                    break
                    
                issues_data = repo_data.get("issues", {})
                nodes = issues_data.get("nodes", [])
                
                for node in nodes:
                    number = node.get("number")
                    if number not in issue_map:
                        continue
                        
                    issue = issue_map[number]
                    
                    parent = node.get("parent")
                    if parent and isinstance(parent, dict):
                        issue.parent_number = parent.get("number")
                        
                    # Tracked in issues override standard parent because they represent task lists relationships
                    tracked_in = node.get("trackedInIssues", {}).get("nodes", [])
                    if tracked_in and isinstance(tracked_in, list) and len(tracked_in) > 0:
                        issue.parent_number = tracked_in[0].get("number")
                        
                    # Extract explicitly blocking and blocked by relationships
                    blocking_nodes = node.get("blocking", {}).get("nodes", [])
                    if blocking_nodes and isinstance(blocking_nodes, list):
                        issue.blocking = [b.get("number") for b in blocking_nodes if b.get("number")]
                        
                    blocked_by_nodes = node.get("blockedBy", {}).get("nodes", [])
                    if blocked_by_nodes and isinstance(blocked_by_nodes, list):
                        issue.blocked_by = [b.get("number") for b in blocked_by_nodes if b.get("number")]
                    
                    project_items = node.get("projectItems", {}).get("nodes", [])
                    for item in project_items:
                        if not item:
                            continue
                            
                        field_values = item.get("fieldValues", {}).get("nodes", [])
                        for fv in field_values:
                            if not fv or not fv.get("field"):
                                continue
                                
                            field_name = fv["field"]["name"].lower()
                            
                            # Map standard field names to our dataclass properties
                            if "prioridad" in field_name or "priority" in field_name:
                                issue.priority = fv.get("name") or fv.get("text")
                            elif "inicio temprano" in field_name or "early start" in field_name:
                                issue.early_start = fv.get("date")
                            elif "final temprano" in field_name or "early finish" in field_name:
                                issue.early_finish = fv.get("date")
                            elif "inicio tardío" in field_name or "late start" in field_name or "inicio tardio" in field_name:
                                issue.late_start = fv.get("date")
                            elif "final tardío" in field_name or "late finish" in field_name or "final tardio" in field_name:
                                issue.late_finish = fv.get("date")
                            elif "duración estimada" in field_name or "estimated duration" in field_name or "duracion" in field_name:
                                issue.estimated_duration = fv.get("number")
                
                page_info = issues_data.get("pageInfo", {})
                has_next_page = page_info.get("hasNextPage", False)
                cursor = page_info.get("endCursor")
                
        except Exception as e:
            print(f"Error enriching issues with project fields: {e}")
    
    def get_milestones(self, owner: str, repo: str, state: str = "all") -> List[GitHubMilestone]:
        """
        Fetch all milestones (sprints) from a repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: Milestone state (open, closed, all)
        """
        milestones = []
        page = 1
        
        while True:
            params = {
                "state": state,
                "per_page": 100,
                "page": page
            }
            
            data = self._get(f"/repos/{owner}/{repo}/milestones", params)
            
            if not data:
                break
            
            for item in data:
                milestone = GitHubMilestone(
                    id=item["id"],
                    number=item["number"],
                    title=item["title"],
                    state=item["state"],
                    description=item.get("description"),
                    due_on=item.get("due_on"),
                    created_at=item["created_at"],
                    updated_at=item["updated_at"],
                    closed_at=item.get("closed_at"),
                    open_issues=item["open_issues"],
                    closed_issues=item["closed_issues"]
                )
                milestones.append(milestone)
            
            if len(data) < 100:
                break
            
            page += 1
        
        return milestones
        
def save_to_json(data: List, filename: str):
    """Save data to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump([asdict(item) for item in data], f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data)} items to {filename}")

def load_from_json(filename: str, dataclass_type) -> List:
    """Load data from JSON file"""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [dataclass_type(**item) for item in data]
