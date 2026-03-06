#!/usr/bin/env python
"""Update Product Requirements Document for TrueVow Financial Management Service."""

import os
import sys
from datetime import datetime

# External documentation path (universal for all repos)
DOC_PATH = r"C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Documentation"

# Target PRD file
PRD_FILE = os.path.join(DOC_PATH, "TrueVow-Financial-Management-PRD.md")

def main():
    """Update the PRD with recent architectural changes."""
    
    # Check if documentation directory exists
    if not os.path.exists(DOC_PATH):
        print(f"❌ Documentation directory not found: {DOC_PATH}")
        sys.exit(1)
    
    # Create PRD file if it doesn't exist
    if not os.path.exists(PRD_FILE):
        print(f"📝 Creating new PRD file: {PRD_FILE}")
        initial_content = f"""# TrueVow Financial Management Service - Product Requirements Document

> **Version:** 1.0
> **Last Updated:** {datetime.now().strftime('%B %Y')}
> **Status:** ✅ INITIAL SETUP COMPLETE | 🔄 ACTIVE DEVELOPMENT

---

## 📋 Overview

TrueVow Financial Management Service is a comprehensive financial management system built with Python/FastAPI backend and Next.js/React frontend.

## 🔧 Recent Architectural Updates

### Version 1.0 Updates ({datetime.now().strftime('%B %Y')})

**Authentication & Security:**
- ✅ Integrated Clerk App 1 (TrueVow-Platform-Operators) authentication
- ✅ High-trust finance-role users with approval workflows
- ✅ JWT-based API authentication with role-based access control
- ✅ Protected routes with proper middleware implementation

**Core API Infrastructure:**
- ✅ Implemented legal entity management API endpoints
- ✅ Created `/api/v1/entities` endpoint for organization structure
- ✅ Built book management system for multi-entity accounting
- ✅ Established proper database seeding with sample entities

**Frontend Integration:**
- ✅ Next.js 14 with TypeScript and Tailwind CSS
- ✅ React Query for data fetching and caching
- ✅ Entity/Book context providers for state management
- ✅ Responsive UI components with proper error handling

## 🏗️ System Architecture

### Backend (Python/FastAPI)
- **Framework:** FastAPI with async SQLAlchemy
- **Database:** PostgreSQL with Alembic migrations
- **Authentication:** Clerk JWT validation
- **API Version:** v1 with proper routing structure

### Frontend (Next.js/React)
- **Framework:** Next.js 14 with App Router
- **State Management:** React Query + Context API
- **Styling:** Tailwind CSS with custom components
- **Authentication:** Clerk SDK with session management

## 🎯 Key Features

### Current Implementation
- User authentication and authorization
- Legal entity management
- Book/accounting period management
- Basic financial data structures
- Responsive dashboard interface

### Planned Features
- Full accounting workflow
- Reporting and analytics
- Treasury management
- Payroll processing
- Intercompany transactions

## 🛡️ Security

- Role-based access control (RBAC)
- JWT token validation
- Protected API endpoints
- Secure session management
- Audit logging capabilities

---
*This document is automatically maintained by the Financial Management service repository.*
"""
        with open(PRD_FILE, "w", encoding="utf-8") as f:
            f.write(initial_content)
        print(f"✅ Created new PRD file: {PRD_FILE}")
        return
    
    # Read existing content
    with open(PRD_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Update timestamp
    updated_content = content.replace(
        f"> **Last Updated:** {datetime.now().strftime('%B %Y')}",
        f"> **Last Updated:** {datetime.now().strftime('%B %Y')}"
    )
    
    # Add recent changes section if not present
    if "## 🔧 Recent Architectural Updates" not in content:
        # Insert after Overview section
        sections = updated_content.split("## 🏗️ System Architecture")
        if len(sections) == 2:
            recent_updates = f"""

## 🔧 Recent Architectural Updates

### Version 1.0 Updates ({datetime.now().strftime('%B %Y')})

**Authentication & Security:**
- ✅ Integrated Clerk App 1 (TrueVow-Platform-Operators) authentication
- ✅ High-trust finance-role users with approval workflows
- ✅ JWT-based API authentication with role-based access control
- ✅ Protected routes with proper middleware implementation

**Core API Infrastructure:**
- ✅ Implemented legal entity management API endpoints
- ✅ Created `/api/v1/entities` endpoint for organization structure
- ✅ Built book management system for multi-entity accounting
- ✅ Established proper database seeding with sample entities

**Frontend Integration:**
- ✅ Next.js 14 with TypeScript and Tailwind CSS
- ✅ React Query for data fetching and caching
- ✅ Entity/Book context providers for state management
- ✅ Responsive UI components with proper error handling

"""
            updated_content = sections[0] + recent_updates + "## 🏗️ System Architecture" + sections[1]
    
    # Write updated content
    with open(PRD_FILE, "w", encoding="utf-8") as f:
        f.write(updated_content)
    
    print(f"✅ Updated PRD: {PRD_FILE}")

if __name__ == "__main__":
    main()