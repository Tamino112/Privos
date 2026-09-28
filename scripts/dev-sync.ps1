param(
    [Parameter(Mandatory)]
    [string]$VmHost,
    [string]$User = $env:PRIVOS_VM_USER
)

# Überträgt system_files/ per SSH in eine installierte Privos-VM, ohne Image- oder ISO-Build.
# /usr wird dafür mit `bootc usr-overlay` vorübergehend beschreibbar; nach einem Neustart
# gilt wieder das installierte Image. Dauerhaft wird eine Änderung erst mit einem neuen Image.

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$target = if ($User) { "$User@$VmHost" } else { $VmHost }
$archive = Join-Path ([IO.Path]::GetTempPath()) 'privos-sync.tar'
$script = Join-Path ([IO.Path]::GetTempPath()) 'privos-sync.sh'
$remoteArchive = '/tmp/privos-sync.tar'
$remoteScript = '/tmp/privos-sync.sh'

# Windows-Dateien kennen kein Ausführbar-Bit; die Rechte kommen aus dem Git-Index.
$executables = & git -C $repo ls-files -s -- system_files |
    Where-Object { $_ -match '^100755 ' } |
    ForEach-Object { '/' + ($_ -split "`t", 2)[1].Substring('system_files/'.Length) }
if ($LASTEXITCODE -ne 0) { throw 'git ls-files ist fehlgeschlagen.' }

& tar.exe -cf $archive -C (Join-Path $repo 'system_files') etc usr
if ($LASTEXITCODE -ne 0) { throw 'Das Archiv konnte nicht erstellt werden.' }

$chmod = if ($executables) { 'chmod 755 ' + (($executables | ForEach-Object { "'$_'" }) -join ' ') } else { 'true' }
$remote = @"
set -e
if ! touch /usr/.privos-sync 2>/dev/null; then bootc usr-overlay; fi
rm -f /usr/.privos-sync
umask 022
tar -xf $remoteArchive -C / --no-same-owner --no-same-permissions --no-overwrite-dir
$chmod
rm -f $remoteArchive $remoteScript
glib-compile-schemas /usr/share/glib-2.0/schemas
dconf update
systemctl daemon-reload
"@
[IO.File]::WriteAllText($script, ($remote -replace "`r", '') + "`n")

Write-Host "Übertrage system_files nach $target ..."
& scp.exe -q $archive $script "${target}:/tmp/"
if ($LASTEXITCODE -ne 0) { throw 'Die Übertragung per scp ist fehlgeschlagen.' }
Remove-Item -LiteralPath $archive, $script

& ssh.exe -t $target "sudo sh $remoteScript"
if ($LASTEXITCODE -ne 0) { throw "Das Einspielen in der VM ist fehlgeschlagen (Fehlercode $LASTEXITCODE)." }

Write-Host 'Fertig. GNOME-Einstellungen und Shell-Erweiterungen greifen nach Ab- und Anmelden.'
Write-Host 'Die Änderungen gelten bis zum nächsten Neustart der VM.'
