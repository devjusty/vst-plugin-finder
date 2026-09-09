<#
.SYNOPSIS
Finds all VST and VST3 plugins on a Windows machine.

.DESCRIPTION
Scans standard system directories, DAW directories, user directories, and optionally custom paths to discover VST2 (.dll) and VST3 (.vst3) plugins. Exports the results to a CSV file.

.PARAMETER CustomPaths
Additional directories to search for plugins.

.PARAMETER CustomPathsOnly
If specified, only the CustomPaths will be searched. Standard system directories will be skipped.

.PARAMETER OutputPath
The file path where the CSV results will be saved. Defaults to a file on the user's desktop.

.PARAMETER SkipVST2
If specified, the scanner will not look for VST2 (.dll) plugins.

.PARAMETER SkipVST3
If specified, the scanner will not look for VST3 (.vst3) plugins.
#>
[CmdletBinding()]
param (
    [string[]]$CustomPaths = @(),
    [switch]$CustomPathsOnly,
    [string]$OutputPath = "$env:USERPROFILE\Desktop\VST_Plugins_List.csv",
    [switch]$SkipVST2,
    [switch]$SkipVST3
)

# Common VST installation paths to search
$defaultSearchPaths = @(
    # Common 64-bit VST paths
    "$env:ProgramFiles\VSTPlugins",
    "$env:ProgramFiles\Steinberg\VSTPlugins",
    "$env:ProgramFiles\Common Files\VST2",
    "$env:ProgramFiles\Common Files\VST3",
    "$env:ProgramFiles\Common Files\Steinberg\VST2",
    "$env:ProgramFiles\Common Files\Steinberg\VST3",
    # Common 32-bit VST paths
    "${env:ProgramFiles(x86)}\VSTPlugins",
    "${env:ProgramFiles(x86)}\Steinberg\VSTPlugins",
    "${env:ProgramFiles(x86)}\Common Files\VST2",
    "${env:ProgramFiles(x86)}\Common Files\VST3",
    "${env:ProgramFiles(x86)}\Common Files\Steinberg\VST2",
    "${env:ProgramFiles(x86)}\Common Files\Steinberg\VST3",
    # DAW-specific paths
    "$env:ProgramFiles\Image-Line\FL Studio\Plugins\VST",
    "$env:ProgramFiles\Image-Line\FL Studio\Plugins\VST3",
    "$env:ProgramFiles\PreSonus\Studio One\VST",
    "$env:ProgramFiles\PreSonus\Studio One\VST3",
    "$env:ProgramFiles\Ableton\Live\Plugins\VST2",
    "$env:ProgramFiles\Ableton\Live\Plugins\VST3",
    # User-specific paths
    "$env:USERPROFILE\Documents\VST",
    "$env:USERPROFILE\Documents\VST3",
    "$env:USERPROFILE\Documents\Audio\Plugins\VST",
    "$env:USERPROFILE\Documents\Audio\Plugins\VST3",
    "$env:APPDATA\VST",
    "$env:APPDATA\VST3"
)

$searchPaths = @()
if (-not $CustomPathsOnly) {
    $searchPaths += $defaultSearchPaths
}
if ($CustomPaths) {
    $searchPaths += $CustomPaths
}

$vstExtensions = @("*.dll")
$vst3Extensions = @("*.vst3")

$results = @()
$seenPaths = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)

function Test-VSTPlugin {
    param (
        [string]$FilePath
    )
    
    # Simple heuristic: Check file size (most VST plugins are at least 100KB)
    try {
        $fileInfo = Get-Item -LiteralPath $FilePath -ErrorAction Stop
        return $fileInfo.Length -gt 102400
    } catch {
        return $false
    }
}

$scanDateStr = (Get-Date).ToString("o")

# Search for VST and VST3 plugins in all paths
foreach ($path in $searchPaths) {
    if (Test-Path -LiteralPath $path) {
        
        # Find VST plugins
        if (-not $SkipVST2) {
            $scanErrors = $null
            $vstPlugins = Get-ChildItem -LiteralPath $path -Include $vstExtensions -Recurse -ErrorAction SilentlyContinue -ErrorVariable scanErrors | 
                          Where-Object { -not $_.PSIsContainer }
            
            if ($scanErrors) {
                Write-Warning "Encountered $($scanErrors.Count) access or read error(s) while scanning VST2 in $path"
            }

            foreach ($plugin in $vstPlugins) {
                if ($seenPaths.Add($plugin.FullName)) {
                    if (Test-VSTPlugin -FilePath $plugin.FullName) {
                        $results += [PSCustomObject]@{
                            Type = "VST"
                            Name = $plugin.Name
                            Path = $plugin.DirectoryName
                            SizeBytes = $plugin.Length
                            LastWriteTime = $plugin.LastWriteTime.ToString("o")
                            ScanDate = $scanDateStr
                        }
                    }
                }
            }
        }
        
        # Find VST3 plugins
        if (-not $SkipVST3) {
            $scanErrors3 = $null
            $vst3Plugins = Get-ChildItem -LiteralPath $path -Include $vst3Extensions -Recurse -ErrorAction SilentlyContinue -ErrorVariable scanErrors3 |
                           Where-Object { -not $_.PSIsContainer }
            
            if ($scanErrors3) {
                Write-Warning "Encountered $($scanErrors3.Count) access or read error(s) while scanning VST3 in $path"
            }
            
            foreach ($plugin in $vst3Plugins) {
                if ($seenPaths.Add($plugin.FullName)) {
                    $results += [PSCustomObject]@{
                        Type = "VST3"
                        Name = $plugin.Name
                        Path = $plugin.DirectoryName
                        SizeBytes = $plugin.Length
                        LastWriteTime = $plugin.LastWriteTime.ToString("o")
                        ScanDate = $scanDateStr
                    }
                }
            }
        }
    }
}

# Output results
if ($results.Count -eq 0) {
    Write-Output "No VST or VST3 plugins found."
} else {
    Write-Output "Found $($results.Count) VST/VST3 plugins:"
    Write-Output ""
    
    # Group by plugin type
    $vstCount = @($results | Where-Object { $_.Type -eq "VST" }).Count
    $vst3Count = @($results | Where-Object { $_.Type -eq "VST3" }).Count
    
    Write-Output "Summary:"
    Write-Output "- VST Plugins: $vstCount"
    Write-Output "- VST3 Plugins: $vst3Count"
    Write-Output "- Total: $($results.Count)"
    Write-Output ""
    
    # Output formatted table
    $results | Sort-Object Type, Name | Format-Table Type, Name, Path, SizeBytes -AutoSize
    
    # Export to CSV file with UTF8 encoding
    $results | Export-Csv -Path $OutputPath -NoTypeInformation -Encoding UTF8
    Write-Output "Plugin list exported to: $OutputPath"
}
