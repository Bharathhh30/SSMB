# Mobile dependency audit finding — 2026-10-16

The locked mobile dependency tree currently reports two high-severity
transitive advisories:

| Package | Locked version | Dependency path | Advisory | npm fix available |
|---|---:|---|---|---|
| `braces` | `3.0.3` | `expo` → `@expo/cli` → Metro file-map → `micromatch` → `braces` | `GHSA-vfj7-8cjw-p6xm` | No |
| `node-forge` | `1.4.0` | `expo` → `@expo/cli` → `@expo/code-signing-certificates` → `node-forge` | `GHSA-86w9-cpqp-85rv` | No |

These are currently in the Expo CLI/Metro/signing toolchain path. This note
does **not** assert that they are absent from every build artifact and is not a
production security waiver. Do not hide them with a blanket audit threshold,
`npm audit fix --force`, or an unreviewed fork. The CI audit remains
fail-closed until compatible upstream fixes are available or the project owner
records an explicit, time-bounded risk disposition.

Re-run `npm audit --json` after Expo SDK-compatible dependency updates. Remove
this note only after the vulnerable versions are gone from the lockfile and the
high/critical audit is clean.
