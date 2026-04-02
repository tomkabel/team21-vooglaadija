#!/usr/bin/env zsh
set -e

npx skills add https://github.com/vamseeachanta/workspace-hub --skill github-project-board -g -y
npx skills add https://github.com/anton-abyzov/specweave --skill github-issue-tracker -g -y
npx skills add https://github.com/yu-iskw/github-project-skills -g -y
npx skills add https://github.com/aj-geddes/useful-ai-prompts --skill agile-sprint-planning -g -y
npx skills add deanpeters/product-manager-skills@roadmap-planning -g -y
npx skills add vamseeachanta/workspace-hub@github-project-board -g -y
npx skills add anton-abyzov/specweave@github-issue-tracker -g -y
npx skills add n8n-io/n8n@linear-issue -g -y
npx skills list
