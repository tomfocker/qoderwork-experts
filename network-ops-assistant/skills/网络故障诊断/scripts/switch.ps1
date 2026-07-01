<#
.SYNOPSIS
    快速开关交换机端口网络（VLAN切换）
.PARAMETER Port
    端口号，如 21 表示 GE0/0/21
.PARAMETER Action
    on = VLAN 1210（开通） / off = VLAN 444（隔离）
.EXAMPLE
    .\switch.ps1 -Port 21 -Action off
    .\switch.ps1 -Port 21 -Action on
#>
param(
    [Parameter(Mandatory)] [int]$Port,
    [Parameter(Mandatory)] [ValidateSet("on","off")] [string]$Action
)

$ip = "172.16.20.217"
$pw = "xxzx5331101"
$vlan = if ($Action -eq "on") { "1210" } else { "444" }
$label = if ($Action -eq "on") { "ENABLE" } else { "ISOLATE" }

Write-Host ">>> $label GE0/0/$Port ..." -ForegroundColor Yellow

$c = New-Object System.Net.Sockets.TcpClient
$c.ReceiveTimeout = 5000; $c.SendTimeout = 5000
$c.Connect($ip, 23)
$s = $c.GetStream()
Start-Sleep -Milliseconds 800
$b = [byte[]]::new(4096)
while ($s.DataAvailable) { $s.Read($b, 0, 4096) | Out-Null }

$e = [Text.Encoding]::ASCII
$d = $e.GetBytes("$pw`r`n"); $s.Write($d, 0, $d.Length)
Start-Sleep -Milliseconds 1500
while ($s.DataAvailable) { $s.Read($b, 0, 4096) | Out-Null }

# Enter system view, set port VLAN, quit
$cmds = @(
    "sys",
    "int g0/0/$Port",
    "port default vlan $vlan",
    "quit",
    "quit",
    "disp port vlan g0/0/$Port",
    "save",
    "y"
)

foreach ($cmd in $cmds) {
    $d = $e.GetBytes("$cmd`r`n"); $s.Write($d, 0, $d.Length)
    Start-Sleep -Milliseconds 800
    while ($s.DataAvailable) {
        $r = $s.Read($b, 0, $b.Length)
        Write-Host ($e.GetString($b, 0, $r).Trim()) -NoNewline
    }
}

$d = $e.GetBytes("quit`r`n"); $s.Write($d, 0, $d.Length)
$c.Close()
Write-Host "`n$label GE0/0/$Port done" -ForegroundColor Green
