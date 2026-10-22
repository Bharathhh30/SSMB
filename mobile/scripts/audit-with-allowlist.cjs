const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const mobileRoot = path.resolve(__dirname, "..");
const policyPath = path.join(mobileRoot, "security", "audit-exceptions.json");
const severityRank = { low: 1, moderate: 2, high: 3, critical: 4 };

function isIsoDate(value) {
  return (
    /^\d{4}-\d{2}-\d{2}$/.test(value ?? "") &&
    !Number.isNaN(Date.parse(`${value}T00:00:00Z`)) &&
    new Date(`${value}T00:00:00Z`).toISOString().slice(0, 10) === value
  );
}

function advisoryIdFromUrl(url) {
  return url?.match(/GHSA-[a-z0-9-]+/i)?.[0].toUpperCase();
}

function collectRootAdvisories(packageName, vulnerabilities, ancestry = new Set()) {
  if (ancestry.has(packageName)) {
    return [];
  }

  const vulnerability = vulnerabilities[packageName];
  if (!vulnerability) {
    return [];
  }

  const nextAncestry = new Set(ancestry);
  nextAncestry.add(packageName);
  const advisories = [];

  for (const via of vulnerability.via ?? []) {
    if (typeof via === "string") {
      advisories.push(...collectRootAdvisories(via, vulnerabilities, nextAncestry));
      continue;
    }

    const advisory = advisoryIdFromUrl(via.url);
    if (advisory) {
      advisories.push({
        advisory,
        package: via.name ?? packageName,
        severity: via.severity ?? vulnerability.severity,
        fixAvailable: vulnerability.fixAvailable,
      });
    }
  }

  return [
    ...new Map(
      advisories.map((item) => [`${item.advisory}:${item.package}`, item]),
    ).values(),
  ];
}

function evaluateAuditReport(report, policy, today = new Date().toISOString().slice(0, 10)) {
  const errors = [];
  const accepted = new Map();
  const exceptions = new Map();
  if (!isIsoDate(policy.expires_on)) {
    errors.push("Audit exception policy must contain a valid expires_on date.");
  }
  if (!isIsoDate(today)) {
    errors.push("Audit checker received an invalid current date.");
  }

  for (const exception of policy.exceptions ?? []) {
    if (
      !exception.advisory ||
      !exception.package ||
      exception.severity !== "high" ||
      !exception.reason
    ) {
      errors.push("Invalid or overly broad audit exception policy entry.");
      continue;
    }
    if (today > policy.expires_on) {
      errors.push(
        `Temporary audit exception ${exception.advisory} expired on ${policy.expires_on}.`,
      );
    }
    const normalizedAdvisory = exception.advisory.toUpperCase();
    if (exceptions.has(normalizedAdvisory)) {
      errors.push(`Duplicate audit exception for ${exception.advisory}.`);
    }
    exceptions.set(normalizedAdvisory, exception);
  }

  const vulnerabilities = report.vulnerabilities ?? {};
  for (const [packageName, vulnerability] of Object.entries(vulnerabilities)) {
    if ((severityRank[vulnerability.severity] ?? 0) < severityRank.high) {
      continue;
    }

    const rootAdvisories = collectRootAdvisories(packageName, vulnerabilities).filter(
      (item) => (severityRank[item.severity] ?? 0) >= severityRank.high,
    );
    if (rootAdvisories.length === 0) {
      errors.push(`Could not trace high-severity finding for ${packageName} to an advisory.`);
      continue;
    }

    for (const finding of rootAdvisories) {
      const exception = exceptions.get(finding.advisory.toUpperCase());
      if (!exception || exception.package !== finding.package) {
        errors.push(
          `Unapproved high-severity advisory ${finding.advisory} affecting ${finding.package}.`,
        );
        continue;
      }
      if (finding.severity !== exception.severity) {
        errors.push(
          `Audit exception ${finding.advisory} is only approved for ${exception.severity}, not ${finding.severity}.`,
        );
        continue;
      }
      if (finding.fixAvailable !== false) {
        errors.push(
          `A fix is now available for ${finding.advisory}; remove the exception and update the dependency.`,
        );
        continue;
      }
      accepted.set(finding.advisory, exception);
    }
  }

  return { errors, accepted: [...accepted.values()] };
}

function run() {
  const policy = JSON.parse(fs.readFileSync(policyPath, "utf8"));
  const npmExecPath = process.env.npm_execpath;
  let command;
  let args;
  if (npmExecPath) {
    command = process.execPath;
    args = [npmExecPath, "audit", "--audit-level=high", "--json"];
  } else if (process.platform === "win32") {
    command = process.env.ComSpec || "cmd.exe";
    args = ["/d", "/s", "/c", "npm.cmd audit --audit-level=high --json"];
  } else {
    command = "npm";
    args = ["audit", "--audit-level=high", "--json"];
  }
  const result = spawnSync(command, args, {
    cwd: mobileRoot,
    encoding: "utf8",
    maxBuffer: 32 * 1024 * 1024,
  });

  if (result.error) {
    console.error(`Could not run npm audit: ${result.error.message}`);
    process.exitCode = 1;
    return;
  }
  if (result.status !== 0 && result.status !== 1) {
    console.error(result.stderr || `npm audit exited with status ${result.status}.`);
    process.exitCode = 1;
    return;
  }

  let report;
  try {
    report = JSON.parse(result.stdout);
  } catch {
    console.error("npm audit did not return valid JSON.");
    console.error(result.stderr);
    process.exitCode = 1;
    return;
  }

  const { errors, accepted } = evaluateAuditReport(report, policy);
  for (const exception of accepted) {
    console.warn(
      `TEMPORARY AUDIT EXCEPTION: ${exception.advisory} (${exception.package}, ${exception.severity}); ` +
        `expires ${policy.expires_on}. ${exception.reason}`,
    );
  }
  if (errors.length > 0) {
    for (const error of errors) {
      console.error(error);
    }
    process.exitCode = 1;
    return;
  }

  console.log("npm audit passed with only the documented, time-limited exceptions above.");
}

if (require.main === module) {
  run();
}

module.exports = { evaluateAuditReport };
