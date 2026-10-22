param(
  [string]$ApiBaseUrl = "http://127.0.0.1:8000/api/v1",
  [string]$MailpitBaseUrl = "http://127.0.0.1:8025"
)

$ErrorActionPreference = "Stop"
$email = "backend-smoke-$([guid]::NewGuid().ToString('N'))@example.com"
$initialPassword = "Local-Only-Passphrase-2026!"
$resetPassword = "Reset-Only-Passphrase-2026!"

function Invoke-JsonPost {
  param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][object]$Body,
    [hashtable]$Headers = @{}
  )

  $json = ConvertTo-Json -InputObject $Body -Depth 5
  Invoke-RestMethod `
    -Method Post `
    -Uri "$ApiBaseUrl$Path" `
    -ContentType "application/json" `
    -Headers $Headers `
    -Body $json
}

function Wait-ForEmailToken {
  param([Parameter(Mandatory = $true)][string]$Subject)

  for ($attempt = 0; $attempt -lt 30; $attempt += 1) {
    $listing = Invoke-RestMethod -Uri "$MailpitBaseUrl/api/v1/messages"
    $message = $listing.messages |
      Where-Object {
        $recipientAddresses = @($_.To | ForEach-Object { $_.Address })
        $_.Subject -eq $Subject -and $recipientAddresses -contains $email
      } |
      Select-Object -First 1

    if ($null -ne $message) {
      $detail = Invoke-RestMethod -Uri "$MailpitBaseUrl/api/v1/message/$($message.ID)"
      $match = [regex]::Match(
        [string]$detail.Text,
        '"token"\s*:\s*"(?<token>[^"]+)"'
      )
      if ($match.Success) {
        return $match.Groups["token"].Value
      }
    }

    Start-Sleep -Milliseconds 500
  }

  throw "Timed out waiting for '$Subject' in Mailpit for $email."
}

function Assert-HttpFailure {
  param(
    [Parameter(Mandatory = $true)][scriptblock]$Request,
    [Parameter(Mandatory = $true)][int]$ExpectedStatus
  )

  try {
    & $Request | Out-Null
  } catch {
    $response = $_.Exception.Response
    if ($null -ne $response -and [int]$response.StatusCode -eq $ExpectedStatus) {
      return
    }
    throw
  }

  throw "Expected HTTP $ExpectedStatus, but the request succeeded."
}

$registration = Invoke-JsonPost -Path "/auth/register" -Body @{
  email = $email
  password = $initialPassword
  display_name = "Backend smoke test"
}
if ($registration.message -notlike "If the address is eligible,*") {
  throw "Unexpected registration response."
}

$verificationToken = Wait-ForEmailToken -Subject "Verify your Community account"
$verification = Invoke-JsonPost -Path "/auth/verify-email" -Body @{ token = $verificationToken }
if ($verification.message -ne "Email verified. You can now sign in.") {
  throw "Email verification did not complete."
}

Assert-HttpFailure -ExpectedStatus 400 -Request {
  Invoke-JsonPost -Path "/auth/verify-email" -Body @{ token = $verificationToken }
}

$login = Invoke-JsonPost -Path "/auth/login" -Body @{
  email = $email
  password = $initialPassword
}
$authHeaders = @{ Authorization = "Bearer $($login.access_token)" }
$profile = Invoke-RestMethod -Uri "$ApiBaseUrl/auth/me" -Headers $authHeaders
if ($profile.email -ne $email) {
  throw "Authenticated profile returned an unexpected email."
}

$profileDraft = Invoke-RestMethod `
  -Method Patch `
  -Uri "$ApiBaseUrl/profile/me" `
  -ContentType "application/json" `
  -Headers $authHeaders `
  -Body (ConvertTo-Json -InputObject @{
    display_name = "Backend smoke profile"
    interests = @("backend")
  } -Depth 5)
if ($profileDraft.display_name -ne "Backend smoke profile" -or $profileDraft.interests.Count -ne 1) {
  throw "Private profile update did not persist."
}

$profileDraft = Invoke-RestMethod `
  -Method Patch `
  -Uri "$ApiBaseUrl/profile/me" `
  -ContentType "application/json" `
  -Headers $authHeaders `
  -Body (ConvertTo-Json -InputObject @{ interests = @("native") } -Depth 5)
if ($profileDraft.interests.Count -ne 2 -or $profileDraft.interests[1] -ne "native") {
  throw "Profile PATCH replaced existing interests instead of adding the new interest."
}

$refreshed = Invoke-JsonPost -Path "/auth/refresh" -Body @{
  refresh_token = $login.refresh_token
}
if ($refreshed.access_token -eq $login.access_token) {
  throw "Refresh did not rotate the access token."
}

Assert-HttpFailure -ExpectedStatus 401 -Request {
  Invoke-JsonPost -Path "/auth/refresh" -Body @{
    refresh_token = $login.refresh_token
  }
}

Invoke-JsonPost -Path "/auth/password/forgot" -Body @{ email = $email } | Out-Null
$resetToken = Wait-ForEmailToken -Subject "Reset your Community password"
Invoke-JsonPost -Path "/auth/password/reset" -Body @{
  token = $resetToken
  new_password = $resetPassword
} | Out-Null

Assert-HttpFailure -ExpectedStatus 401 -Request {
  Invoke-JsonPost -Path "/auth/login" -Body @{
    email = $email
    password = $initialPassword
  }
}

$newLogin = Invoke-JsonPost -Path "/auth/login" -Body @{
  email = $email
  password = $resetPassword
}
Invoke-RestMethod `
  -Method Post `
  -Uri "$ApiBaseUrl/auth/logout" `
  -Headers @{ Authorization = "Bearer $($newLogin.access_token)" } | Out-Null

Write-Host "Authentication smoke flow passed."
Write-Host "Test account: $email"
Write-Host "Test password after reset: $resetPassword (local test only)"
Write-Host "Mailpit inbox: $MailpitBaseUrl"
Write-Host "The generated test account remains in the configured development database."
