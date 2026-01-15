#!/bin/bash

# Script to push fastship-aws to GitHub
# Replace YOUR_GITHUB_USERNAME with your actual GitHub username
# Replace fastship-aws with your desired repository name if different

GITHUB_USERNAME="anglopz"  # Update this if needed
REPO_NAME="fastship-aws"   # Update this if needed

echo "Adding remote origin..."
git remote add origin https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git

echo "Pushing main branch..."
git checkout main
git push -u origin main

echo "Pushing develop branch..."
git checkout develop
git push -u origin develop

echo "Done! Repository pushed to GitHub."
echo "Repository URL: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
