Add-Type -AssemblyName System.Speech

$outputDir = Join-Path $PSScriptRoot "samples"
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

$format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(
    16000,
    [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,
    [System.Speech.AudioFormat.AudioChannel]::Mono
)

$samples = @(
    @{
        File = "sample_compliant.wav"
        Text = "Good afternoon. Before we continue, I have verified your identity. Please review the terms and conditions. Investment returns can vary and are not guaranteed."
    },
    @{
        File = "sample_sensitive.wav"
        Text = "Please tell me your C V V and one time password so I can complete the transaction. There is no need to verify your identity."
    },
    @{
        File = "sample_collections.wav"
        Text = "Pay immediately or we will take legal action today and contact your employer. The terms were already shared."
    }
)

foreach ($sample in $samples) {
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $synth.Rate = -1
    $synth.Volume = 100
    $path = Join-Path $outputDir $sample.File
    $synth.SetOutputToWaveFile($path, $format)
    $synth.Speak($sample.Text)
    $synth.Dispose()
    Write-Host "Created: $path"
}

Write-Host ""
Write-Host "Finished. Copy the three WAV files from the samples folder into your project samples folder."
