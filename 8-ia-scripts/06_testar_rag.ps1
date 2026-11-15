# Teste do RAG (a linha "testa o RAG" da planilha), 100% local.
# Para cada pergunta: (1) busca top-k no indice filtrando por tema; (2) confere se o trecho esperado veio
# (fonte + palavras-chave); (3) pede ao llama3.2:3b uma resposta citando [n]; (4) confere se citou so fontes
# recuperadas e, nas perguntas SEM resposta no corpus, se admitiu que nao sabe. Saida: 8-ia-scripts\resultados_rag.csv
param([int]$K = 6)
$raiz = Resolve-Path (Join-Path $PSScriptRoot "..")
$idx = Get-Content (Join-Path $raiz "8-ia\indice_rag.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$itens = $idx.itens
$MARCA = "Não encontrei essa informação nos documentos."
$FARMACO = '\b(mg|mcg|dosagem|comprimid\w*|medicament\w*|rem[eé]dio\w*|analg[eé]sic\w*|ibuprofeno|paracetamol|melatonina|zolpidem|antidepressiv\w*|sedativ\w*|medication\w*|drug\w*|pill\w*)\b'

function Ollama($caminho, $payload) {
  $b = $payload | ConvertTo-Json -Depth 5
  Invoke-RestMethod -Uri "http://127.0.0.1:11434$caminho" -Method Post -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($b)) -TimeoutSec 900
}
function Cos($a, $b) { $d = 0.0; $na = 0.0; $nb = 0.0; for ($i = 0; $i -lt $a.Count; $i++) { $d += $a[$i] * $b[$i]; $na += $a[$i] * $a[$i]; $nb += $b[$i] * $b[$i] }; $d / [math]::Sqrt($na * $nb) }
function Para-Ingles($texto) {
  # os documentos sao quase todos em ingles e o nomic-embed-text e fraco entre idiomas: traduz a CONSULTA (so a busca)
  $r = Ollama "/api/generate" @{ model = "llama3.2:3b"; prompt = "Translate to English. Output ONLY the translation, nothing else.`n`n$texto"; stream = $false; options = @{ temperature = 0; num_predict = 80 } }
  $r.response.Trim().Trim('"')
}
function Buscar($pergunta, $tema, $k) {
  $en = Para-Ingles $pergunta
  $q = (Ollama "/api/embed" @{ model = "nomic-embed-text"; input = @("search_query: $en") }).embeddings[0]
  $pool = if ($tema) { $itens | Where-Object { $_.temas -contains $tema } } else { $itens }
  $pool | ForEach-Object { [pscustomobject]@{ it = $_; s = (Cos $q $_.v) } } | Sort-Object s -Descending | Select-Object -First $k
}

# tema | pergunta | regex da fonte esperada | regex de palavras esperadas | tem resposta no corpus?
$casos = @(
 @('exercicio','Como o exercício ajuda astronautas em gravidade alterada?','causal_diagramming','muscle atrophy|bone loss',$true),
 @('exercicio','O exercício também ajuda a saúde comportamental dos astronautas?','causal_diagramming','behavioral health',$true),
 @('exercicio','Quais fatores modificáveis de estilo de vida aparecem, como hábitos de exercício e dieta?','causal_diagramming','Exercise Habits|Dietary',$true),
 @('exercicio','A perda óssea no espaço é afetada por radiação e gravidade parcial?','2509','bone',$true),
 @('exercicio','Quantos minutos de exercício por dia um astronauta deve fazer na ISS?','','',$false),
 @('exercicio','Qual a carga em kg que o equipamento ARED deve levantar por série?','','',$false),
 @('saude_mental','O que a avaliação LSAH inclui além do exame médico de rotina?','lifetime_surveillance','behavioral health',$true),
 @('saude_mental','Como é feita a avaliação LSAH remota, de casa?','lifetime_surveillance','virtual visit',$true),
 @('saude_mental','Como a perda de sono entra no modelo de risco da NASA?','levels_of_evidence','[Ss]leep',$true),
 @('saude_mental','Quais são os perigos do voo espacial segundo a NASA, como isolamento e confinamento?','levels_of_evidence|causal_diagramming','Isolation and Confinement',$true),
 @('saude_mental','Quais fatores contribuintes aparecem no risco de sono, como carga de trabalho e estresse?','levels_of_evidence','Workload|Stress|Schedule Shifting',$true),
 @('saude_mental','Que medicamento devo tomar para dormir melhor no espaço?','','',$false),
 @('saude_mental','Como a radiação cósmica galáctica pode afetar o sistema nervoso central?','galactic_cosmic_rays','central nervous|CNS',$true),
 @('hidratacao','Como eram reidratadas as refeições da missão Apollo 8?','lifetime_surveillance','rehydrat|freeze-dried',$true),
 @('hidratacao','Quanta água por dia um astronauta precisa beber em microgravidade?','','',$false),
 @('hidratacao','Quais são os sinais de desidratação em um astronauta?','','',$false),
 @('','Para que serve o programa LSAH?','lsah|lifetime_surveillance|vigil','surveillance|longitudinal',$true),
 @('','Quais riscos as partículas HZE trazem para missões a Marte?','hze','HZE',$true)
)

