# Booklat

Version: 1.0

## Overview

Booklat is a mobile-first, open-source library management system designed for schools and small organizations.

The system focuses on:

* Mobile usability
* Simple deployment
* Fine-grained permissions
* Complete auditability
* Copy-level inventory tracking
* CSV-based bulk operations
* No email dependency

---

# Goals

## Primary Goals

* Manage books and inventory
* Manage library members
* Manage borrowing and returns
* Manage checkout requests
* Maintain complete inventory history
* Support CSV imports and exports
* Support complete audit logging
* Provide simple administration tools

---

## Non-Goals (v1)

* Email notifications
* QR codes
* Barcode scanning
* Public catalog
* Multi-branch support
* Offline support
* Progressive Web App (PWA)
* Fine calculations
* Advanced analytics

---

# Technology Stack

## Application

* Django
* PostgreSQL
* Redis
* Gunicorn
* django-ratelimit

## Infrastructure

* Docker
* Docker Compose
* WhiteNoise
* Cloudflare Tunnel (production-only, `docker-compose.prod.yml`)

## Not Used

* Nginx
* Node.js
* npm
* React
* Vue
* Angular

---

# Architecture

Internet
→ Cloudflare (optional)
→ Cloudflare Tunnel (optional, production only)
→ Gunicorn
→ Django
→ PostgreSQL
→ Redis

## Django Admin

`django.contrib.admin` is **not** installed. All management is through custom views.

## Session Behavior

Sessions use the `cached_db` backend (DB + Redis cache). Expires on browser close (`SESSION_EXPIRE_AT_BROWSER_CLOSE = True`), max 24-hour cookie age.

## Rate Limiting

`django-ratelimit` is used on auth and form submission endpoints. Ratelimits are disabled when `DEBUG=1` and active in production.

## Environment

No dotenv package. Environment variables are read directly from `os.environ` in `settings.py` with fallback defaults. A `.env.example` is provided as a template.

---

# Design Principles

## Mobile First

Most users will access Booklat using mobile devices.

Requirements:

* Responsive layouts
* Large touch targets
* Search-first workflows
* Single-column forms
* Minimal horizontal scrolling

---

## Soft Deletes

Operational records must never be hard deleted.

Use archival instead.

Applicable entities:

* Users
* Books
* Book Copies

Historical records must remain available.

---

## Auditability

All significant actions must generate audit logs.

Audit logs are immutable.

---

# Roles

## Administrator

Full system access.

Capabilities:

* Manage users
* Reset passwords
* Manage books
* Manage copies
* Manage loans
* Manage checkout requests
* Import data
* Export data
* View audit logs
* Configure settings

---

## Staff

Library operational access.

Capabilities:

* Manage books
* Manage copies
* Manage loans
* Process checkout requests

Optional permissions:

* Password reset
* User creation

Cannot:

* Change system settings
* Import/export data
* Modify role definitions

---

## Member

Capabilities:

* Login
* View own profile
* View own loan history
* Search books
* Request book checkout

---

# Permission Model

Permissions are stored in the database.

Examples:

users.view
users.create
users.update
users.archive
users.password_reset

books.view
books.create
books.update
books.archive

copies.view
copies.create
copies.update

loans.create
loans.return

requests.process

audit.view

system.import_data
system.export_data

Roles are collections of permissions.

---

# Authentication

## Login

Users authenticate using LRN.

Example:

123456789012

---

## Password Requirements

Minimum requirements:

* 16 characters minimum
* At least 1 uppercase letter
* At least 1 lowercase letter
* At least 1 number
* At least 1 special character

Validation applies to:

* Password changes
* Password resets
* CSV imports

---

## Password Storage

Algorithm:

Argon2id

Requirements:

* Never store plaintext passwords
* Never log passwords
* Never expose passwords through APIs

Only password hashes are stored.

---

## First Login Password Change

Imported users must change their password during first login.

Field:

must_change_password

Workflow:

1. User logs in
2. Authentication succeeds
3. Redirect to password change page
4. Access blocked until password changed

