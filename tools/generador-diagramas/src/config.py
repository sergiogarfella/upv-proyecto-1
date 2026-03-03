#!/usr/bin/env python3
"""
Configuration file for GitHub Gantt Chart Generator
Modify these settings to match your repository
"""

# =============================================================================
# GITHUB REPOSITORY CONFIGURATION
# =============================================================================

# Repository owner (username or organization)
GITHUB_OWNER = "sergiogarfella"

# Repository name
GITHUB_REPO = "dsr-ai"

# GitHub Personal Access Token (optional but recommended)
# Set to None to use unauthenticated requests (60 requests/hour limit)
# Create token at: https://github.com/settings/tokens
GITHUB_TOKEN = None  # Or set: "ghp_your_token_here"

# =============================================================================
# OUTPUT CONFIGURATION
# =============================================================================

import os

# Project Root is one level up from this file's directory (src)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directory for generated charts
OUTPUT_DIRECTORY = os.path.join(PROJECT_ROOT, "charts")

# Directory for JSON data files
DATA_DIRECTORY = os.path.join(PROJECT_ROOT, "data")

# =============================================================================
# ANALYSIS SETTINGS
# =============================================================================

# Maximum number of issues to fetch (per request)
# GitHub API pagination limit is 100
MAX_ISSUES_PER_PAGE = 100

# Maximum pages to fetch for issues
# Set to None to fetch all pages
MAX_PAGES = 10

# Issue states to fetch: "open", "closed", or "all"
ISSUE_STATE = "all"

# Milestone states to fetch: "open", "closed", or "all"
MILESTONE_STATE = "all"

# =============================================================================
# GANTT CHART CUSTOMIZATION
# =============================================================================

# Chart DPI (resolution)
CHART_DPI = 150

# Advanced Settings
DEBUG_MODE = False
