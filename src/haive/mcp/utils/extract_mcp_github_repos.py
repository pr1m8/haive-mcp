#!/usr/bin/env python3
"""
GitHub Repository Extractor and Categorizer Script

This script extracts repository URLs from https://github.com/TensorBlock/awesome-mcp-servers,
attempts to categorize them based on HTML structure, and saves the results to JSON files.

Features:
- Extracts repository URLs from the README content
- Attempts to categorize repositories by their section headers
- Identifies and removes duplicates
- Validates repository URLs (optional)
- Saves results to JSON files (both all repositories and by category when possible)
- Provides basic analysis of the collected repositories

Usage:
    python extract_categorized_mcp_repositories.py [--validate] [--timeout SECONDS]

Options:
    --validate      Validate repository URLs (check if they exist)
    --timeout       Request timeout in seconds (default: 10)
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import os
import argparse
from datetime import datetime
import concurrent.futures
import time

# Constants
DEFAULT_TIMEOUT = 10
DEFAULT_OUTPUT_FILE = "mcp_repositories.json"
CATEGORIZED_OUTPUT_FILE = "mcp_repositories_by_category.json"
SOURCE_URL = "https://github.com/TensorBlock/awesome-mcp-servers"

def extract_repositories_from_github_page(url, timeout=DEFAULT_TIMEOUT):
    """
    Extract repository references from GitHub page HTML content
    
    Args:
        url (str): URL of the GitHub page to extract repositories from
        timeout (int): Request timeout in seconds
        
    Returns:
        tuple: (repos, categorized_repos)
            - repos: List of all repository names
            - categorized_repos: Dictionary of categories to repository lists (may be empty)
    """
    try:
        print(f"Fetching content from {url}...")
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        
        print("Parsing HTML content...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the README content which is usually in the article.markdown-body element
        article = soup.select_one('article.markdown-body')
        if not article:
            print("Could not find the rendered markdown content.")
            return [], {}
        
        # Find all <li> elements which may contain repository references
        list_items = article.select('li')
        
        # Pattern to match repository references like "username/repository-name:"
        repo_pattern = re.compile(r'([a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+):')
        
        # Extract all repositories
        repos = []
        for li in list_items:
            li_text = li.get_text()
            match = repo_pattern.search(li_text)
            if match:
                repos.append(match.group(1))
        
        # Try to categorize repositories based on HTML structure
        # This is a best-effort approach and may not work perfectly
        categorized_repos = {}
        
        # Find all h2 elements (section headers)
        section_headers = article.select('h2')
        
        # Ignore certain headers that don't represent repository categories
        ignore_headers = ['Model Context Protocol', 'Coverage', 'Server Categories']
        
        for header in section_headers:
            category = header.get_text().strip()
            if category in ignore_headers:
                continue
            
            # Find all list items that follow this header until the next h2
            category_repos = []
            next_element = header.next_sibling
            
            while next_element and not (next_element.name == 'h2'):
                if hasattr(next_element, 'name') and next_element.name == 'ul':
                    # Found a list under this header
                    for li in next_element.select('li'):
                        li_text = li.get_text()
                        match = repo_pattern.search(li_text)
                        if match:
                            category_repos.append(match.group(1))
                next_element = next_element.next_sibling
            
            if category_repos:
                categorized_repos[category] = category_repos
        
        return repos, categorized_repos
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return [], {}
    except Exception as e:
        print(f"Error extracting repositories from {url}: {e}")
        return [], {}

def find_unique_repos(repos):
    """
    Find unique repositories and create their GitHub URLs
    
    Args:
        repos (list): List of repository names
        
    Returns:
        list: List of unique GitHub repository URLs
    """
    unique_repos = set(repos)
    github_urls = [f"https://github.com/{repo}" for repo in unique_repos]
    return github_urls

def check_repository_exists(repo_url, timeout=DEFAULT_TIMEOUT):
    """
    Check if a repository URL is valid and accessible
    
    Args:
        repo_url (str): URL of the repository to check
        timeout (int): Request timeout in seconds
        
    Returns:
        bool: True if the repository exists, False otherwise
    """
    try:
        response = requests.head(repo_url, timeout=timeout)
        return response.status_code == 200
    except:
        return False

def validate_repositories(repo_urls, max_workers=10, timeout=DEFAULT_TIMEOUT):
    """
    Validate repository URLs using parallel requests
    
    Args:
        repo_urls (list): List of repository URLs to validate
        max_workers (int): Maximum number of concurrent workers
        timeout (int): Request timeout in seconds
        
    Returns:
        list: List of valid repository URLs
    """
    valid_urls = []
    
    print(f"\nValidating {len(repo_urls)} repositories (this might take some time)...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks
        future_to_url = {executor.submit(check_repository_exists, url, timeout): url for url in repo_urls}
        
        # Process completed tasks
        for i, future in enumerate(concurrent.futures.as_completed(future_to_url)):
            url = future_to_url[future]
            try:
                is_valid = future.result()
                if is_valid:
                    valid_urls.append(url)
                
                # Show progress every 50 repositories
                if (i + 1) % 50 == 0:
                    print(f"Processed {i + 1}/{len(repo_urls)} repositories, found {len(valid_urls)} valid ones.")
                
                # Avoid rate limiting
                if (i + 1) % 100 == 0:
                    time.sleep(1)
            except Exception as e:
                print(f"Error checking {url}: {e}")
    
    return valid_urls

def save_repositories_to_file(repo_urls, filename=DEFAULT_OUTPUT_FILE):
    """
    Save repository URLs to a JSON file
    
    Args:
        repo_urls (list): List of repository URLs to save
        filename (str): Output filename
    """
    with open(filename, "w") as f:
        json.dump(sorted(repo_urls), f, indent=2)
    print(f"Saved {len(repo_urls)} repository URLs to {filename}")

def save_categorized_repositories(categorized_repos, filename=CATEGORIZED_OUTPUT_FILE):
    """
    Save categorized repository URLs to a JSON file
    
    Args:
        categorized_repos (dict): Dictionary mapping categories to repository lists
        filename (str): Output filename
    """
    # Convert to full GitHub URLs
    categorized_urls = {}
    for category, repos in categorized_repos.items():
        categorized_urls[category] = sorted([f"https://github.com/{repo}" for repo in repos])
    
    # Count total repositories
    total_count = sum(len(repos) for repos in categorized_urls.values())
    
    with open(filename, "w") as f:
        json.dump(categorized_urls, f, indent=2)
    print(f"Saved {len(categorized_urls)} categories with {total_count} repository URLs to {filename}")

def analyze_repositories(repo_urls, categorized_repos=None):
    """
    Analyze repository data
    
    Args:
        repo_urls (list): List of repository URLs to analyze
        categorized_repos (dict, optional): Dictionary mapping categories to repository lists
    """
    print(f"\nAnalysis of {len(repo_urls)} repositories:")
    
    # Count repositories by organization/username
    usernames = {}
    for repo_url in repo_urls:
        # Extract username from URL (format: https://github.com/username/repo)
        parts = repo_url.split("/")
        if len(parts) >= 4:
            username = parts[3]
            usernames[username] = usernames.get(username, 0) + 1
    
    # Print the top 10 users/organizations
    print("\nTop 10 users/organizations by number of repositories:")
    top_users = sorted(usernames.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (username, count) in enumerate(top_users):
        print(f"{i+1}. {username}: {count} repositories")
    
    # If categorized repositories are provided, analyze them as well
    if categorized_repos:
        print("\nRepository distribution by category:")
        category_counts = [(category, len(repos)) for category, repos in categorized_repos.items()]
        for category, count in sorted(category_counts, key=lambda x: x[1], reverse=True):
            print(f"- {category}: {count} repositories")

def parse_arguments():
    """
    Parse command-line arguments
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Extract and categorize repository URLs from TensorBlock/awesome-mcp-servers")
    parser.add_argument("--validate", action="store_true", help="Validate repository URLs")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})")
    return parser.parse_args()

