param([string]$InputJson, [string]$OutputWav)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
try {
    Add-Type -AssemblyName System.Speech
    $data = Get-Content -LiteralPath $InputJson -Raw -Encoding UTF8 | ConvertFrom-Json
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
    try {
        $voices = @($synth.GetInstalledVoices() | Where-Object { $_.Enabled -and $_.VoiceInfo.Culture.Name -eq $data.locale })
        if ($voices.Count -eq 0) { throw "No installed System.Speech voice for $($data.locale). Install a Windows TTS language voice." }
        $preferred = @($voices | Where-Object { $_.VoiceInfo.Gender.ToString() -eq $data.gender })
        if ($preferred.Count -gt 0) { $synth.SelectVoice($preferred[0].VoiceInfo.Name) }
        else { $synth.SelectVoice($voices[0].VoiceInfo.Name) }
        $synth.Rate = [int]$data.rate
        $synth.SetOutputToWaveFile($OutputWav)
        $synth.Speak([string]$data.text)
    } finally { if ($synth) { $synth.Dispose() } }
} catch { [Console]::Error.WriteLine($_.Exception.Message); exit 1 }
