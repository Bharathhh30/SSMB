# EAS build profiles

`eas.json` defines three build profiles:

- `development`: internal development-client builds for device testing.
- `preview`: internal staging builds.
- `production`: store-distribution builds with remote version management.

Before the first cloud build:

1. Sign in to the project's Expo account and run `npx eas-cli@latest init` from
   `mobile/` to link the project. The generated EAS project ID belongs in the
   Expo app config; never commit an access token.
2. Choose the permanent, globally unique iOS bundle identifier and Android
   application ID, then add them to `app.json`. Do not ship a placeholder ID.
3. In EAS, create the `development`, `preview`, and `production` environments.
   Set `EXPO_PUBLIC_API_BASE_URL` in each environment to that environment's
   HTTPS API base URL including `/api/v1`. These values are public app config,
   not secrets. Keep signing credentials and other secrets in EAS/GitHub secret
   stores.
4. Configure Apple and Google signing credentials through EAS, then build the
   `development` profile for both platforms before distributing the internal
   client. A successful JS export is not a substitute for a signed native
   device build.

Commands, from `mobile/`:

```powershell
npx eas-cli@latest build --platform all --profile development
npx eas-cli@latest build --platform all --profile preview
npx eas-cli@latest build --platform all --profile production
```

EAS project linking, final application IDs, signing, and store accounts are
deliberately not fabricated in this repository; they require the project
owner's Expo/Apple/Google accounts and permanent app identity.
