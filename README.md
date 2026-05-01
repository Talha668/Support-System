@"
# 🎫 Support Ticket Management System

A comprehensive, production-ready customer support ticket management system built with Django and Django REST Framework. This system helps organizations manage customer support tickets, track agent performance, enforce SLA compliance, and provide tiered support based on customer subscription levels.

![Django](https://img.shields.io/badge/Django-5.0-green)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Installation Guide](#-installation-guide)
- [Configuration](#-configuration)
- [Testing Guide](#-testing-guide)
- [API Documentation](#-api-documentation)
- [Data Models](#-data-models)
- [Management Commands](#-management-commands)
- [Troubleshooting](#-troubleshooting)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### Core Functionality
- 🎫 **Ticket Management**: Create, view, update, and resolve support tickets
- 👥 **Agent Management**: Track agents, their teams, skills, and workload
- ⏰ **SLA Enforcement**: Automated SLA deadline calculation based on customer tier and priority
- 📊 **Dashboard Analytics**: Real-time metrics on ticket status, agent performance, and SLA compliance
- 🔔 **Notifications & Alerts**: SLA breach warnings, assignment notifications, escalation alerts
- 🎯 **Intelligent Assignment**: Skills-based, workload-balanced, and round-robin ticket assignment

### Customer Support Features
- 👑 **Multi-Tier Support**: Basic, Pro, and Enterprise customer tiers
- 🚨 **Priority Levels**: Low, Medium, High, and Urgent ticket priorities
- 📞 **Multi-Channel**: Phone calls, emails, live chat, web forms, and API
- 🏷️ **Issue Categorization**: Technical, Billing, Integration, Onboarding, Account Management
- 📈 **SLA Compliance Tracking**: Response time and resolution time monitoring
- 🔄 **Escalation Management**: Automatic escalation rules based on conditions

### Business Intelligence
- 📉 **Performance Metrics**: Agent workload, resolution rates, customer satisfaction
- ⏱️ **Time Tracking**: First response time, resolution time, business hours calculation
- 📊 **Trend Analysis**: Ticket creation trends, SLA compliance rates over time

---

## 🛠️ Tech Stack

| Category | Technology | Version |
|----------|------------|---------|
| **Backend Framework** | Django | 5.0.2 |
| **REST API** | Django REST Framework | 3.14.0 |
| **Database** | PostgreSQL (Production) / SQLite (Development) | 15+ |
| **Authentication** | JWT (Simple JWT) | 5.3.1 |
| **Task Queue** | Celery + Redis | 5.3+ |
| **API Documentation** | Swagger / ReDoc | - |
| **CORS** | Django CORS Headers | 4.3.1 |
| **Filters** | Django Filter | 23.5 |
| **Python** | Python | 3.10+ |

---
# Start server first, then in another terminal:

# Test API root
curl http://127.0.0.1:8000/api/v1/

# List all tickets
curl http://127.0.0.1:8000/api/v1/support/tickets/?format=json

# Get single ticket
curl http://127.0.0.1:8000/api/v1/support/tickets/T-1001/?format=json

# List all agents
curl http://127.0.0.1:8000/api/v1/support/agents/?format=json

# List all teams
curl http://127.0.0.1:8000/api/v1/support/teams/?format=json

# List SLA rules
curl http://127.0.0.1:8000/api/v1/support/sla-rules/?format=json

# Filter tickets by status
curl "http://127.0.0.1:8000/api/v1/support/tickets/?status=open&format=json"

# Filter tickets by priority
curl "http://127.0.0.1:8000/api/v1/support/tickets/?priority=urgent&format=json"

# Search tickets
curl "http://127.0.0.1:8000/api/v1/support/tickets/?search=payment&format=json"




## 📁 Project Structure
