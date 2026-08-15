# Escaneo de texto: cuenta píxeles claros (texto) en la zona de filas de un PNG.
param([string]$Png = "C:\Users\fjmn2\Dev\taskbar-app\verify.png")

Add-Type -AssemblyName System.Drawing
$bmp = [System.Drawing.Bitmap]::FromFile($Png)
$w = $bmp.Width; $h = $bmp.Height
$bright = 0; $done = 0
for ($y = [int]($h*0.22); $y -lt [int]($h*0.50); $y++) {
    for ($x = [int]($w*0.01); $x -lt [int]($w*0.95); $x++) {
        $c = $bmp.GetPixel($x, $y)
        $sum = $c.R + $c.G + $c.B
        if ($sum -gt 600) { $bright++ }
        elseif ($sum -gt 400) { $done++ }
    }
}
$total = $bright + $done
Write-Output ("{0}: px pendientes: {1} | px completado: {2} | total texto: {3}" -f $Png, $bright, $done, $total)
$bmp.Dispose()
