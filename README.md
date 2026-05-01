# GreenGig Africa – Backend

Backend service for the GreenGig Africa platform.

## Overview

This repository contains the backend system responsible for powering core platform workflows such as authentication, task management, proof-of-work handling, and organization operations.

The backend is designed to support a mobile-first, low-bandwidth environment and enable reliable execution and verification of climate micro-jobs.

---

## Responsibilities (Backend Track)

### Authentication
- Phone number + OTP-based login  
- Role-based access (Job Seeker, Volunteer, Organization)  

### Task Management APIs
- Create, update, and manage tasks (organization side)  
- Fetch and filter tasks (user side)  
- Task acceptance and assignment handling  

### Task Workflow Management
- Handle task lifecycle states:  
  Post → Accept → In Progress → Submitted → Verified  
- Maintain status updates for users and organizations  

### Proof of Work Handling
- Upload and store images (start, during, completion)  
- Capture and store GPS coordinates  
- Capture timestamps for each submission  
- Provide data for verification by organizations  

### Organization Module
- Organization registration and data handling  
- Approval status management  
- Task ownership and control  

### Volunteer Support
- Track completed tasks  
- Store and update impact data (e.g., tasks completed, contributions)  
- Provide data for certificate generation  

---

## AI Integration (Handled by AI Track)

- Backend exposes APIs for:
  - Job matching inputs/outputs  
  - Image validation requests and responses  
- AI/ML logic is implemented by the AI track and consumed via backend endpoints  

---

## Backend Scope

- REST API development  
- Database design and management  
- File upload and storage handling  
- Authentication and authorization  
- Role-based access control  
- Integration endpoints for frontend and AI services  

---

## Core Workflows

- User signup → OTP verification  
- Organization posts task → stored in system  
- User accepts task → assignment created  
- User submits proof → stored with metadata  
- Organization reviews → status updated  

---

## MVP Scope

### Included
- OTP authentication  
- Task APIs (create, read, accept)  
- Proof-of-work upload and storage  
- Organization management APIs  
- Task status management  
- AI integration endpoints  

### Out of Scope
- Payment processing  
- Push notifications  
- Offline support  
- Mobile application logic  

---

## Status

Backend APIs in development — supporting frontend and AI track integration.

---

## Team

Team 16 – GreenGig Africa  
Backend Track