---

## Password Reset

Authorized staff and administrators may reset passwords.

System actions:

* Hash password using Argon2id
* Set must_change_password = true
* Generate audit log

---

# User Management

## User Fields

* LRN
* First Name
* Last Name
* Status
* Created At
* Updated At

---

## User Status

### Active

Can log in.

### Suspended

Cannot log in.

### Archived

Cannot log in.

History remains available.

---

## Bulk User Import

### CSV Format

first_name,last_name,lrn,password

Example:

Juan,Dela Cruz,123456789012,SecurePassword@2026

---

### Validation Rules

Required:

* first_name
* last_name
* lrn
* password

LRN must be unique.

Password must satisfy password policy.

---

### Processing

For each row:

1. Validate
2. Hash password
3. Create user
4. Set must_change_password = true

Uploaded CSV files must be deleted after processing.

---

# Books

## Book

Represents a title.

Books are not directly borrowable.

Fields:

* ISBN
* Title
* Subtitle
* Authors
* Publisher
* Publication Year
* Description
* Categories
* Cover Image

---

# Inventory

## Book Copy

Represents a physical copy.

Example:

The Hobbit

* Copy 000001
* Copy 000002
* Copy 000003

Each copy maintains independent history.

---

## Copy Fields

* Copy ID
* Book
* Acquisition Date
* Shelf Location
* Notes
* Status

---

## Copy Status

* Available
* Borrowed
* Reserved
* Lost
* Damaged
* Under Repair
* Archived

---

## Copy History

History is append-only.

Examples:

* Created
* Borrowed
* Returned
* Damaged
* Repaired
* Lost
* Archived

---

# Loans

## Loan Fields

* User
* Book Copy
* Checkout Date
* Due Date
* Return Date
* Processed By

---

## Checkout Workflow

1. Search user
2. Search copy
3. Confirm checkout
4. Create loan
5. Update copy status

---

## Return Workflow

1. Search copy
2. Confirm return
3. Save return
4. Update copy status

---

# Checkout Requests

## Overview

Members can request checkout of a book through the web application.

Requests require staff approval.

---

## Request Status

* Pending
* Approved
* Rejected
* Cancelled
* Fulfilled

---

## Request Fields

* Request ID
* User
* Book
* Requested At
* Status
* Notes
* Processed By
* Processed At

---

## Member Workflow

1. Search book
2. Open book details
3. Request checkout
4. Submit request

System creates request.

Status = Pending

---

## Staff Workflow

Staff may:

* Approve
* Reject

When approved:

1. Select available copy
2. Create loan
3. Update copy status
4. Mark request as Fulfilled

---

# Dashboard

## Statistics

Display:

* Total Titles
* Total Copies
* Available Copies
* Borrowed Copies
* Reserved Copies
* Lost Copies
* Damaged Copies
* Total Members
* Overdue Loans

---

## Pending Requests

Display:

* Pending checkout requests
* Approved today
* Rejected today

---

## Recent Activity

Display:

* Recent loans
* Recent returns
* New users

---

## Overdue Loans

Display:

* User
* Book
* Copy ID
* Due Date
* Days Overdue

Actions:

* View User
* Mark Returned

---

# Book Inspection Page

When staff inspect a book they should see:

## Book Information

* Title
* Authors
* ISBN
* Publisher
* Publication Year
* Categories
* Description

---

## Inventory Summary

* Total Copies
* Available Copies
* Borrowed Copies
* Reserved Copies
* Lost Copies
* Damaged Copies

---

## Copy List

Display every physical copy.

Per copy:

* Copy ID
* Status
* Shelf Location
* Current Borrower

Actions:

* View Copy
* Edit Copy
* Archive Copy

---

## Active Loans

Display all active loans.

---

## Pending Requests

Display all pending checkout requests.

Actions:

* Approve
* Reject

---

## Book History

Display:

* Created
* Updated
* Archived

---

## Copy History

Display all events for each copy.

