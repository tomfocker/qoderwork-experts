<#
.SYNOPSIS
    华为/H3C 交换机 Telnet 远程执行工具 - 一条命令完成连接/执行/返回

.PARAMETER Ip      交换机 IP
.PARAMETER Password 登录密码
.PARAMETER Cmd      命令，多条用分号分隔
.PARAMETER Wait     每条命令等待秒数(默认3)

.EXAMPLE
    .\telnet_diag.ps1 -Ip 172.16.20.217 -Password xxx -Cmd "disp interface g0/0/13"
    .\telnet_diag.ps1 -Ip 172.16.20.217 -Password xxx -Cmd "sys;int g0/0/21;port default vlan 444;quit;quit"
#>
param([Parameter(Mandatory)][string]$Ip,[Parameter(Mandatory)][string]$Password,[string]$Cmd="",[int]$Wait=3)
$e=[Text.Encoding]::ASCII;$c=New-Object System.Net.Sockets.TcpClient
$c.ReceiveTimeout=10000;$c.SendTimeout=5000;$c.Connect($Ip,23);$s=$c.GetStream()
Sleep -Milliseconds 1000;$b=[byte[]]::new(65536)
while($s.DataAvailable){$s.Read($b,0,$b.Length)|Out-Null}
$d=$e.GetBytes("$Password`r`n");$s.Write($d,0,$d.Length);Sleep -Milliseconds 2000
while($s.DataAvailable){$s.Read($b,0,$b.Length)|Out-Null}
if(!$Cmd){$c.Close();exit}
$Cmd -split ';'|?{$_.Trim()}|%{$t=$_.Trim()
    $d=$e.GetBytes("$t`r`n");$s.Write($d,0,$d.Length);Sleep -Seconds $Wait
    $r="";$p=0;do{$hd=$false;while($s.DataAvailable){$hd=$true
            $n=$s.Read($b,0,$b.Length);$r+=$e.GetString($b,0,$n)}
        if($r -match "---- More ----\s*$" -and $p -lt 50){$p++
            $r=$r -replace '---- More ----\s*',''
            $d=$e.GetBytes(" ");$s.Write($d,0,$d.Length);Sleep -Milliseconds 500}else{break}}while($hd)
    Write-Host $r.Trim()}
$d=$e.GetBytes("quit`r`n");$s.Write($d,0,$d.Length);$c.Close()