def main():
    """
    Main function to extract and process MCP repositories
    """
    args = parse_arguments()
    
    print(f"Extracting repositories from {SOURCE_URL}...")
    
    # Extract repositories
    repos, categorized_repos = extract_repositories_from_github_page(SOURCE_URL, args.timeout)
    
    if not repos:
        print("No repositories found.")
        return
    
    print(f"\nFound {len(repos)} repositories.")
    
    # Get unique repositories and create URLs
    github_urls = find_unique_repos(repos)
    
    print(f"Found {len(github_urls)} unique repository URLs.")
    
    # Print a sample of the GitHub URLs
    print("\nSample GitHub URLs:")
    for i, url in enumerate(sorted(github_urls)[:10]):
        print(f"{i+1}. {url}")
    
    # Validate repositories if requested
    if args.validate:
        github_urls = validate_repositories(github_urls, timeout=args.timeout)
        print(f"\nValidated {len(github_urls)} repository URLs.")
    
    # Save all repositories to a timestamped file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"mcp_repositories_{timestamp}.json"
    save_repositories_to_file(github_urls, filename)
    
    # Also save to a standard filename for easier access
    save_repositories_to_file(github_urls)
    
    # Save categorized repositories if available
    if categorized_repos:
        cat_filename = f"mcp_repositories_by_category_{timestamp}.json"
        save_categorized_repositories(categorized_repos, cat_filename)
        save_categorized_repositories(categorized_repos)
    else:
        print("\nUnable to categorize repositories.")
    
    # Analyze the collected repositories
    analyze_repositories(github_urls, categorized_repos)
    
    print("\nRepository URLs successfully extracted and saved.")
    print(f"Output files:")
    print(f"- {DEFAULT_OUTPUT_FILE} (all repositories)")
    if categorized_repos:
        print(f"- {CATEGORIZED_OUTPUT_FILE} (categorized repositories)")
    print(f"- {filename} (timestamped all repositories)")
    if categorized_repos:
        print(f"- {cat_filename} (timestamped categorized repositories)")

if __name__ == "__main__":
    main()
