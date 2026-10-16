# Local prototype URLs

The prototype needs only the local Expo server and local FastAPI service. No
public website, custom domain, EAS project, or app-store identifier is needed
to run it in Expo Go.

1. Copy `.env.example` to `.env.development.local`.
2. Keep the default `EXPO_PUBLIC_API_BASE_URL` for an iOS Simulator on the
   development Mac: `http://127.0.0.1:8000/api/v1`.
3. For the Android emulator, use `http://10.0.2.2:8000/api/v1`.
4. For a physical phone, use the computer's LAN address, for example
   `http://192.168.1.20:8000/api/v1`. Start FastAPI with `--host 0.0.0.0`,
   keep both devices on the same trusted Wi-Fi, and allow the local API port
   through the computer firewall if prompted.
5. From `mobile/`, run `npm run start -- --go --lan` and scan the QR code with
   Expo Go. The API URL and Expo/Metro URL are separate.

Restart Expo after changing `.env.development.local`. `EXPO_PUBLIC_*` values
are bundled into the app and are public; never put credentials or secrets there.

## Sharing later

After the prototype is approved for remote testing, expose the backend through
its own temporary HTTPS tunnel and update only `EXPO_PUBLIC_API_BASE_URL`.
An Expo tunnel serves the JavaScript bundle; it does not expose FastAPI. Never
tunnel PostgreSQL. Permanent domains, EAS environments, signing, and store
distribution are intentionally deferred until the final prototype is approved.
