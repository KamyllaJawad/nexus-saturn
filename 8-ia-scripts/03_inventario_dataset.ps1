# Passo 1 (captura + limpeza) para 9-Dataset-Nasa.
# NAO move, NAO apaga e NAO altera nenhum arquivo: so le e grava inventario_dataset.csv.
#  - captura: lista todos os arquivos (pasta de origem, extensao, tamanho)
#  - limpeza: SHA256 para achar copias identicas entre as pastas; 1 arquivo vira o "canonico"
$base = Join-Path $PSScriptRoot "..\9-Dataset-Nasa" | Resolve-Path
$saida = Join-Path $PSScriptRoot "inventario_dataset.csv"

$arquivos = Get-ChildItem $base -Recurse -File
$linhas = foreach ($f in $arquivos) {
    $rel = $f.FullName.Substring($base.Path.Length + 1)
    [pscustomobject]@{
        dataset   = $rel.Split('\')[0]
        caminho   = $rel
        nome      = $f.Name
        extensao  = $f.Extension.ToLower()
        tamanho_kb = [math]::Round($f.Length / 1KB, 1)
        sha256    = (Get-FileHash $f.FullName -Algorithm SHA256).Hash
    }
}
# canonico = primeiro caminho (ordem alfabetica) de cada hash
$vistos = @{}
$linhas = $linhas | Sort-Object caminho | ForEach-Object {
    if ($vistos.ContainsKey($_.sha256)) { $_ | Add-Member duplicado_de $vistos[$_.sha256] -PassThru }
    else { $vistos[$_.sha256] = $_.caminho; $_ | Add-Member duplicado_de "" -PassThru }
}
$linhas | Export-Csv $saida -NoTypeInformation -Encoding UTF8

$unicos = $linhas | Where-Object { -not $_.duplicado_de }
"Arquivos: $($linhas.Count)  | Unicos: $($unicos.Count)  | Copias: $($linhas.Count - $unicos.Count)"
"Tamanho total (MB): " + [math]::Round(($linhas | Measure-Object tamanho_kb -Sum).Sum / 1024, 1)
"Tamanho dos unicos (MB): " + [math]::Round(($unicos | Measure-Object tamanho_kb -Sum).Sum / 1024, 1)
"--- por extensao (todos / unicos)"
$linhas | Group-Object extensao | Sort-Object Count -Descending | ForEach-Object {
    $u = ($_.Group | Where-Object { -not $_.duplicado_de }).Count
    "{0,-10} {1,5} / {2,5}" -f $(if ($_.Name) { $_.Name } else { "(sem)" }), $_.Count, $u
}
"--- pastas de origem"
$linhas | Group-Object dataset | ForEach-Object {
    $u = ($_.Group | Where-Object { -not $_.duplicado_de }).Count
    "{0,-28} {1,4} arquivos, {2,4} unicos" -f $_.Name, $_.Count, $u
}
"Salvo em $saida"

