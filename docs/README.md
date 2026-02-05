# Financial Management Service Documentation

This directory contains all documentation for the Financial Management Service.

## 📁 Documentation Structure

```
docs/
├── 01-main/                                    # Main project documentation
│   ├── FM_Service_PRD.md                      # Product Requirements Document
│   ├── FM_Service_Detailed_Implementation_Guide.md  # Technical Implementation Guide
│   ├── QUICK_START_FOR_AGENTS.md              # ⚡ Quick start for AI agents
│   ├── AGENT_CONTEXT_MANAGEMENT_GUIDE.md      # Complete context management guide
│   ├── IMPLEMENTATION_PROGRESS.md             # Progress tracker
│   ├── MILESTONE_*_CHECKPOINT.md              # Milestone checkpoints
│   └── ADRs/                                   # Architecture Decision Records
│
├── 02-api/                                     # API documentation (to be created)
│   └── API_Reference.md
│
├── 03-database/                                # Database documentation (to be created)
│   ├── Schema_Documentation.md
│   └── Migration_Guide.md
│
├── 04-integrations/                            # Integration documentation (to be created)
│   ├── Billing_Sync_Integration.md
│   └── Currency_API_Integration.md
│
├── 05-deployment/                              # Deployment documentation (to be created)
│   ├── Deployment_Guide.md
│   └── Environment_Setup.md
│
└── 06-troubleshooting/                         # Troubleshooting guides (to be created)
    └── Common_Issues.md
```

## 📚 Document Categories

### 01-main/
Main project documentation including:
- **Product Requirements Document (PRD):** Business requirements, user stories, acceptance criteria
- **Implementation Guide:** Technical architecture, database design, API design, development guidelines
- **Agent Guides:** Context management methodology for AI agents and developers
- **Progress Tracking:** Milestone status and checkpoint summaries

### 02-api/ (Future)
API reference documentation including:
- Endpoint specifications
- Request/response schemas
- Authentication requirements
- Example requests

### 03-database/ (Future)
Database documentation including:
- Complete schema documentation
- Table relationships
- Index strategies
- Migration procedures

### 04-integrations/ (Future)
Integration documentation including:
- Billing module sync integration
- Currency exchange rate API integration
- Third-party service integrations

### 05-deployment/ (Future)
Deployment documentation including:
- Production deployment procedures
- Environment configuration
- CI/CD pipeline documentation
- Monitoring and alerting setup

### 06-troubleshooting/ (Future)
Troubleshooting guides including:
- Common issues and solutions
- Debug procedures
- Performance optimization tips

## 🔄 Document Maintenance

All documentation should be kept up-to-date with code changes. When making significant changes:

1. Update relevant documentation files
2. Update the "Last Updated" date in each document
3. Update the change log section
4. Review with relevant stakeholders

## 📝 Document Naming Convention

- Use descriptive, clear names
- Use PascalCase for document names
- Include version numbers in document content, not filenames
- Use underscores for multi-word names (e.g., `FM_Service_PRD.md`)

## 🎯 Quick Links

### Main Documentation
- [Product Requirements Document (PRD)](./01-main/FM_Service_PRD.md) - **Complete PRD v2.0 with Treasury + FM microservices**
- [Implementation Guide](./01-main/FM_Service_Detailed_Implementation_Guide.md) - Technical implementation guide
- [Token Cost Estimate](./01-main/Token_Cost_Estimate.md) - GPT-5.2 code model cost estimates

### For AI Agents & Developers
- [**Quick Start Guide**](./01-main/QUICK_START_FOR_AGENTS.md) - ⚡ **START HERE** - 5-minute guide to checkpoint methodology
- [**Agent Context Management Guide**](./01-main/AGENT_CONTEXT_MANAGEMENT_GUIDE.md) - Complete guide for context checkpoint methodology
- [Implementation Progress](./01-main/IMPLEMENTATION_PROGRESS.md) - Current milestone status and progress
- [Milestone Checkpoints](./01-main/MILESTONE_*_CHECKPOINT.md) - Checkpoint summaries for each milestone

---

**Last Updated:** December 21, 2025
