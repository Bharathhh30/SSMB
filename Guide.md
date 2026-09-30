# React Native + Backend Deployment Guide

A practical checklist for building and deploying a React Native application with a backend. Start with a focused MVP, then automate the repetitive parts as the project becomes stable.

## 1. Project Setup

Before coding:

- Define the MVP and its features.
- Decide the architecture.
- Choose the mobile stack: React Native + Expo.
- Choose the backend: Node.js + Express, FastAPI, or another suitable framework.
- Choose the database: MongoDB, PostgreSQL, or another suitable database.
- Create a Git repository.
- Create a `.gitignore` file.
- Create an `.env.example` file.
- Keep secrets out of Git.
- Decide how `development`, `staging`, and `production` environments will work.

A useful structure:

```text
my-app/
├── mobile/
│   ├── app/
│   ├── components/
│   ├── services/
│   ├── hooks/
│   └── ...
│
├── backend/
│   ├── src/
│   │   ├── controllers/
│   │   ├── routes/
│   │   ├── models/
│   │   ├── middleware/
│   │   └── services/
│   └── ...
│
├── README.md
└── .gitignore
```

## 2. Frontend Checklist

### UI

- Navigation
- Loading states
- Empty states
- Error states
- Form validation
- Keyboard handling
- Responsive layouts
- Dark/light mode, if required
- Accessibility

### API Integration

Create one API layer instead of making requests throughout the app:

```text
screens
   ↓
hooks
   ↓
services/api.ts
   ↓
backend
```

For example:

```ts
api.login()
api.getProfile()
api.getPosts()
api.createPost()
```

The API layer should:

- Centralize API calls.
- Handle HTTP errors.
- Handle network failures.
- Add request timeouts.
- Handle authentication and token expiration.
- Avoid hardcoded API URLs.

## 3. Backend Checklist

### API

- Define API routes.
- Separate controllers from services and business logic.
- Define database models.
- Validate requests.
- Add error handling.
- Implement authentication.
- Implement authorization.
- Add logging.

Example routes:

```text
POST   /auth/login
POST   /auth/register

GET    /users/me

GET    /posts
POST   /posts
DELETE /posts/:id
```

### Security

Before deployment:

- Hash passwords.
- Use secure JWT or session handling.
- Validate all user input.
- Add rate limiting.
- Configure CORS correctly.
- Keep secrets private.
- Do not return sensitive database fields.
- Use HTTPS in production.
- Configure proper database permissions.

## 4. Database

- Design the schema.
- Add indexes where needed.
- Handle relationships and references properly.
- Add validation.
- Create seed or test data if useful.
- Configure backups.
- Never expose database credentials to the mobile app.

The intended architecture is:

```text
React Native
     ↓
   API
     ↓
 Backend
     ↓
 Database
```

Never connect the mobile app directly to the database:

```text
React Native → Database
```

Database credentials must remain on the backend.

## 5. Environment Variables

Use separate configuration for each environment.

Development:

```env
API_URL=http://localhost:3000
```

Production:

```env
API_URL=https://api.myapp.com
```

For Expo, public configuration commonly uses variables such as:

```env
EXPO_PUBLIC_API_URL=https://api.myapp.com
```

Never put secrets such as database passwords or private API keys in `EXPO_PUBLIC_*` variables. Anything bundled into a mobile app should be considered potentially visible to the user.

## 6. Testing

You do not need 100% coverage for an MVP, but test the important paths.

### Frontend

- Navigation
- Forms
- Authentication
- API failures
- Different screen sizes

### Backend

- Important business logic
- API and integration behavior
- Authentication
- Validation

## 7. Git Workflow

For a personal project, keep the workflow simple:

```text
main
  ↑
feature branch
```

Example:

```bash
git checkout -b feature/auth
```

Finish the feature, open a pull request, and merge it into `main`.

Avoid creating branches such as `development`, `staging`, `qa`, `uat`, `pre-prod`, and `production` unless the project genuinely needs that complexity.

## 8. CI/CD

Use CI/CD, but keep it lightweight. A simple GitHub Actions pipeline is enough.

On every pull request:

```text
Push / PR
   ↓
Install dependencies
   ↓
Lint
   ↓
Type check
   ↓
Tests
   ↓
Build
```

If a required check fails, the pull request should not be merged.

## 9. Backend Deployment

A typical backend deployment flow is:

```text
GitHub
   ↓
GitHub Actions
   ↓
Tests
   ↓
Build
   ↓
Deploy
   ↓
Backend hosting
```

Possible hosting providers include:

- Render
- Railway
- Fly.io
- AWS
- Azure

Your production backend may use an address such as:

```text
https://api.yourapp.com
```

## 10. React Native and Expo Deployment

Expo provides a separate mobile build pipeline:

```text
Code
 ↓
GitHub
 ↓
CI
 ↓
EAS Build
 ↓
Android APK/AAB
 ↓
Google Play
```

For development:

```bash
npx expo start
```

For a development build:

```bash
eas build
```

For a production Android build:

```bash
eas build --platform android
```

Eventually, publish the release build to the Google Play Store.

## 11. Production Checklist

Before considering the app deployed:

- Production environment variables are configured.
- The production database is configured.
- HTTPS is enabled.
- CORS is configured.
- Authentication has been tested.
- Error handling is in place.
- Logging is available.
- Rate limiting is enabled.
- Database backups are configured.
- The app connects to the production API.
- An Android release build has been tested.
- Crash monitoring is configured.
- Basic analytics are configured.
- A privacy policy is available if applicable.
- App permissions have been reviewed.

## 12. Recommended Workflow

Since you are already familiar with React, Node.js, and GitHub Actions, use this setup:

```text
                 DEVELOPMENT

React Native + Expo          Node/Express
       │                           │
       │                           │
       └────────── API ────────────┘
                    │
                 Database

                 GITHUB

              feature branch
                    │
                   PR
                    ↓
             GitHub Actions
          ┌─────────┼─────────┐
          ↓         ↓         ↓
        Lint      Tests     Build
          └─────────┼─────────┘
                    ↓
                  main
                    │
             ┌──────┴──────┐
             ↓             ↓
          Backend        EAS Build
          Deploy          ↓
             ↓         Android
          Production      ↓
                       Play Store
```

## Guiding Rule

**Build normally first. Automate the repetitive parts.**

Do not spend several days creating CI/CD before the app exists.

### Suggested Timeline

**Day 1**

- Expo app
- Backend
- Database
- Git repository

**During development**

- Feature branches
- Pull requests

**Once the app works**

- GitHub Actions for linting, testing, and building

**Before launch**

- Automated backend deployment
- EAS production builds

This gives you a professional workflow without turning a small React Native project into a DevOps project.
