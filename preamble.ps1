Write-Host "> Initialization"

# Create files
$filesToCreate = @(
    ".\orders\utility\admins",
    ".\orders\utility\mali",
    ".\orders\utility\secrets",
    ".\orders\utility\superadmins",
    ".\orders\utility\usage.csv"
)

foreach ($file in $filesToCreate) {
    $path = Join-Path $PSScriptRoot $file
    $null | Out-File -FilePath $path -Force
}

Write-Host "> Files created"

# Introduce a delay to allow the file system to register the newly created files
Start-Sleep -Seconds 1

# Populate files
@("meets a dragon and wins", "meets a dragon and loses") | Out-File -FilePath ".\orders\utility\mali" -Append
Write-Host "> Mali populated"

@("CMD;USER;TIME;OUT;FULL_CMD;ERR") | Out-File -FilePath ".\orders\utility\usage.csv"
Write-Host "> Usage initialized"

# Download yolov4-tiny files
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/coco.names' -OutFile '.\orders\utility\coco.names'
Invoke-WebRequest -Uri 'https://github.com/AlexeyAB/darknet/releases/download/darknet_yolo_v4_pre/yolov4-tiny.weights' -OutFile '.\orders\utility\yolov4-tiny.weights'
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov4-tiny.cfg' -OutFile '.\orders\utility\yolov4-tiny.cfg'
Write-Host "> Downloaded yolov4-tiny files"

# Install Chocolatey
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
# Install required softwares
choco install exiftool -y
choco install ffmpeg -y
choco install ghostscript -y
choco install imagemagick -y
choco install jpegoptim -y
choco install optipng -y
choco install qalculate -y

Write-Host "> Finished, close this shell and open a new one"
