# Captura fiel de la ventana "TaskBar" con PrintWindow (aunque esté tapada por otras ventanas)
# y mide el render real. Uso: powershell -File capture_print.ps1 <salida.png> [process-id]
param(
    [string]$OutPng = "C:\Users\fjmn2\Dev\taskbar-app\print_capture.png",
    [int]$ProcessId = 0
)

Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public struct RECT5 { public int Left; public int Top; public int Right; public int Bottom; }
public class Win32e {
    public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr lParam);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder sb, int max);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT5 rect);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdc, uint flags);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
}
"@

$found = [IntPtr]::Zero
$fallback = [IntPtr]::Zero
$cb = [Win32e+EnumProc]{
    param($h, $l)
    if ([Win32e]::IsWindowVisible($h)) {
        $sb = New-Object System.Text.StringBuilder 256
        [Win32e]::GetWindowText($h, $sb, 256) | Out-Null
        $windowPid = 0
        [Win32e]::GetWindowThreadProcessId($h, [ref]$windowPid) | Out-Null
        $pidMatches = ($ProcessId -gt 0 -and $windowPid -eq $ProcessId)
        $titleMatches = ($sb.ToString() -eq "TaskBar")
        if ($pidMatches) { $script:found = $h; return $false }
        if ($titleMatches -and $script:fallback -eq [IntPtr]::Zero) { $script:fallback = $h }
    }
    return $true
}
[Win32e]::EnumWindows($cb, [IntPtr]::Zero) | Out-Null
if ($script:found -eq [IntPtr]::Zero -and $script:fallback -ne [IntPtr]::Zero) { $script:found = $script:fallback }
if ($script:found -eq [IntPtr]::Zero) { Write-Output "NO_WINDOW"; exit 1 }
$h = $script:found
[Win32e]::ShowWindow($h, 9) | Out-Null  # SW_RESTORE
[Win32e]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 250

$r = New-Object RECT5
[Win32e]::GetWindowRect($h, [ref]$r) | Out-Null
$w = $r.Right - $r.Left; $ht = $r.Bottom - $r.Top
Write-Output ("WindowRect: {0},{1} {2}x{3}" -f $r.Left, $r.Top, $w, $ht)

$bmp = New-Object System.Drawing.Bitmap($w, $ht)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$hdc = $g.GetHdc()
$ok = [Win32e]::PrintWindow($h, $hdc, 2)   # PW_RENDERFULLCONTENT
$g.ReleaseHdc($hdc)
$g.Dispose()
Write-Output ("PrintWindow ok: {0}" -f $ok)
$bmp.Save($OutPng)
Write-Output ("Saved: {0}" -f $OutPng)

$pts = @(
    @("titulo(50%,3%)",   [int]($w*0.50), [int]($ht*0.03)),
    @("header(10%,7%)",   [int]($w*0.10), [int]($ht*0.07)),
    @("progreso(50%,14%)",[int]($w*0.50), [int]($ht*0.14)),
    @("entrada(40%,23%)", [int]($w*0.40), [int]($ht*0.23)),
    @("boton-add(88%,23%)",[int]($w*0.88), [int]($ht*0.23)),
    @("fila1(15%,40%)",   [int]($w*0.15), [int]($ht*0.40)),
    @("fila2(15%,46%)",   [int]($w*0.15), [int]($ht*0.46)),
    @("fila3(15%,52%)",   [int]($w*0.15), [int]($ht*0.52)),
    @("lista-vacia(50%,70%)", [int]($w*0.50), [int]($ht*0.70)),
    @("boton-ghost(8%,93%)",[int]($w*0.08), [int]($ht*0.93))
)
foreach ($pt in $pts) {
    $x = $pt[1]; $y = $pt[2]
    if ($x -lt $w -and $y -lt $ht) {
        $c = $bmp.GetPixel($x, $y)
        Write-Output ("{0} -> RGB({1},{2},{3})" -f $pt[0], $c.R, $c.G, $c.B)
    }
}

# Conteo de píxeles claros (texto) en la banda de filas: debe ser >0 si hay texto.
# En esta UI las primeras filas empiezan cerca del 27% de la ventana.
$light = 0; $sample = 0
for ($y = [int]($ht*0.25); $y -lt [int]($ht*0.60); $y += 2) {
    for ($x = [int]($w*0.06); $x -lt [int]($w*0.90); $x += 2) {
        $px = $bmp.GetPixel($x, $y); $sample++
        if (($px.R + $px.G + $px.B) -gt 420) { $light++ }
    }
}
Write-Output ("Banda de filas: {0} px claros / {1} muestreados ({2:P1})" -f $light, $sample, ($light/$sample))
$bmp.Dispose()