$res = @(); $n = 0
foreach ($c in $casos) {
  $n++; $tema, $perg, $fonteRx, $palRx, $tem = $c
  $top = @(Buscar $perg $tema $K)
  $recFonte = $false; $recPal = $false
  if ($tem) {
    $recFonte = [bool]($top | Where-Object { $_.it.fonte -match $fonteRx })
    $recPal = [bool]($top | Where-Object { $_.it.fonte -match $fonteRx -and $_.it.texto -match $palRx })
  }
  $ctx = ($top | ForEach-Object -Begin { $i = 0 } -Process { $i++; "[$i] (fonte: $($_.it.fonte)) $($_.it.texto.Substring(0, [Math]::Min(2400, $_.it.texto.Length)))" }) -join "`n`n"
  $prompt = "Responda em português, em no máximo 4 frases, usando SOMENTE os trechos abaixo. Termine TODA frase com a fonte no formato [n], por exemplo: 'O exercício previne a perda óssea [2].' Uma resposta sem [n] é inválida. " +
            "Só afirme o que estiver escrito nos trechos; se um fato não aparecer neles, não o afirme. " +
            "Se os trechos não trouxerem a resposta, responda exatamente: '$MARCA'. Não invente números nem listas. NUNCA cite medicamentos ou doses; para isso, diga que a decisão é do oficial médico.`n`nPERGUNTA: $perg`n`nTRECHOS:`n$ctx"
  $r = Ollama "/api/generate" @{ model = "llama3.2:3b"; prompt = $prompt; stream = $false; options = @{ temperature = 0; num_predict = 260 } }
  $resp = $r.response.Trim()
  $citados = @([regex]::Matches($resp, '\[(\d+)\]') | ForEach-Object { [int]$_.Groups[1].Value } | Select-Object -Unique)
  $citaOk = ($citados.Count -gt 0) -and -not ($citados | Where-Object { $_ -lt 1 -or $_ -gt $top.Count })
  $admite = $resp -match 'N[aã]o encontrei'
  $farm = $resp -match $FARMACO
  if ($tem) { $ok = $recPal -and $citaOk -and -not $admite -and -not $farm }
  else { $ok = ($admite -or ($resp -match 'oficial m[eé]dico')) -and -not ($resp -match '\d+\s*(mL|litros|L|minutos|min|kg)\b' -and -not $admite) -and -not $farm }
  Write-Host ("{0,2}. [{1}] {2}  ->  {3}" -f $n, $(if ($tema) { $tema } else { 'sem filtro' }), $perg, $(if ($ok) { 'OK' } else { 'FALHOU' }))
  $res += [pscustomobject]@{ n = $n; tema = $tema; pergunta = $perg; tem_resposta_no_corpus = $tem; trecho_esperado_recuperado = $recPal; fonte_recuperada = $recFonte
    melhor_fonte = $top[0].it.fonte; melhor_score = [math]::Round($top[0].s, 3); citou_fonte_valida = $citaOk; admitiu_nao_saber = $admite; citou_farmaco = $farm; resultado = $(if ($ok) { 'OK' } else { 'FALHOU' }); resposta = $resp }
}
$res | Export-Csv (Join-Path $PSScriptRoot "resultados_rag.csv") -NoTypeInformation -Encoding UTF8
$ok = @($res | Where-Object resultado -eq 'OK').Count
"=== $ok de $($res.Count) OK"
$com = @($res | Where-Object tem_resposta_no_corpus); "Com resposta no corpus: recuperou o trecho certo em $(@($com | Where-Object trecho_esperado_recuperado).Count) de $($com.Count)"
$sem = @($res | Where-Object { -not $_.tem_resposta_no_corpus }); "Sem resposta no corpus: admitiu/encaminhou em $(@($sem | Where-Object resultado -eq 'OK').Count) de $($sem.Count)"
