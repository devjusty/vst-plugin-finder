# Script to find all VST and VST3 plugins on a Windows machine
# Save this as Find-VSTPlugins.ps1

# Common VST installation paths to search
$searchPaths = @(
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
    "$env:ProgramFiles\Ableton\Live\Plugins\VST3"
)

# Add user-specific paths that might contain VST plugins
$userPaths = @(
    "$env:USERPROFILE\Documents\VST",
    "$env:USERPROFILE\Documents\VST3",
    "$env:USERPROFILE\Documents\Audio\Plugins\VST",
    "$env:USERPROFILE\Documents\Audio\Plugins\VST3",
    "$env:APPDATA\VST",
    "$env:APPDATA\VST3"
)

$searchPaths += $userPaths

# File extensions to search for
$vstExtensions = @("*.dll")
$vst3Extensions = @("*.vst3")

# Create an array to store results
$results = @()

# Function to check if a file is likely a VST plugin
function Test-VSTPlugin {
    param (
        [string]$FilePath
    )
    
    # Simple heuristic: Check file size (most VST plugins are at least 100KB)
    $fileInfo = Get-Item $FilePath
    return $fileInfo.Length -gt 102400
}

# Search for VST and VST3 plugins in all paths
foreach ($path in $searchPaths) {
    if (Test-Path $path) {
        # Find VST plugins
        $vstPlugins = Get-ChildItem -Path $path -Include $vstExtensions -Recurse -ErrorAction SilentlyContinue | 
                      Where-Object { Test-VSTPlugin $_.FullName }
        foreach ($plugin in $vstPlugins) {
            $results += [PSCustomObject]@{
                Type = "VST"
                Name = $plugin.Name
                Path = $plugin.DirectoryName
                Size = "{0:N2} MB" -f ($plugin.Length / 1MB)
            }
        }
        
        # Find VST3 plugins
        $vst3Plugins = Get-ChildItem -Path $path -Include $vst3Extensions -Recurse -ErrorAction SilentlyContinue
        foreach ($plugin in $vst3Plugins) {
            $results += [PSCustomObject]@{
                Type = "VST3"
                Name = $plugin.Name
                Path = $plugin.DirectoryName
                Size = "{0:N2} MB" -f ($plugin.Length / 1MB)
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
    $vstCount = ($results | Where-Object { $_.Type -eq "VST" }).Count
    $vst3Count = ($results | Where-Object { $_.Type -eq "VST3" }).Count
    
    Write-Output "Summary:"
    Write-Output "- VST Plugins: $vstCount"
    Write-Output "- VST3 Plugins: $vst3Count"
    Write-Output "- Total: $($results.Count)"
    Write-Output ""
    
    # Output formatted table
    $results | Sort-Object Type, Name | Format-Table -AutoSize
    
    # Export to CSV file in the current user's desktop
    $csvPath = "$env:USERPROFILE\Desktop\VST_Plugins_List.csv"
    $results | Export-Csv -Path $csvPath -NoTypeInformation
    Write-Output "Plugin list exported to: $csvPath"
}
