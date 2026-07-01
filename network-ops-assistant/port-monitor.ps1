param(
    [string]$SwitchIP = "172.16.20.217",
    [int]$SwitchPort = 23,
    [string]$Password = "xxzx5331101",
    [string]$MonitorInterface = "GigabitEthernet0/0/19",
    [string]$NotifyTo = "1448960082@qq.com",
    [string]$StateFile = "$PSScriptRoot\port19_state.txt"
)

# === Telnet session ===
$tcp = New-Object System.Net.Sockets.TcpClient
try {
    $tcp.Connect($SwitchIP, $SwitchPort)
} catch {
    Write-Host "ERROR: Cannot connect to ${SwitchIP}:${SwitchPort}"
    exit 1
}
$stream = $tcp.GetStream()
$stream.ReadTimeout = 8000

$buffer = New-Object byte[] 4096
$stream.Read($buffer, 0, $buffer.Length) | Out-Null

$passBytes = [System.Text.Encoding]::ASCII.GetBytes("${Password}`r`n")
$stream.Write($passBytes, 0, $passBytes.Length)
Start-Sleep -Seconds 2

$buffer2 = New-Object byte[] 8192
$stream.Read($buffer2, 0, $buffer2.Length) | Out-Null

function Send-Cmd([string]$cmd, [int]$wait = 2000) {
    $cmdBytes = [System.Text.Encoding]::ASCII.GetBytes("${cmd}`r`n")
    $stream.Write($cmdBytes, 0, $cmdBytes.Length)
    Start-Sleep -Milliseconds $wait
    $all = ""
    $buf = New-Object byte[] 32768
    $stream.ReadTimeout = 3000
    while ($true) {
        try {
            $n = $stream.Read($buf, 0, $buf.Length)
            if ($n -gt 0) {
                $all += [System.Text.Encoding]::Default.GetString($buf, 0, $n)
                if ($all -match "---- More ----") {
                    $sp = [System.Text.Encoding]::ASCII.GetBytes(" ")
                    $stream.Write($sp, 0, $sp.Length)
                    $all = $all -replace "---- More ----", ""
                    Start-Sleep -Milliseconds 500
                } else { break }
            } else { break }
        } catch { break }
    }
    return $all
}

Send-Cmd "screen-length 0 temporary" 1000 | Out-Null
$output = Send-Cmd "display interface brief" 4000

$quitBytes = [System.Text.Encoding]::ASCII.GetBytes("quit`r`n")
$stream.Write($quitBytes, 0, $quitBytes.Length)
$tcp.Close()

# === Parse status - look for GE0/0/19 line ===
$currentStatus = "unknown"
$lines = $output -split "`n"
foreach ($line in $lines) {
    $trimmed = $line.Trim()
    if ($trimmed -match "GigabitEthernet0/0/19\s+(up|down|\*down)\s+(up|down)") {
        $phyStatus = $Matches[1]
        $protoStatus = $Matches[2]
        if ($phyStatus -eq "up" -and $protoStatus -eq "up") {
            $currentStatus = "up"
        } else {
            $currentStatus = "down"
        }
        break
    }
}

Write-Host "Interface: $MonitorInterface"
Write-Host "Current Status: $currentStatus"

# === Compare with last known state ===
$lastStatus = "unknown"
if (Test-Path $StateFile) {
    $lastStatus = (Get-Content $StateFile -Raw).Trim()
}

Write-Host "Last Known Status: $lastStatus"

if ($currentStatus -ne $lastStatus -and $currentStatus -ne "unknown") {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

    if ($currentStatus -eq "down") {
        $subject = "[ALERT] GE0/0/19 DOWN - $timestamp"
        $body = "Switch YouJiaoLou-F2-1-3 ($SwitchIP) GE0/0/19 is DOWN. Time: $timestamp Previous: $lastStatus Current: $currentStatus"
    } else {
        $subject = "[OK] GE0/0/19 UP - $timestamp"
        $body = "Switch YouJiaoLou-F2-1-3 ($SwitchIP) GE0/0/19 recovered UP. Time: $timestamp Previous: $lastStatus Current: $currentStatus"
    }

    Write-Host "Status CHANGED! Sending notification..."

    $sendResult = agently-cli message +send --to $NotifyTo --subject $subject --body $body 2>&1
    $sendStr = "$sendResult"
    if ($sendStr -match '(ctk_[a-zA-Z0-9_-]+)') {
        $token = $Matches[1]
        $confirmResult = agently-cli message +send --to $NotifyTo --subject $subject --body $body --confirmation-token $token 2>&1
        Write-Host "Email sent to $NotifyTo"
    } else {
        Write-Host "WARNING: Failed to extract confirmation token"
        Write-Host $sendStr
    }

    $currentStatus | Out-File -FilePath $StateFile -NoNewline
} else {
    Write-Host "No change. Skipping notification."
    if (-not (Test-Path $StateFile)) {
        $currentStatus | Out-File -FilePath $StateFile -NoNewline
    }
}
