# Cobalt Project Sprint Setup Guide

This guide explains how to use the sprint setup scripts to initialize the entire Cobalt project from start to finish.

## 📁 Setup Scripts Overview

| Script | Purpose | Duration |
|--------|---------|----------|
| `setup-sprint-1.sh` | Project Kickoff & Planning | Mar 9-15, 2026 |
| `setup-sprint-2.sh` | Architecture Foundation | Mar 16-22, 2026 |
| `setup-sprint-3.sh` | Core Features Implementation | Mar 23-29, 2026 |
| `setup-sprint-4.sh` | AWS Infrastructure & Deployment | Mar 30-Apr 5, 2026 |
| `setup-sprint-5.sh` | Advanced Features & Optimization | Apr 6-12, 2026 |
| `setup-sprint-6.sh` | Final Polish & Project Closure | Apr 13-19, 2026 |
| `setup-sprint2-project.sh` | GitHub Project Board for Sprint 2 | Optional |
| `setup-all-sprints.sh` | Master script to run all sprints | Orchestrates all |

## 🚀 Quick Start

### Prerequisites

1. **GitHub CLI** installed and authenticated:
   ```bash
   gh auth login
   ```

2. **Repository Access**: Ensure you have write access to `tomkabel/team21-vooglaadija`

3. **jq** installed (for JSON processing):
   ```bash
   # macOS
   brew install jq
   
   # Ubuntu/Debian
   sudo apt-get install jq
   ```

### Option 1: Setup All Sprints at Once (Recommended for Initial Setup)

```bash
# Navigate to project root
cd /home/tomkabel/Documents/team21-vooglaadija

# Run master setup script
./setup-all-sprints.sh --all

# Or with project boards
./setup-all-sprints.sh --all --with-projects

# Dry run first (recommended)
./setup-all-sprints.sh --all --dry-run
```

### Option 2: Setup Individual Sprints

```bash
# Setup only Sprint 1
./setup-sprint-1.sh

# Setup multiple specific sprints
./setup-all-sprints.sh 1 2 3

# Setup Sprint 2 with project board
./setup-sprint-2.sh
./setup-sprint2-project.sh
```

## 📋 What Each Script Creates

### Sprint 1: Project Kickoff & Planning
- **Epic**: Project foundation and planning
- **Stories**: Requirements, ADRs, dev environment, AWS planning, documentation
- **Labels**: sprint-1, type-research, area-architecture, area-planning
- **Milestone**: Sprint 1: Project Kickoff & Planning (Due: Mar 15, 2026)
- **Story Points**: 21

### Sprint 2: Architecture Foundation
- **Epic**: Technical foundation establishment
- **Stories**: PostgreSQL schema, Svelte 5 setup, pnpm workspaces, auth service, CI/CD
- **Labels**: sprint-2, type-infra, type-refactor, area-db, area-svelte, area-auth
- **Milestone**: Sprint 2: Architecture Foundation (Due: Mar 22, 2026)
- **Story Points**: 26

### Sprint 3: Core Features Implementation
- **Epic**: First working features
- **Stories**: WebCodecs decoder, format selection, trim feature, UI library, testing framework
- **Labels**: sprint-3, type-feature, type-testing, area-webcodecs, area-ui, area-testing
- **Milestone**: Sprint 3: Core Features Implementation (Due: Mar 29, 2026)
- **Story Points**: 26

### Sprint 4: AWS Infrastructure & Deployment
- **Epic**: Production infrastructure
- **Stories**: Terraform infrastructure, download service, CI/CD pipeline, monitoring, hardening
- **Labels**: sprint-4, type-infra, area-aws, area-monitoring, area-download
- **Milestone**: Sprint 4: AWS Infrastructure & Deployment (Due: Apr 5, 2026)
- **Story Points**: 26

### Sprint 5: Advanced Features & Optimization
- **Epic**: Feature-complete application
- **Stories**: Batch processing, premium features (Stripe), performance optimization, caching, error recovery
- **Labels**: sprint-5, type-feature, type-optimization, area-premium, area-performance
- **Milestone**: Sprint 5: Advanced Features & Optimization (Due: Apr 12, 2026)
- **Story Points**: 26

### Sprint 6: Final Polish & Project Closure
- **Epic**: Project completion
- **Stories**: Bug fixes, comprehensive testing, final documentation, demo prep, project handoff
- **Labels**: sprint-6, type-docs, type-testing, type-bug, area-demo
- **Milestone**: Sprint 6: Final Polish & Project Closure (Due: Apr 19, 2026)
- **Story Points**: 26

## 🎯 Total Project Scope

| Metric | Count |
|--------|-------|
| **Sprints** | 6 |
| **Total Duration** | 6 weeks |
| **Epics** | 6 |
| **Stories** | 30 |
| **Total Story Points** | 151 |
| **Labels** | 30+ |
| **Milestones** | 6 |

## 🏷️ Label System

### Sprint Labels
- `sprint-1` through `sprint-6` - Sprint assignment

### Priority Labels
- `priority-critical` - Blocks release
- `priority-high` - Important
- `priority-medium` - Normal priority
- `priority-low` - Nice to have

