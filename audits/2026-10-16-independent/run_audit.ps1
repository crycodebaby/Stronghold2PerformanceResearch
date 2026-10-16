param(
  [string]$InputRoot = (Join-Path $PSScriptRoot '..\..\..'),
  [string]$Ghidra = (Join-Path $env:USERPROFILE 'Tools\ghidra_12.1.4_PUBLIC'),
  [string]$Work = (Join-Path $env:TEMP 'sh2-independent-audit-work'),
  [switch]$ExportBinary
)
$ErrorActionPreference = 'Stop'
$auditDir = $PSScriptRoot
$scratch = $Work   # published copy: work files stay outside the repository
New-Item -ItemType Directory -Force -Path $scratch | Out-Null
function Invoke-PythonAudit([string]$Name, [string[]]$Arguments) {
  & python -I (Join-Path $auditDir $Name) @Arguments
  if ($LASTEXITCODE -ne 0) { throw "$Name failed: $LASTEXITCODE" }
}
if (-not (Test-Path -LiteralPath (Join-Path $auditDir 'identity_before.json'))) {
  Invoke-PythonAudit 'audit_data.py' @('--root',$InputRoot,'--snapshot','before')
}
# Refuse to proceed after an unnoticed change to audited inputs.
Invoke-PythonAudit 'audit_data.py' @('--root',$InputRoot,'--snapshot','after')
Invoke-PythonAudit 'audit_data.py' @('--root',$InputRoot)
if ($ExportBinary) {
  $projectCopy = Join-Path $scratch 'ghidra-copy'
  if (-not (Test-Path -LiteralPath (Join-Path $projectCopy 'SH2.gpr'))) {
    New-Item -ItemType Directory -Force -Path $projectCopy | Out-Null
    Copy-Item -LiteralPath (Join-Path $InputRoot 'ghidra-projects\SH2.gpr') -Destination $projectCopy
    Copy-Item -LiteralPath (Join-Path $InputRoot 'ghidra-projects\SH2.rep') -Destination $projectCopy -Recurse
  }
  $jobs = @(
    @{Program='Stronghold2.exe'; Folder='exe'; Addresses=@('0078e4d0','0078c9e0','0076b210')},
    @{Program='granny2.dll'; Folder='granny'; Addresses=@('5004f4e0','5004f6d0','50052f90','50052bb0','5004f4c0','50052f80')},
    @{Program='granny2.dll'; Folder='granny-workers'; Addresses=@('50002640','5004f700','50033d40','50032300')}
  )
  foreach ($job in $jobs) {
    $destination = Join-Path $scratch ('binary\'+$job.Folder)
    $headlessArgs = @($projectCopy,'SH2','-process',$job.Program,'-noanalysis','-readOnly','-scriptPath',$auditDir,
                     '-postScript','AuditPath.java',$destination) + $job.Addresses
    & (Join-Path $Ghidra 'support\analyzeHeadless.bat') @headlessArgs *> (Join-Path $scratch ($job.Folder+'-headless.txt'))
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath (Join-Path $destination 'references.txt'))) { throw 'Ghidra export failed' }
  }
}
Invoke-PythonAudit 'verify_binary.py' @('--root',$InputRoot)
Invoke-PythonAudit 'observer_repro.py' @('--hub-source',(Join-Path $InputRoot 'Stronghold2AnalyseHub\Stronghold2AnalyseHub\core\granny_observer.cpp'))
Invoke-PythonAudit 'audit_data.py' @('--root',$InputRoot,'--snapshot','after')
Write-Output 'Audit checks passed. All generated files are in this audit workspace.'
