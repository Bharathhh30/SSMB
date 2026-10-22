const assert = require("node:assert/strict");
const test = require("node:test");

const { evaluateAuditReport } = require("./audit-with-allowlist.cjs");

const expiresOn = "2026-11-05";
const approvedPolicy = {
  expires_on: expiresOn,
  known_breaking_fix: {
    name: "expo",
    version: "44.0.6",
    is_semver_major: true,
  },
  exceptions: [
    {
      advisory: "GHSA-vfj7-8cjw-p6xm",
      package: "braces",
      severity: "high",
      reason: "No compatible fix is available yet.",
    },
    {
      advisory: "GHSA-86w9-cpqp-85rv",
      package: "node-forge",
      severity: "high",
      reason: "No compatible fix is available yet.",
    },
  ],
};

function advisory(name, id, { severity = "high", fixAvailable = false } = {}) {
  return {
    severity,
    via: [
      {
        name,
        severity,
        url: `https://github.com/advisories/${id}`,
      },
    ],
    fixAvailable,
  };
}

test("allows only the approved high advisories and their transitive dependency chain", () => {
  const report = {
    vulnerabilities: {
      braces: advisory("braces", "GHSA-vfj7-8cjw-p6xm"),
      micromatch: { severity: "high", via: ["braces"], fixAvailable: false },
      "node-forge": advisory("node-forge", "GHSA-86w9-cpqp-85rv"),
      expo: { severity: "high", via: ["node-forge"], fixAvailable: false },
    },
  };

  const result = evaluateAuditReport(report, approvedPolicy, "2026-10-22");

  assert.deepEqual(result.errors, []);
  assert.deepEqual(
    result.accepted.map((item) => item.advisory).sort(),
    ["GHSA-86w9-cpqp-85rv", "GHSA-vfj7-8cjw-p6xm"],
  );
});

test("fails on any unapproved high advisory", () => {
  const report = {
    vulnerabilities: {
      braces: advisory("braces", "GHSA-vfj7-8cjw-p6xm"),
      vite: advisory("vite", "GHSA-0000-0000-0000"),
    },
  };

  const result = evaluateAuditReport(report, approvedPolicy, "2026-10-22");

  assert.ok(result.errors.some((error) => error.includes("Unapproved high-severity advisory")));
});

test("fails if an audit exception has expired", () => {
  const report = {
    vulnerabilities: {
      braces: advisory("braces", "GHSA-vfj7-8cjw-p6xm"),
    },
  };

  const result = evaluateAuditReport(report, approvedPolicy, "2026-11-07");

  assert.ok(result.errors.some((error) => error.includes("expired")));
});

test("fails an expired exception even after the advisory disappears", () => {
  const result = evaluateAuditReport(
    { vulnerabilities: {} },
    approvedPolicy,
    "2026-11-07",
  );

  assert.ok(result.errors.some((error) => error.includes("expired")));
});

test("permits only the specifically recorded breaking Expo downgrade", () => {
  const report = {
    vulnerabilities: {
      braces: advisory("braces", "GHSA-vfj7-8cjw-p6xm", {
        fixAvailable: { name: "expo", version: "44.0.6", isSemVerMajor: true },
      }),
    },
  };

  const result = evaluateAuditReport(report, approvedPolicy, "2026-10-22");

  assert.deepEqual(result.errors, []);
});

test("fails if npm proposes a different forced downgrade", () => {
  const report = {
    vulnerabilities: {
      braces: advisory("braces", "GHSA-vfj7-8cjw-p6xm", {
        fixAvailable: { name: "expo", version: "45.0.0", isSemVerMajor: true },
      }),
    },
  };

  const result = evaluateAuditReport(report, approvedPolicy, "2026-10-22");

  assert.ok(result.errors.some((error) => error.includes("unapproved remediation")));
});

test("fails if npm reports a compatible fix for an excepted advisory", () => {
  const report = {
    vulnerabilities: {
      braces: advisory("braces", "GHSA-vfj7-8cjw-p6xm", {
        fixAvailable: { name: "braces", version: "3.0.4", isSemVerMajor: false },
      }),
    },
  };

  const result = evaluateAuditReport(report, approvedPolicy, "2026-10-22");

  assert.ok(result.errors.some((error) => error.includes("unapproved remediation")));
});

test("fails closed when a high finding cannot be traced to an advisory", () => {
  const report = {
    vulnerabilities: {
      metro: { severity: "high", via: ["missing-package"], fixAvailable: false },
    },
  };

  const result = evaluateAuditReport(report, approvedPolicy, "2026-10-23");

  assert.ok(result.errors.some((error) => error.includes("Could not trace")));
});