Examples:

* Created
* Borrowed
* Returned
* Damaged
* Repaired
* Lost
* Archived

---

# Bulk Data Import

## Overview

Booklat supports bulk imports to simplify migration and onboarding.

Supported imports:

* Users
* Books
* Books with Inventory
* Book Copies

Features:

* Validation
* Preview
* Duplicate detection
* Dry Run Mode
* Audit logging
* Transaction-based execution

---

## Import Workflow

1. Upload CSV
2. Parse file
3. Validate records
4. Display preview
5. Display warnings
6. Confirm import
7. Execute transaction
8. Generate import log

Failures must rollback the entire import.

No partial imports.

---

# Book Import

## CSV Format

isbn,title,author,publisher,publication_year,category

Example:

9780547928227,The Hobbit,J.R.R. Tolkien,Houghton Mifflin,1937,Fantasy

---

## Validation

Required:

* title

Duplicate detection:

* ISBN
* Title + Author

---

# Book + Inventory Import

## Purpose

Create books and copies simultaneously.

---

## CSV Format

isbn,title,author,copies

Example:

9780547928227,The Hobbit,J.R.R. Tolkien,5

---

## Processing

Creates:

Book:

The Hobbit

Copies:

* Copy 000001
* Copy 000002
* Copy 000003
* Copy 000004
* Copy 000005

Default status:

Available

---

# Copy Import

## CSV Format

copy_id,isbn,shelf_location,status

Example:

000001,9780547928227,Fiction-A-01,Available

---

## Validation

Required:

* copy_id
* isbn

Copy ID must be unique.

Referenced book must exist.

---

# Import Job History

Booklat stores history of import operations.

Fields:

* Job ID
* Import Type
* Performed By
* Started At
* Completed At
* Status
* Records Processed
* Records Created
* Validation Errors

---

## Status Values

* Pending
* Running
* Completed
* Failed

---

# Data Export

Purpose:

* Backups
* Reporting
* Migration
* Cleanup operations

Permission:

system.export_data

Administrator only.

---

## Exportable Data

### Users

* LRN
* First Name
* Last Name
* Status
* Created At

Passwords and password hashes must never be exported.

---

### Books

* ISBN
* Title
* Author
* Publisher
* Publication Year
* Category

---

### Copies

* Copy ID
* Book
* Status
* Shelf Location
* Acquisition Date

---

### Loans

* User LRN
* Copy ID
* Checkout Date
* Due Date
* Return Date

---

### Audit Logs

* Timestamp
* Actor
* Action
* Resource Type
* Resource ID

---

# Data Import Permissions

Permission:

system.import_data

Administrator only.

---

# Backups

## CSV Backups

Purpose:

* Migration
* Cleanup operations
* Human-readable exports

---

## Database Backups

Preferred disaster recovery mechanism:

PostgreSQL pg_dump

Benefits:

* Preserves relationships
* Preserves constraints
* Preserves indexes
* Preserves audit logs
* Preserves settings

CSV exports are not a replacement for database backups.

---

# Django Applications

config/
accounts/
books/
inventory/
loans/
requests_app/
audit/
dashboard/
core/

---

# Core Models

User
Role
Permission

Book
BookCopy
CopyHistory

Loan

CheckoutRequest

AuditLog

---

# MVP Deliverables

Authentication

* LRN login
* Argon2id passwords
* Password policy enforcement
* First-login password change

Users

* User management
* Bulk user import
* Password resets

Books

* Book management
* Book inspection page
* Bulk book import

Inventory

* Copy management
* Copy history
* Bulk copy import
* Book + inventory import

Loans

* Checkout
* Return
* Overdue tracking

Requests

* Checkout requests
* Staff approval workflow

Dashboard

* Statistics
* Pending requests
* Overdue loans
* Recent activity

Administration

* Audit logs
* Import history
* CSV exports
* CSV imports

Deployment

* Docker Compose
* PostgreSQL
* Redis
* Cloudflare Tunnel (production-only)
