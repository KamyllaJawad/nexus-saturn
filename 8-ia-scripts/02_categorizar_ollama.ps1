# Passo 1 (categorizacao): usa o Ollama local (llama3.2:3b) para dar UM tema a cada documento.
# Nao move nem altera arquivos: so grava o manifesto 8-ia-scripts\manifesto_documentos.csv
$base = Join-Path $PSScriptRoot "..\8-ia-base-conhecimento" | Resolve-Path
$saida = Join-Path $PSScriptRoot "manifesto_documentos.csv"
$temas = "hidratacao","saude-mental","exercicio","radiacao","osseo-muscular","cardiovascular","nutricao-sono","vigilancia-saude-astronautas","geral-spaceflight","irrelevante"

$files = Get-ChildItem $base -File | Where-Object { $_.Extension -in ".md", ".txt" }
$resultado = foreach ($f in $files) {
    $trecho = (Get-Content $f.FullName -Encoding UTF8 -TotalCount 60) -join "`n"
    if ($trecho.Length -gt 2500) { $trecho = $trecho.Substring(0, 2500) }
    $prompt = "Classifique o documento em UM tema da lista: $($temas -join ', '). " +
              "Use 'irrelevante' se nao tratar de saude humana em voos espaciais (ex.: fisica de particulas, MRI de laboratorio, otimizacao de redes neurais). " +
              "Responda apenas JSON: {`"tema`":`"...`",`"motivo`":`"uma frase`"}.`n`nNome: $($f.Name)`nTexto:`n$trecho"
    $body = @{ model = "llama3.2:3b"; prompt = $prompt; stream = $false; format = "json"; options = @{ temperature = 0 } } | ConvertTo-Json -Depth 4
    try {
        $r = Invoke-RestMethod -Uri http://127.0.0.1:11434/api/generate -Method Post -ContentType "application/json; charset=utf-8" `
             -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 600
        $j = $r.response | ConvertFrom-Json
        $tema = if ($temas -contains $j.tema) { $j.tema } else { "revisar" }
        $motivo = $j.motivo
    } catch { $tema = "erro"; $motivo = $_.Exception.Message }
    Write-Output ([pscustomobject]@{ arquivo = $f.Name; tamanho_kb = [math]::Round($f.Length / 1KB, 1); tema = $tema; motivo = $motivo })
    Write-Host "$($f.Name) -> $tema"
}
$resultado | Export-Csv $saida -NoTypeInformation -Encoding UTF8
"Manifesto salvo em $saida"

