# Executa a logica de Gamificacao do AstroHealth OS (Bioma Cooperativo + Elo Terra-Espaco)
# Utiliza chamadas locais ao Ollama (llama3.2:3b) em http://127.0.0.1:11434
$OLLAMA_URL = "http://127.0.0.1:11434"
$MODELO = "llama3.2:3b"
$saidaJson = Join-Path $PSScriptRoot "resultado_gamificacao.json"

function Chamar-Ollama([string]$prompt) {
    $body = @{
        model   = $MODELO
        prompt  = $prompt
        stream  = $false
        options = @{ temperature = 0.3; num_predict = 100 }
    } | ConvertTo-Json -Depth 4
    try {
        $resp = Invoke-RestMethod -Uri "$OLLAMA_URL/api/generate" -Method Post -ContentType "application/json; charset=utf-8" `
            -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 120
        return $resp.response.Trim()
    } catch {
        return "Conexao com o Ollama local indisponivel no momento."
    }
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " AstroHealth OS · Gamificacao (Bioma Cooperativo & Elo) " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. BIOMA COOPERATIVO (3 Astronautas na estufa da nave)
Write-Host "`n1. Calculando Bioma Cooperativo da tripulacao..." -ForegroundColor Yellow
$tripulacao = @(
    @{ nome = "Alex";   agua_ml = 2400; meta_agua_ml = 2400; exercicio_min = 60; meta_exercicio_min = 60; sono_h = 7.5; meta_sono_h = 7.0 }
    @{ nome = "Sarah";  agua_ml = 2000; meta_agua_ml = 2400; exercicio_min = 50; meta_exercicio_min = 60; sono_h = 6.2; meta_sono_h = 7.0 }
    @{ nome = "Kenji";  agua_ml = 2200; meta_agua_ml = 2400; exercicio_min = 65; meta_exercicio_min = 60; sono_h = 6.8; meta_sono_h = 7.0 }
)

$taxasAgua = @(); $taxasEx = @(); $taxasSono = @()
foreach ($t in $tripulacao) {
    $taxasAgua += [Math]::Min(1.0, ($t.agua_ml / $t.meta_agua_ml))
    $taxasEx   += [Math]::Min(1.0, ($t.exercicio_min / $t.meta_exercicio_min))
    $taxasSono += [Math]::Min(1.0, ($t.sono_h / $t.meta_sono_h))
}

$medAgua = [Math]::Round((($taxasAgua | Measure-Object -Average).Average * 100), 1)
$medEx   = [Math]::Round((($taxasEx | Measure-Object -Average).Average * 100), 1)
$medSono = [Math]::Round((($taxasSono | Measure-Object -Average).Average * 100), 1)
$vitalidade = [Math]::Round(($medAgua * 0.35 + $medEx * 0.35 + $medSono * 0.30), 1)

$fase = if ($vitalidade -ge 85) { "Florescendo (Ecossistema Vibrante)" }
        elseif ($vitalidade -ge 65) { "Crescendo (Estavel)" }
        else { "Brotando (Requer Atencao)" }

Write-Host " Vitalidade Coletiva: $vitalidade%" -ForegroundColor Green
Write-Host " Fase da Estufa:      $fase" -ForegroundColor Green
Write-Host " Adesao Media:       Agua: $medAgua% | Exercicio: $medEx% | Sono: $medSono%"

Write-Host " Consultando Cosmo no Ollama local para narrativa da estufa..." -ForegroundColor Gray
$promptBioma = "Voce e a Cosmo, IA de saude de astronautas. O Bioma Cooperativo da estufa da nave alcancou $vitalidade% de vitalidade (Fase: $fase). " +
               "Gere uma mensagem curta em portugues (2 frases), incentivando a tripulacao de forma acolhedora para o visor do relogio."
$narrativaBioma = Chamar-Ollama $promptBioma
Write-Host " Cosmo: `"$narrativaBioma`"" -ForegroundColor White

# 2. ELO TERRA-ESPACO (Astronauta Alex + Familiar Lucas na Terra)
Write-Host "`n2. Calculando Elo Terra-Espaco (Corrida Terra-Orbita)..." -ForegroundColor Yellow
$astronauta = @{ nome = "Alex"; km_esteira = 24.5 }
$familiar   = @{ nome = "Lucas (filho)"; km_corrida = 19.1 }
$consentimento = @{ compartilhar_atividades = $true; permitir_mensagens = $true }

$metaKm = 60.0
$totalKm = [Math]::Round(($astronauta.km_esteira + $familiar.km_corrida), 1)
$progresso = [Math]::Round((($totalKm / $metaKm) * 100), 1)

Write-Host " Desafio:            Corrida Terra-Orbita" -ForegroundColor Green
Write-Host " Alex (Orbita):      $($astronauta.km_esteira) km" -ForegroundColor Green
Write-Host " Lucas (Terra):       $($familiar.km_corrida) km" -ForegroundColor Green
Write-Host " Progresso Conjunto: $totalKm / $metaKm km ($progresso%)" -ForegroundColor Green
Write-Host " Privacidade ADR-007: Respeitada (Sinais vitais brutos e saude mental nao sao expostos)." -ForegroundColor DarkGray

Write-Host " Consultando Cosmo no Ollama local para mensagem de conexao..." -ForegroundColor Gray
$promptElo = "Voce e a Cosmo no relogio do astronauta Alex. Ele e seu filho Lucas na Terra estao na Corrida Terra-Orbita e somaram $totalKm de $metaKm km ($progresso% da meta). " +
             "Crie uma mensagem curta e afetuosa em portugues (2 frases) celebrando essa conexao para o visor do relogio."
$mensagemElo = Chamar-Ollama $promptElo
Write-Host " Cosmo: `"$mensagemElo`"" -ForegroundColor White

# 3. SALVAR RESULTADO
$resultado = [pscustomobject]@{
    timestamp           = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    bioma_cooperativo   = [pscustomobject]@{
        vitalidade_pct   = $vitalidade
        fase_estufa      = $fase
        adesao_medias    = @{ agua = $medAgua; exercicio = $medEx; sono = $medSono }
        narrativa_cosmo  = $narrativaBioma
    }
    elo_terra_espaco    = [pscustomobject]@{
        desafio          = "Corrida Terra-Orbita"
        astronauta       = $astronauta.nome
        familiar         = $familiar.nome
        km_total         = $totalKm
        km_meta          = $metaKm
        progresso_pct    = $progresso
        mensagem_cosmo   = $mensagemElo
        privacidade      = "ADR-007 cumprida: dados de saude mental restritos"
    }
}

$resultado | ConvertTo-Json -Depth 4 | Out-File -FilePath $saidaJson -Encoding utf8
Write-Host "`nResultado salvo com sucesso em $saidaJson" -ForegroundColor Green

