Add-Type -AssemblyName System.Drawing

$OutDir = Join-Path $PSScriptRoot "visuals"
New-Item -ItemType Directory -Force $OutDir | Out-Null

$W = 1600
$H = 900
$BG = [System.Drawing.ColorTranslator]::FromHtml("#f7f2ea")
$INK = [System.Drawing.ColorTranslator]::FromHtml("#1b1b1f")
$MUTED = [System.Drawing.ColorTranslator]::FromHtml("#66615c")
$GRID = [System.Drawing.ColorTranslator]::FromHtml("#dfd5c8")
$TRACK = [System.Drawing.ColorTranslator]::FromHtml("#ebe2d6")
$BLUE = [System.Drawing.ColorTranslator]::FromHtml("#276ef1")
$RED = [System.Drawing.ColorTranslator]::FromHtml("#d84a3a")
$GREEN = [System.Drawing.ColorTranslator]::FromHtml("#16805d")
$GOLD = [System.Drawing.ColorTranslator]::FromHtml("#c17c18")
$PURPLE = [System.Drawing.ColorTranslator]::FromHtml("#7b4bc4")
$PANEL = [System.Drawing.ColorTranslator]::FromHtml("#fff9f0")

function New-Font($Size, [switch]$Bold) {
    $style = if ($Bold) { [System.Drawing.FontStyle]::Bold } else { [System.Drawing.FontStyle]::Regular }
    return [System.Drawing.Font]::new("Arial", $Size, $style, [System.Drawing.GraphicsUnit]::Pixel)
}

$FTitle = New-Font 62 -Bold
$FSub = New-Font 32
$FLabel = New-Font 34 -Bold
$FSmall = New-Font 27
$FTiny = New-Font 22

function New-Chart($Title, $Subtitle) {
    $bmp = [System.Drawing.Bitmap]::new($W, $H)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.Clear($BG)
    $g.DrawString($Title, $FTitle, [System.Drawing.SolidBrush]::new($INK), 80, 58)
    $g.DrawString($Subtitle, $FSub, [System.Drawing.SolidBrush]::new($MUTED), 84, 138)
    return @($bmp, $g)
}

function Add-Footer($g) {
    $g.DrawString(
        "Source: 1,000 LLM story openings, five models, July 2026",
        $FTiny,
        [System.Drawing.SolidBrush]::new($MUTED),
        80,
        840
    )
}

function Add-RoundedRect($g, $x, $y, $w, $h, $r, $color) {
    $path = [System.Drawing.Drawing2D.GraphicsPath]::new()
    $d = $r * 2
    $path.AddArc($x, $y, $d, $d, 180, 90)
    $path.AddArc($x + $w - $d, $y, $d, $d, 270, 90)
    $path.AddArc($x + $w - $d, $y + $h - $d, $d, $d, 0, 90)
    $path.AddArc($x, $y + $h - $d, $d, $d, 90, 90)
    $path.CloseFigure()
    $g.FillPath([System.Drawing.SolidBrush]::new($color), $path)
    $path.Dispose()
}

function Save-Chart($bmp, $g, $Name) {
    Add-Footer $g
    $path = Join-Path $OutDir $Name
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose()
    $bmp.Dispose()
}

function New-BarChart($Name, $Title, $Subtitle, $Rows, $MaxValue) {
    $parts = New-Chart $Title $Subtitle
    $bmp = $parts[0]
    $g = $parts[1]
    $left = 430
    $top = 245
    $barH = 72
    $gap = 34
    $maxW = 850
    for ($i = 0; $i -lt $Rows.Count; $i++) {
        $row = $Rows[$i]
        $label = $row[0]
        $value = [int]$row[1]
        $color = $row[2]
        $y = $top + $i * ($barH + $gap)
        $g.DrawString($label, $FLabel, [System.Drawing.SolidBrush]::new($INK), 80, $y + 14)
        Add-RoundedRect $g $left $y $maxW $barH 14 $TRACK
        $bw = [int]($maxW * $value / $MaxValue)
        Add-RoundedRect $g $left $y $bw $barH 14 $color
        $g.DrawString("$value%", $FLabel, [System.Drawing.SolidBrush]::new($INK), $left + $bw + 28, $y + 13)
    }
    Save-Chart $bmp $g $Name
}

New-BarChart "elara_by_model.png" `
    "Elara is Gemini's favorite name" `
    "Share of each model's 200 story openings containing Elara" `
    @(
        @("Gemini 2.5 Flash", 46, $BLUE),
        @("DeepSeek v3.1", 19, $PURPLE),
        @("GPT-5-mini", 6, $GREEN),
        @("Llama 4 Maverick", 4, $GOLD),
        @("Claude Sonnet 4.5", 2, $RED)
    ) `
    50

New-BarChart "top_female_name_share.png" `
    "The female-name pool collapses" `
    "Each model's top female name as a share of female first-name mentions" `
    @(
        @("Gemini: Elara", 46, $BLUE),
        @("Llama: Emily", 28, $GOLD),
        @("DeepSeek: Elara", 23, $PURPLE),
        @("GPT-5-mini: Emily", 23, $GREEN),
        @("Claude: Sarah", 13, $RED)
    ) `
    50

$parts = New-Chart "The role default is gendered" "Pooled across 1,000 story openings"
$bmp = $parts[0]
$g = $parts[1]

$blocks = @(
    @("Protagonists", 76, "female", $BLUE, 160, 260),
    @("Secondary characters", 35, "female", $RED, 880, 260)
)

foreach ($block in $blocks) {
    $title = $block[0]
    $value = [int]$block[1]
    $suffix = $block[2]
    $color = $block[3]
    $x = [int]$block[4]
    $y = [int]$block[5]
    $g.DrawString($title, $FLabel, [System.Drawing.SolidBrush]::new($INK), $x, $y)
    Add-RoundedRect $g $x ($y + 78) 560 132 22 $TRACK
    Add-RoundedRect $g $x ($y + 78) ([int](560 * $value / 100)) 132 22 $color
    $g.DrawString("$value% $suffix", $FTitle, [System.Drawing.SolidBrush]::new([System.Drawing.Color]::White), $x + 24, $y + 110)
}

Add-RoundedRect $g 270 600 1060 140 24 $PANEL
$g.DrawRectangle([System.Drawing.Pen]::new($GRID, 3), 270, 600, 1060, 140)
$g.DrawString("Most common pairing:", $FSmall, [System.Drawing.SolidBrush]::new($MUTED), 330, 626)
$g.DrawString("female lead + male secondary = 57%", $FLabel, [System.Drawing.SolidBrush]::new($INK), 330, 670)

Save-Chart $bmp $g "role_gender_skew.png"
