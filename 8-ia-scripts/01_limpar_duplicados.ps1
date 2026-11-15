# Passo 1 (limpeza): acha arquivos com conteudo identico (hash SHA256) e MOVE as copias
# para _duplicados. Nada e apagado; para desfazer, mova de volta.
$base = Join-Path $PSScriptRoot "..\8-ia-base-conhecimento" | Resolve-Path
$dup = Join-Path $base "_duplicados"
New-Item -ItemType Directory -Force $dup | Out-Null

$files = Get-ChildItem $base -File | Where-Object { $_.Extension -in ".md", ".txt" }
$files | Group-Object { (Get-FileHash $_.FullName -Algorithm SHA256).Hash } | Where-Object Count -gt 1 | ForEach-Object {
    # mantem o de nome "mais limpo": sem 'Copia' nem '(1)', e o mais curto
    $ordenado = $_.Group | Sort-Object { ($_.Name -match 'Copia|\(\d+\)') }, { $_.Name.Length }
    $manter = $ordenado[0]
    foreach ($d in $ordenado | Select-Object -Skip 1) {
        Move-Item $d.FullName (Join-Path $dup $d.Name) -Force
        "DUPLICADO: $($d.Name)  ->  mantido: $($manter.Name)"
    }
}
"Concluido. Arquivos unicos restantes: " + (Get-ChildItem $base -File | Where-Object { $_.Extension -in ".md", ".txt" }).Count

