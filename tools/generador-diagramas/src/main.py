#!/usr/bin/env python3
"""
Main execution script for GitHub Gantt Chart Generator
Orchestrates data extraction and chart generation
"""

import os
import sys
import argparse
from datetime import datetime
from typing import Optional

# Import our modules
import config
from github_api import GitHubAPI, save_to_json, load_from_json, GitHubIssue, GitHubMilestone
from gantt_generator import GanttChartGenerator

def run_full_analysis(owner: str, repo: str, token: Optional[str] = None,
                      output_dir: str = "charts"):
    """
    Run complete analysis: fetch data and generate Gantt charts
    """
    print("=" * 60)
    print(f"GitHub Gantt Chart Generator")
    print(f"Repository: {owner}/{repo}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Step 1: Fetch data from GitHub
    print("\n📥 STEP 1: Fetching data from GitHub...")
    print("-" * 40)
    
    api = GitHubAPI(token=token)
    
    try:
        os.makedirs(config.DATA_DIRECTORY, exist_ok=True)
        
        # Fetch issues
        print("Fetching issues...")
        issues = api.get_issues(owner, repo, state=config.ISSUE_STATE, 
                                per_page=config.MAX_ISSUES_PER_PAGE, max_pages=config.MAX_PAGES)
        save_to_json(issues, os.path.join(config.DATA_DIRECTORY, "issues.json"))
        
        # Fetch milestones (sprints)
        print("Fetching milestones...")
        milestones = api.get_milestones(owner, repo, state=config.MILESTONE_STATE)
        save_to_json(milestones, os.path.join(config.DATA_DIRECTORY, "milestones.json"))
        
        # Sort milestones by title
        if milestones:
            milestones.sort(key=lambda m: m.title)
        
        print(f"\n✅ Data fetched successfully!")
        print(f"   Issues: {len(issues)}")
        print(f"   Milestones: {len(milestones)}")
        
    except Exception as e:
        print(f"\n❌ Error fetching data: {e}")
        sys.exit(1)
    
    # Step 2: Generate charts
    print("\n📊 STEP 2: Generating Gantt charts...")
    print("-" * 40)
    
    generator = GanttChartGenerator(output_dir=output_dir)
    
    try:
        if issues:
            if milestones:
                print("Creating Gantt and PERT charts per sprint...")
                for i, milestone in enumerate(milestones):
                    generator.create_gantt_chart(issues, milestone, filename=f"diagrama_gantt_{i+1}.png")
                    generator.create_pert_chart(issues, milestone, filename=f"diagrama_pert_{i+1}.png")
            else:
                print("Creating overall Gantt and PERT chart...")
                generator.create_gantt_chart(issues)
                generator.create_pert_chart(issues)
        
        print(f"\n✅ Charts generated successfully!")
        print(f"   Output directory: {output_dir}/")
        
    except Exception as e:
        print(f"\n❌ Error generating Gantt charts: {e}")
        sys.exit(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE!")
    print("=" * 60)

def run_from_json(issues_file: str = "issues.json",
                  milestones_file: str = "milestones.json",
                  output_dir: str = "charts"):
    """
    Generate charts from existing JSON files (no API calls)
    """
    print("=" * 60)
    print("Generating charts from existing data...")
    print("=" * 60)
    
    issue_path = os.path.join(config.DATA_DIRECTORY, issues_file) if not os.path.exists(issues_file) else issues_file
    milestone_path = os.path.join(config.DATA_DIRECTORY, milestones_file) if not os.path.exists(milestones_file) else milestones_file
    
    # Load data
    try:
        issues = load_from_json(issue_path, GitHubIssue)
        milestones = load_from_json(milestone_path, GitHubMilestone)
    except FileNotFoundError as e:
        print(f"File not found error: {e}")
        sys.exit(1)
    
    # Sort milestones
    if milestones:
        milestones.sort(key=lambda m: m.title)
    
    print(f"Loaded {len(issues)} issues and {len(milestones)} milestones")
    
    generator = GanttChartGenerator(output_dir=output_dir)
    
    if milestones:
        for i, milestone in enumerate(milestones):
            generator.create_gantt_chart(issues, milestone, filename=f"diagrama_gantt_{i+1}.png")
            generator.create_pert_chart(issues, milestone, filename=f"diagrama_pert_{i+1}.png")
    else:
        generator.create_gantt_chart(issues)
        generator.create_pert_chart(issues)
    
    print(f"\nCharts saved to: {output_dir}/")

def main():
    parser = argparse.ArgumentParser(
        description='GitHub Gantt Chart Generator Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick start (uses config.py)
  python main.py
  
  # Override with full analysis (fetch + charts)
  python main.py --owner sergiogarfella --repo dsr-ai
  
  # Use existing JSON files
  python main.py --from-json
        """
    )
    
    parser.add_argument('--owner', type=str, 
                       help='GitHub repository owner')
    parser.add_argument('--repo', type=str, 
                       help='GitHub repository name')
    parser.add_argument('--token', type=str, 
                       help='GitHub Personal Access Token')
    parser.add_argument('--output', type=str, default=config.OUTPUT_DIRECTORY,
                       help=f'Output directory for charts (default: {config.OUTPUT_DIRECTORY})')
    parser.add_argument('--from-json', action='store_true',
                       help='Generate charts from existing JSON files')
    
    args = parser.parse_args()
    
    if args.from_json:
        run_from_json(output_dir=args.output)
    elif args.owner and args.repo:
        token = args.token or os.getenv("GITHUB_TOKEN") or config.GITHUB_TOKEN
        run_full_analysis(args.owner, args.repo, token, args.output)
    else:
        # Default behavior uses Config.py settings
        run_full_analysis(config.GITHUB_OWNER, config.GITHUB_REPO, config.GITHUB_TOKEN, args.output)


if __name__ == "__main__":
    main()