### Type Labels
- `type-feature` - New feature
- `type-bug` - Bug fix
- `type-refactor` - Code refactoring
- `type-infra` - Infrastructure/DevOps
- `type-docs` - Documentation
- `type-testing` - Testing
- `type-research` - Research/Spike
- `type-optimization` - Performance

### Area Labels
- `area-architecture` - System architecture
- `area-planning` - Project planning
- `area-db` - Database
- `area-svelte` - Svelte/SvelteKit
- `area-auth` - Authentication
- `area-webcodecs` - WebCodecs API
- `area-ui` - UI/UX
- `area-aws` - AWS/Infrastructure
- `area-monitoring` - Monitoring
- `area-download` - Download service
- `area-testing` - Testing infrastructure
- `area-premium` - Premium features
- `area-performance` - Performance
- `area-demo` - Demo preparation
- `area-docs` - Documentation

## 🔧 Automation Workflows

The sprint setup scripts rely on existing automation workflows in `.github/workflows/`:

### Sprint Automation (`sprint-automation.yml`)
- Automatically assigns milestones to PRs and linked issues
- Labels PRs by size (XS/S/M/L/XL)
- Updates sprint digest on merge
- Manages `status: in-progress` labels

### AI PR Reviewer (`ai-pr-reviewer.yml`)
- Automated code review via OpenRouter/Claude
- Responds to `/review`, `/describe`, `/improve` commands
- Cost-optimized (skips synchronize events)

These workflows are **not** created by the sprint setup scripts - they are already in the repository.

## 📊 GitHub Project Boards

### Creating Project Boards

For each sprint, you can create a GitHub Project v2 board:

```bash
# Sprint 1 (using generic approach - future sprints)
gh project create --owner=tomkabel --title="Cobalt Sprint 1: Project Kickoff"

# Sprint 2 (has dedicated script)
./setup-sprint2-project.sh
```

### Recommended Board Columns

```
Backlog → Ready for Dev → In Progress → Code Review → Testing → Done
```

### Custom Fields

- **Story Points**: Number field
- **Priority**: Single select (Critical/High/Medium/Low)
- **Status**: Single select (board columns)
- **Type**: Single select (Feature/Bug/Refactor/etc.)

## 🛠️ Troubleshooting

### Script Fails with "gh: not found"

```bash
# Install GitHub CLI
# macOS
brew install gh

# Ubuntu
sudo apt-get install gh

# Then authenticate
gh auth login
```

### Issues Already Exist

Scripts are idempotent - they skip creating items that already exist:
- Labels: "Label X already exists"
- Milestones: "Milestone may already exist"

### Permission Denied

```bash
# Make scripts executable
chmod +x setup-*.sh
```

### Rate Limiting

If you hit GitHub API rate limits:
```bash
# Wait a few minutes and retry
# Or run specific sprints instead of all at once
./setup-all-sprints.sh 1 2  # Just sprints 1-2
```

## 🔄 Sprint Execution Workflow

### Week 1: Sprint Planning
```bash
# 1. Create sprint issues and milestone
./setup-sprint-N.sh

# 2. Create project board (optional)
./setup-sprintN-project.sh  # if available

# 3. Conduct sprint planning meeting
# 4. Move stories to "Ready for Dev"
```

### During Sprint
- Automation workflows handle milestone assignment
- PR size labeling happens automatically
- Sprint digest updates on merge

### Sprint Review
```bash
# View closed issues
gh issue list -R tomkabel/team21-vooglaadija --state=closed --milestone "Sprint N"

# View sprint digest
cat SPRINT-DIGEST.md
```

### Sprint Retrospective
- Review velocity (story points completed)
- Update process documentation
- Plan next sprint

## 📈 Velocity Tracking

| Sprint | Story Points | Focus Area |
|--------|--------------|------------|
| 1 | 21 | Planning |
| 2 | 26 | Foundation |
| 3 | 26 | Core Features |
| 4 | 26 | Infrastructure |
| 5 | 26 | Advanced Features |
| 6 | 26 | Polish & Closure |
| **Total** | **151** | **6 Weeks** |

## 🎓 Best Practices

1. **Run dry-run first**: `./setup-all-sprints.sh --all --dry-run`
2. **Setup one sprint at a time** for active development
3. **Use project boards** for visual sprint tracking
4. **Leverage automation** - don't manually manage labels/milestones
5. **Review sprint digest** regularly for progress tracking

## 📚 Additional Resources

- [GitHub Projects Documentation](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [GitHub CLI Manual](https://cli.github.com/manual/)
- [Svelte 5 Migration Guide](https://svelte-5-preview.vercel.app/docs)
- [WebCodecs API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/WebCodecs_API)

## 🤝 Support

For issues with sprint setup scripts:
1. Check the script has execute permissions
2. Verify GitHub CLI authentication
3. Review error messages carefully
4. Run with `--verbose` flag for detailed output

## 📝 Changelog

### v1.0.0 (2026-03-17)
- Initial sprint setup scripts created
- Master orchestration script added
- Removed workflow creation (now in `.github/workflows/`)
- Added comprehensive documentation
- All 6 sprints defined with 151 total story points

---

**Project**: Cobalt Video Processing Platform  
**Repository**: https://github.com/tomkabel/team21-vooglaadija  
**Project Duration**: March 9 - April 19, 2026 (6 weeks)  
**Team Size**: 2 developers  
**Total Story Points**: 151
