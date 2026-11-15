# Trilha B (RAG) - construcao do indice, 100% local com o Ollama (nomic-embed-text).
# Substitui o ChromaDB (que exige Python) por um indice JSON em 8-ia\indice_rag.json, lido pelo ia.py.
#  1. le os .md/.txt de 8-ia-base-conhecimento (sem README, sem _duplicados, sem os 'irrelevante' do manifesto)
#  2. divide por TITULOS (#), juntando secoes pequenas; cada trecho tem ~1200 a 2800 caracteres (~300 a 700 tokens)
#  3. metadados: fonte, secao (os .md nao tem marcador de pagina, entao pagina = null) e temas
#  4. gera embeddings no Ollama (lotes de 8) e grava o JSON
$raiz = Resolve-Path (Join-Path $PSScriptRoot "..")
$base = Join-Path $raiz "8-ia-base-conhecimento"
$saida = Join-Path $raiz "8-ia\indice_rag.json"
$manifesto = Join-Path $PSScriptRoot "manifesto_documentos.csv"
$MIN = 1200; $MAX = 2800; $MODELO = "nomic-embed-text"

$fora = @{}
Import-Csv $manifesto -Encoding UTF8 | Where-Object { $_.tema -eq "irrelevante" } | ForEach-Object { $fora[$_.arquivo] = $true }

# temas por palavras-chave (modelo de 3B erra muito na classificacao; regra deterministica e auditavel)
$kw = [ordered]@{
  hidratacao  = 'hydrat|dehydrat|fluid (intake|loss|shift|balance|volume)|water intake|drinking water|thirst|urine output|hidrata'
  saude_mental = 'mental health|behavio(u)?ral (health|health)|psycholog|depress|anxiety|mood|cognitive (perform|function|decline)|isolation|confinement|sleep|circadian|fatigue|sa[uú]de mental|comportament'
  exercicio   = 'exercise|treadmill|resistive|\bARED\b|ergometer|aerobic|muscle (atrophy|loss|strength)|bone (loss|density)|exerc[ií]cio'
}
function Get-Temas([string]$t) {
  $r = @()
  foreach ($k in $kw.Keys) {
    $n = ([regex]::Matches($t, $kw[$k], 'IgnoreCase')).Count
    $limite = 1  # 1 ocorrencia ja marca o tema (com 2, trechos relevantes ficavam de fora do filtro)
    if ($n -ge $limite) { $r += $k }
  }
  if ($r.Count -eq 0) { $r = @('geral') }
  return , $r
}

$itens = New-Object System.Collections.Generic.List[object]
$usados = 0
foreach ($arq in Get-ChildItem $base -File | Where-Object { $_.Extension -in '.md', '.txt' -and $_.Name -ne 'README.md' } | Sort-Object Name) {
  if ($fora.ContainsKey($arq.Name)) { continue }
  $usados++
  $texto = Get-Content $arq.FullName -Encoding UTF8 -Raw
  # secoes por titulo
  $secoes = @(); $tit = "(inicio)"; $buf = New-Object System.Text.StringBuilder
  foreach ($ln in ($texto -split "\r?\n")) {
    if ($ln -match '^#{1,4}\s+(.+)$') {
      if ($buf.Length -gt 0) { $secoes += , @($tit, $buf.ToString()) }
      $tit = $Matches[1].Trim(); $buf = New-Object System.Text.StringBuilder
    } else { [void]$buf.AppendLine($ln) }
  }
  if ($buf.Length -gt 0) { $secoes += , @($tit, $buf.ToString()) }

  $atual = ""; $titAtual = ""
  $flush = {
    param($t, $s)
    $t = $t.Trim()
    if ($t.Length -ge 200) { $script:itens.Add([pscustomobject]@{ fonte = $arq.Name; secao = $s; pagina = $null; texto = $t; temas = (Get-Temas $t) }) }
  }
  foreach ($s in $secoes) {
    # fecha o trecho atual antes de um novo titulo se ja tem tamanho minimo
    if ($atual.Length -ge $MIN) { & $flush $atual $titAtual; $atual = ""; $titAtual = "" }
    if (-not $titAtual) { $titAtual = $s[0] }
    foreach ($p in ($s[1] -split "\r?\n\s*\r?\n")) {
      $p = $p.Trim(); if (-not $p) { continue }
      while ($p.Length -gt $MAX) {  # paragrafo gigante
        if ($atual) { & $flush $atual $titAtual; $atual = "" }
        & $flush $p.Substring(0, $MAX) $titAtual; $p = $p.Substring($MAX)
      }
      if (($atual.Length + $p.Length + 2) -gt $MAX -and $atual) { & $flush $atual $titAtual; $atual = ""; $titAtual = $s[0] }
      $atual = ($atual + "`n`n" + $p).Trim()
    }
  }
  if ($atual) { & $flush $atual $titAtual }
}
Write-Host "Documentos: $usados  Trechos: $($itens.Count)"

# embeddings em lotes de 8
$sw = [Diagnostics.Stopwatch]::StartNew()
for ($i = 0; $i -lt $itens.Count; $i += 8) {
  $lote = $itens[$i..([Math]::Min($i + 7, $itens.Count - 1))]
  $entrada = @($lote | ForEach-Object { "search_document: " + $_.secao + "`n" + $_.texto })
  $body = @{ model = $MODELO; input = $entrada } | ConvertTo-Json -Depth 3
  $r = Invoke-RestMethod -Uri http://127.0.0.1:11434/api/embed -Method Post -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 900
  for ($j = 0; $j -lt $lote.Count; $j++) {
    $v = @($r.embeddings[$j] | ForEach-Object { [math]::Round($_, 5) })
    $lote[$j] | Add-Member -NotePropertyName v -NotePropertyValue $v -Force
  }
  Write-Host ("{0}/{1}  ({2:n0}s)" -f [Math]::Min($i + 8, $itens.Count), $itens.Count, $sw.Elapsed.TotalSeconds)
}
$obj = [pscustomobject]@{ modelo = $MODELO; itens = @($itens | ForEach-Object { [pscustomobject]@{ fonte = $_.fonte; secao = $_.secao; pagina = $_.pagina; temas = $_.temas; texto = $_.texto; v = $_.v } }) }
$json = $obj | ConvertTo-Json -Depth 5 -Compress
[IO.File]::WriteAllText($saida, $json, (New-Object Text.UTF8Encoding($false)))
"Indice salvo em $saida"
"--- trechos por tema (um trecho pode ter mais de um)"
foreach ($t in 'hidratacao', 'saude_mental', 'exercicio', 'geral') { "{0,-13} {1}" -f $t, @($itens | Where-Object { $_.temas -contains $t }).Count }
