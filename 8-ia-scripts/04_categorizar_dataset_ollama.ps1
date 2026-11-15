# Passo 1 (categorizacao) para 9-Dataset-Nasa, com o Ollama local (llama3.2:3b).
# Le o inventario_dataset.csv, resume cada pasta (nomes de arquivos unicos e extensoes) e pede ao
# modelo um tema, o tipo de sujeito e a utilidade. NAO altera nenhum arquivo.
# Saida: 8-ia-scripts\categorias_dataset.csv
$inv = Import-Csv (Join-Path $PSScriptRoot "inventario_dataset.csv")
$saida = Join-Path $PSScriptRoot "categorias_dataset.csv"
$temas = "osseo-muscular","cardiovascular","nutricao-hidratacao","sono-circadiano","neurovestibular","radiacao","imunologia-sangue","reproducao-desenvolvimento","ambiente-estacao","documentos-protocolo","outros"

$res = foreach ($g in ($inv | Group-Object dataset)) {
    $todos = $g.Group
    $unicos = $todos | Where-Object { -not $_.duplicado_de }
    # amostra de nomes: remove sufixos numericos para nao listar 1000 variacoes
    $nomes = $unicos | ForEach-Object { ($_.caminho -replace '^[^\\]+\\', '') -replace '_\d{2,}$', '_N' } | Select-Object -Unique | Select-Object -First 25
    $exts = ($todos | Group-Object extensao | ForEach-Object { "$(if ($_.Name) { $_.Name } else { 'sem-ext' }):$($_.Count)" }) -join ", "
    $prompt = "Voce cataloga datasets de pesquisa de voos espaciais da NASA (LSDA). Pelos nomes de arquivo abaixo, responda APENAS JSON " +
              "{`"tema`":`"...`",`"sujeito`":`"humano|animal|ambiente|desconhecido`",`"uso_para_astronautas`":`"alto|medio|baixo`",`"resumo`":`"uma frase em portugues`"}. " +
              "tema deve ser um de: $($temas -join ', '). Dica: 'rat', 'R1' com Surgery/Placenta/Plac costumam ser estudos com ratos; DXA e bone = osseo-muscular.`n`n" +
              "Pasta: $($g.Name)`nExtensoes: $exts`nArquivos (amostra):`n$($nomes -join "`n")"
    $body = @{ model = "llama3.2:3b"; prompt = $prompt; stream = $false; format = "json"; options = @{ temperature = 0 } } | ConvertTo-Json -Depth 4
    try {
        $r = Invoke-RestMethod -Uri http://127.0.0.1:11434/api/generate -Method Post -ContentType "application/json; charset=utf-8" `
             -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 600
        $j = $r.response | ConvertFrom-Json
        $tema = if ($temas -contains $j.tema) { $j.tema } else { "revisar" }
        $sujeito = $j.sujeito; $uso = $j.uso_para_astronautas; $resumo = $j.resumo
    } catch { $tema = "erro"; $sujeito = ""; $uso = ""; $resumo = $_.Exception.Message }
    Write-Host "$($g.Name) -> $tema / $sujeito / $uso"
    [pscustomobject]@{ dataset = $g.Name; arquivos = $todos.Count; unicos = $unicos.Count; extensoes = $exts; tema = $tema; sujeito = $sujeito; uso_para_astronautas = $uso; resumo = $resumo; amostra = ($nomes | Select-Object -First 4) -join " | " }
}
$res | Export-Csv $saida -NoTypeInformation -Encoding UTF8
"Salvo em $saida"

