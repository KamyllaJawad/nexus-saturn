# Guia Estratégico de Pitch: AstroHealth OS

Documento de alinhamento técnico, arquitetural e narrativo para a equipe de apresentação no desafio do NASA Space Apps Challenge 2026. Este guia consolida os fundamentos fisiológicos de voo espacial, a arquitetura de software de missão crítica, a viabilidade de hardware e sensores, e as diretrizes de defesa perante a banca avaliadora.

---

## 1. Visão Executiva e Posicionamento Estratégico

As missões espaciais para a Lua e Marte impõem uma ruptura definitiva com o modelo médico histórico da Estação Espacial Internacional. Em órbita baixa, a telemedicina síncrona com os médicos de voo em Houston oferece suporte quase instantâneo, com latências de sinal inferiores a um segundo e a possibilidade de evacuação emergencial rápida. No entanto, em missões de espaço profundo, o atraso de propagação de rádio bidirecional atinge entre 3 e 22 minutos, somando-se a potenciais apagões de comunicação que podem durar semanas inteiras.

Nesse cenário extremo, uma emergência médica aguda não pode aguardar uma resposta da Terra. A espaçonave precisa possuir capacidade médica autônoma, operando sob uma premissa fundamental: a inteligência artificial deve apoiar, monitorar e preparar condutas, mas a autoridade final sobre decisões clínicas e irreversíveis permanece obrigatoriamente sob controle humano.

### 1.1. O Enquadramento dos Cinco Perigos da NASA (RIDGE)

A NASA categoriza os riscos biológicos e operacionais inerentes a viagens interplanetárias sob o acrônimo RIDGE. O AstroHealth OS foi estruturado como uma resposta direta de engenharia e arquitetura de software a cada um desses eixos:

| Perigo RIDGE | Manifestação Clínica e Operacional | Resposta Arquitetural do AstroHealth OS |
| :--- | :--- | :--- |
| **R — Radiation (Radiação)** | Tempestades solares repentinas, radiação cósmica galáctica, risco elevado de câncer e síndrome aguda de radiação. | Monitoramento integrado com dosímetros de bordo; a Cosmo detecta picos de exposição e calcula a rota para o abrigo blindado; a Comandante confirma a evacuação. |
| **I — Isolation & Confinement (Isolamento)** | Declínio de humor, fadiga comportamental, sobrecarga cognitiva e esgotamento psíquico da tripulação em ambiente extremo. | Rastreamento psicofisiológico passivo via variabilidade da frequência cardíaca e actigrafia; módulo de suporte emocional com consentimento do astronauta e conexão assíncrona com a família (Elo Terra). |
| **D — Distance from Earth (Distância da Terra)** | Inviabilidade de resgate ou telecirurgia em tempo real; latência de 3 a 22 minutos e apagões prolongados de rádio. | Operação 100% *offline-first*; motor de decisões local; rede tolerante a atrasos (DTN com fila de prioridades P1 a P4) para sincronização posterior. |
| **G — Gravity Fields (Campos de Gravidade)** | Descondicionamento cardiovascular, redistribuição cefálica de fluidos, perda de massa óssea e muscular, e síndrome neuro-ocular (SANS). | Monitoramento hemodinâmico contínuo; protocolos de recondicionamento e suporte para aquisição guiada de ultrassom portátil para avaliação vascular e ocular. |
| **E — Hostile/Closed Environments (Ambiente Hostil)** | Acúmulo de dióxido de carbono na cabine, contaminação ambiental, microbioma alterado e degradação de medicamentos estocados. | Cruzamento contínuo de biomarcadores dos astronautas com sensores de qualidade do ar da cabine; controle de estoque e validade farmacológica no kit médico. |

### 1.2. A Tese do Pitch em Uma Frase

> "Quanto mais longe da Terra, mais a medicina precisa estar a bordo: o AstroHealth OS combina biossensores vestíveis de baixo consumo, modelos preditivos locais e um motor determinístico com humano no controle para garantir a sobrevivência da tripulação quando Houston estiver a 20 minutos de distância."

---

## 2. A Arquitetura AstroHealth OS: Offline-First e Humano no Controle

A arquitetura do AstroHealth OS foi desenhada sob normas de segurança de missão crítica. Para eliminar o risco de alucinações de modelos de linguagem em diagnósticos vitais, o sistema estabelece uma separação rígida entre a camada de cognição e suporte (Cosmo) e o núcleo de governança e execução (Motor de Decisões Determinístico).

### 2.1. Princípios de Engenharia de Missão

1. **Operação Offline por Padrão:** Nenhuma funcionalidade de suporte à vida ou detecção precoce de agravos clínicos depende de conexão com a infraestrutura terrestre. Todo o processamento crítico é executado no relógio e no computador de bordo.
2. **Separação de Papéis Decisórios:** A inteligência artificial nunca altera o estado de um evento médico de forma autônoma. O sistema atribui a responsabilidade clínica a um humano específico: o próprio tripulante, o Oficial Médico ou a Comandante da missão.
3. **Escalonamento Humano-para-Humano:** Se o prazo para confirmação de um alarme ou protocolo expirar sem interação, o sistema jamais delega a execução à máquina. A pendência é automaticamente transferida para o próximo humano na cadeia de comando hierárquica.
4. **Temporalidade como Dado de Primeira Classe:** Em uma arquitetura tolerante a atrasos, todo dado carrega obrigatoriamente a estampa de tempo em que foi gerado e o registro de quando foi recebido na Terra, assegurando que o médico em Houston saiba exatamente que está analisando um quadro do passado.
5. **Privacidade e Confiança Psicológica:** Alertas comportamentais e métricas de saúde mental pertencem exclusivamente ao astronauta e não saem do dispositivo sem seu consentimento explícito, salvo em situações de risco iminente de perda de vida.
6. **Integridade e Auditoria Imutável:** Todas as transições de estado, parâmetros de confiança algorítmica e confirmações humanas são registradas em uma trilha de auditoria encadeada por funções de dispersão criptográfica (*hash* encadeado), inviabilizando adulterações posteriores.

### 2.2. Níveis de Autonomia do Sistema

Para dosar a automação sem comprometer a segurança, o sistema implementa cinco níveis padronizados de autonomia operacional:

* **Nível 0 (Observar):** Registro contínuo e silencioso da telemetria fisiológica para construção da linha de base individual (frequência cardíaca, repouso, sono e variabilidade autonômica).
* **Nível 1 (Informar):** Apresentação passiva de métricas contextuais sem emissão de recomendações (exibição de tendências circadianas ou dose acumulada de radiação no turno).
* **Nível 2 (Sugerir):** O sistema detecta pequenas discrepâncias fisiológicas e propõe ações preventivas de baixo impacto que exigem validação do tripulante (hidratação, pausas respiratórias ou ajustes posturais).
* **Nível 3 (Preparar e Solicitar Confirmação):** Utilizado em eventos clínicos graves (como arritmias e crises respiratórias). A Cosmo sintetiza os dados, consulta os protocolos de bordo, prepara a conduta e solicita a confirmação expressa do médico.
* **Nível 4 (Agir e Avisar com Opção de Desfazer):** Restrito a manobras urgentes de mitigação e reversíveis, como priorização de alertas de emergência na fila de transmissão espacial ou direcionamento imediato para rotas de abrigo contra radiação, com janela de 15 segundos para veto humano.
* **Ações Proibidas à Inteligência Artificial:** Administração ou liberação de medicamentos, execução de procedimentos invasivos, remoção de tripulantes de tarefas operacionais críticas e quebra de sigilo de saúde mental sem risco de morte exigem, sem exceção, intervenção e assinatura humana.

---

## 3. Biossensores e Hardware Compatível com o Espaço

A captura de dados fisiológicos em microgravidade enfrenta restrições físicas severas que invalidam equipamentos clínicos convencionais projetados para ambientes hospitalares terrestres. O AstroHealth OS apoia-se em tecnologias de sensoriamento não invasivas, consolidadas na literatura científica aeroespacial e em missões reais.

### 3.1. Visão Geral dos Biossensores e Parâmetros

A tabela a seguir sistematiza os componentes de hardware, seus mecanismos de funcionamento, as grandezas aferidas e os desafios específicos de voo espacial que eles monitoram:

| Componente de Sensoriamento | Mecanismo de Medição Física | Parâmetros Monitorados | Resposta aos Desafios da Microgravidade | Validação Aeroespacial |
| :--- | :--- | :--- | :--- | :--- |
| **Fotopletismografia Óptica (PPG Multi-espectral)** | Emissão de luz (canais verde, vermelho e infravermelho) e leitura da luz absorvida/refletida pelas pulsações microvasculares. | Frequência cardíaca contínua, oximetria de pulso (\\(SpO_2\\)), intervalos entre batimentos (RR/IBI) e VFC. | Uso de luz vermelha e infravermelha para alcançar leitos vasculares profundos, atenuando artefatos mecânicos e desvios de perfusão causados pelo deslocamento de fluidos. | *Garmin fēnix 7* (Missão Polaris Dawn) e *Apple Watch* (Inspiration4). |
| **Eletrodos Secos de ECG em Tecido Inteligente** | Microplacas metálicas ou fios condutores tecidos que captam micropotenciais elétricos cardíacos sem gel. | Traçado eletrocardiográfico contínuo, complexos QRS, detecção de arritmias e instabilidade ventricular. | Eliminação de géis úmidos, que ressecam e causam dermatites em voos longos; fixação elástica por compressão torácica, mantendo contato contínuo sem depender da gravidade. | Sistema *Bio-Monitor / Astroskin* (Agência Espacial Canadense/NASA na ISS). |
| **Eletrodos de Resposta Galvânica da Pele (EDA/GSR)** | Mensuração da condutância elétrica dérmica decorrente da sudorese microscópica das glândulas écrinas. | Atividade eletrodérmica fásica e tônica, níveis de excitação do sistema nervoso autônomo simpático. | Mapeamento objetivo de estresse agudo, sobrecarga cognitiva e ansiedade sem interrupção de tarefas; sensores integrados à fita interna da pulseira. | Relógio médico *EmbracePlus* (NASA/TRISH). |
| **Unidades Inerciais MEMS (IMU de 3 eixos)** | Microacelerômetros e microgiroscópios capacitivos de estado sólido integrados em silício. | Actigrafia tridimensional, padrões de movimentação motora, microtremores e fases do sono. | Baixíssimo consumo elétrico; detecção precisa de distúrbios de sono e vigília em cabines onde o ciclo natural de 24 horas não existe. | Actígrafo da Condor Instruments na Artemis II (parceria em potencial; ficha em `parcerias.md`) e bancos de dados EXPAND. |
| **Termometria Cutânea Digital** | Termistores semicondutores de alta sensibilidade posicionados em contato térmico com a epiderme. | Flutuações da temperatura periférica minuto a minuto e curva de termorregulação circadiana. | Detecção precoce de vasoconstrição periférica ligada a estresse, infecções agudas ou desajuste nos sistemas de controle térmico da cabine e trajes. | Vestuário inteligente *Astroskin* e smartwatches clínicos. |
| **Ultrassom Portátil Semicondutor** | Microtransdutores ultrassônicos em chip de silício (CMUT) acoplados a tablets comerciais. | Ecodopler da veia jugular interna, diâmetro da bainha do nervo óptico e volume da bexiga. | Monitoramento autônomo da estase venosa jugular, prevenção de trombose em voo e rastreamento da síndrome neuro-ocular (SANS) por tripulantes leigos guiados por IA. | Sonda *Butterfly iQ+* (Missão SpaceX Inspiration4). |

### 3.2. Critérios Críticos de Compatibilidade Espacial

Para que os sensores sejam integrados a uma missão interplanetária, o projeto atende a cinco restrições mandatórias de engenharia de voo:

1. **Eliminação de Consumíveis e Resíduos Voláteis:** Eletrodos com gel líquido ou esponjas descartáveis são proibidos em missões prolongadas devido ao ressecamento rápido e à dispersão perigosa de gotículas em gravidade zero. O hardware prioriza eletrodos secos laváveis e biossensores ópticos.
2. **Acoplamento Mecânico por Compressão:** Na ausência de peso, o sensor tende a flutuar sobre a pele com a movimentação do astronauta, gerando ruído excessivo de contato. O uso de malhas elásticas respiráveis e fechos ergonômicos de compressão graduada garante impedância estável.
3. **Controle de Desgaseificação (*Outgassing* e Inflamabilidade):** Todo o encapsulamento polimérico, fiações e pulseiras utilizam polímeros certificados de grau espacial, garantindo taxa nula de liberação de gases tóxicos na atmosfera selada e reciclada do habitat.
4. **Eficiência Energética e Coleta Contínua:** Equipamentos biomédicos não podem exigir ciclos frequentes de recarga que sobrecarreguem o cronograma da tripulação. O uso de microcontroladores de ultra-baixo consumo e protocolos BLE permite registros ininterruptos de 24 a 48 horas por ciclo.
5. **Armazenamento Não Volátil Embarcado:** Para contornar interferências eletromagnéticas e perdas temporárias de enlace na rede local da espaçonave, os dispositivos mantêm memória interna protegida, assegurando que nenhuma janela de dados fisiológicos seja descartada.

---

## 4. Inteligência Artificial Explicável e Modelos de Bordo

O pipeline analítico do AstroHealth OS utiliza modelos de aprendizado de máquina clássicos e explicáveis na borda, rejeitando caixas-pretas inescrutáveis em favor de métricas claras e rastreáveis pelo corpo médico. O processamento segue uma sequência estruturada e auditável:

1. **Camada de Aquisição e Pré-filtragem:** Os sinais de ECG e fotopletismografia alimentam o modelo M2, que avalia a integridade do traçado e filtra artefatos de movimento ou sensores frouxos.
2. **Classificação Diagnóstica:** Os intervalos entre batimentos com qualidade confirmada são processados pelo modelo M1 para identificação de fibrilação atrial e instabilidades de ritmo cardíaco.
3. **Governança Determinística:** O evento detectado ingressa no Motor de Decisões, que avalia o nível de autonomia aplicável e aciona a máquina de estados correspondente.
4. **Enriquecimento com Evidências:** A Cosmo consulta a base local de protocolos clínicos em vetorizador embarcado e formula a recomendação médica acompanhada das justificativas fisiológicas.
5. **Decisão e Disseminação:** O Oficial Médico valida o protocolo no Painel de Bordo; o evento resolvido é transmitido com prioridade máxima pelo Gateway DTN para revisão tardia em Houston e para o informativo simplificado da família.

### 4.1. M1: Detector de Fibrilação Atrial e Arritmias

* **Base de Dados Real:** Treinado sobre 8.528 gravações eletrocardiográficas reais do *PhysioNet Computing in Cardiology (CinC) Challenge 2017*, disponibilizado sob licença aberta ODC-By.
* **Engenharia de Características:** Extração de intervalos entre picos R (série temporal RR) e cálculo de métricas no domínio do tempo e não lineares: frequência cardíaca média, desvio padrão dos intervalos normais (SDNN), raiz quadrada da média das diferenças ao quadrado entre intervalos adjacentes (RMSSD), proporção de intervalos vizinhos com diferença superior a 50 ms (pNN50), dispersões elípticas do gráfico de Poincaré (SD1 e SD2) e entropia aproximada.
* **Algoritmo e Meta de Aceite:** Random Forest ou Gradient Boosting com balanceamento de pesos por classe; meta de aceite fixada em F1-score superior a 0,75 para a classe de fibrilação atrial no conjunto de teste.
* **Local de Execução:** Executado no microprocessador do relógio ou nó local de borda, gerando alertas no pulso em fração de segundo.

### 4.2. M2: Detector de Qualidade de Sinal e Filtro de Alarmes Falsos

* **Objetivo:** Reduzir a fadiga de alarmes, um dos riscos operacionais mais documentados em telemetria contínua.
* **Mecanismo:** Analisa a morfologia do sinal de PPG/ECG, verificando curtose, fração de sinal achatada por saturação óptica, energia espectral em baixa frequência e presença de artefatos de movimento brusco.
* **Comportamento Clínico:** Quando detecta contato inadequado, o sistema não dispara alarme médico. O relógio emite uma mensagem preventiva discreta ao astronauta: *"Seu relógio está folgado? Ajuste a pulseira"*. Apenas leituras com alto índice de qualidade seguem para o classificador M1.

### 4.3. M3: Linha de Base Pessoal e Equilíbrio Homeostático

* **Fundamentação:** Em microgravidade, a redistribuição volêmica e a adaptação cardiovascular alteram os parâmetros médios de repouso dos astronautas. Comparar um astronauta com tabelas populacionais terrestres gera diagnósticos distorcidos.
* **Método Matemático:** Cálculo de escores padronizados robustos baseados na mediana individual e no desvio absoluto da mediana (MAD), atualizados continuamente ao longo dos dias de missão.
* **Interface:** Consolidação dos parâmetros no Avatar de Homeostase exibido no relógio em três estados visuais intuitivos (Ótimo, Atenção, Crítico).
* **Combinação de sinais:** O z robusto continua definindo a faixa de cada sinal. Ao lado dele, um Isolation Forest por tripulante (`m3-if-0.1`, [ADR-012](../4-arquitetura/adr/0012-linha-de-base-com-isolation-forest.md)) marca quando a combinação sai do padrão daquela pessoa, mesmo sem um sinal sozinho na faixa crítica. O motor só abre sugestão de nível 1 se a floresta marcar anomalia, o M2 classificar o sinal como bom e nenhum sinal estiver crítico. A família não recebe o escore.

### 4.4. Cosmo: Copiloto Médico com RAG Local

* **Arquitetura de Bordo:** Modelo de linguagem local quantizado executado localmente via Ollama, conectado a um banco vetorial ChromaDB com orquestração LangChain, sem qualquer dependência de servidores em nuvem.
* **Base de Conhecimento:** Indexação vetorial dos manuais clínicos de exploração espacial da NASA, protocolos de suporte cardiovascular, guia de recursos farmacológicos da enfermaria de bordo e fichas técnicas de equipamentos.
* **O Card "Por que a Cosmo sugeriu isso?":** Toda orientação gerada pela Cosmo ao Oficial Médico é acompanhada por um quadro estruturado de explicabilidade clínica contendo:
  1. A conduta proposta resumida de forma direta e concisa.
  2. O grau de confiança estocástica do modelo e o identificador exato da versão do algoritmo.
  3. Os três parâmetros fisiológicos objetivos do paciente que mais pesaram na decisão.
  4. O trecho exato do protocolo médico indexado que embasa a sugestão.
  5. Hipóteses alternativas e diagnósticos diferenciais a serem considerados pelo médico.
* **Segurança Farmacológica em Dois Passos:** O protocolo e a liberação de fármacos ocorrem em etapas separadas. A prescrição e dosagem requerem autenticação por biometria ou código de segurança do médico no terminal da enfermaria.

---

## 5. Análise de Viabilidade Financeira e Custos de Hardware

Para demonstrar maturidade de gestão e capacidade de execução perante a banca, o projeto apresenta uma estrutura orçamentária escalonada em quatro horizontes técnicos:

### Cenário A: MVP de Software para Demonstração (Plano do Hackathon de 48h)
* **Custo Total: R\$ 0,00 (Gratuito)**
* **Infraestrutura:** Estações de desenvolvimento e notebooks dos membros da equipe.
* **Sinais Fisiológicos:** Dados reais abertos da base PhysioNet CinC Challenge 2017 somados a geradores matemáticos de telemetria sintética multivariada para quatro tripulantes.
* **Stack Tecnológica:** Modelos clássicos locais via `scikit-learn`, `FastAPI`, banco `SQLite`, motor `transitions`, vetorizador `ChromaDB` e LLM local via `Ollama`.
* **Proposta de Valor:** Validação completa de requisitos, contratos JSON e experiência do usuário com custo zero de infraestrutura em nuvem.

### Cenário B: Bancada Física Maker com Microcontrolador (Prova de Conceito de Laboratório)
* **Custo Total Estimado: R\$ 250,00 a R\$ 550,00**
* Permite comprovar a aquisição de sinais físicos em tempo real transmitidos via rede local para o AstroHealth OS:
  * Placa controladora com Wi-Fi/BLE (ESP32 NodeMCU 32-bit dual-core): **R\$ 45,00 – R\$ 70,00**
  * Módulo óptico PPG com LEDs infravermelho e vermelho (MAX30102): **R\$ 30,00 – R\$ 50,00**
  * Sensor de ECG de 1 derivação com cabos de contato (AD8232): **R\$ 60,00 – R\$ 95,00**
  * Sensor de resposta galvânica da pele / atividade eletrodérmica analógica: **R\$ 70,00 – R\$ 130,00**
  * Unidade inercial MEMS acelerômetro/giroscópio (MPU-6050): **R\$ 20,00 – R\$ 35,00**
  * Sensor de temperatura cutânea digital por contato térmico (MAX30205): **R\$ 35,00 – R\$ 60,00**
  * Módulo de alimentação com bateria recarregável LiPo 3.7V e regulador TP4056: **R\$ 40,00 – R\$ 60,00**

### Cenário C: Dispositivos Vestíveis Comerciais com Acesso a SDK de Pesquisa
* **Custo Total Estimado: R\$ 1.100,00 a R\$ 3.000,00 por astronauta**
* Utilização de hardware comercial de alta precisão compatível com a literatura de pesquisa:
  * Smartwatch baseado em Wear OS (como Samsung Galaxy Watch 4 ou 5 Pro), com acesso a dados brutos de PPG multi-comprimento de onda, intervalos IBI e termometria via SDKs autorizados: **R\$ 1.100,00 – R\$ 2.000,00**
  * Cinta torácica com eletrodos secos em malha condutora (Polar H10 com ECG bruto): **R\$ 900,00 – R\$ 1.300,00**

### Cenário D: Equipamentos de Grau Clínico e Espacial Real (Referência de Voo)
* **Custo Total Estimado: US\$ 1.500 a US\$ 5.000+ (R\$ 8.000 a R\$ 30.000+ por unidade)**
* Dispositivos de referência operacional desenvolvidos sob consórcios das agências espaciais:
  * Relógio médico *Empatica EmbracePlus*: Certificado pela FDA, financiado pelo consórcio NASA/TRISH para o programa Artemis, contendo PPG infravermelho, termometria e eletrodos secos de EDA na pulseira.
  * Sistema *Bio-Monitor / Astroskin* (Carré Technologies / CSA): Vestimenta biométrica de malha condutora e eletrodos secos laváveis operada na ISS, comercializada sob licenças institucionais de pesquisa clínica e aeroespacial.

---

## 6. O Hero-Flow Operacional de 90 Segundos: Roteiro para a Banca

Para a apresentação de impacto ao vivo ou gravação de vídeo, o time deve executar o roteiro sincronizado de 90 segundos, demonstrando o trânsito de dados de ponta a ponta através dos quatro ativos do sistema:

### Segundo 00 a 20: A Rotina e a Premissa de Marte
* **Ação Visual:** Abertura no **Relógio da Sarah**. A tela inicial exibe o Avatar de Homeostase com status verde (Ótimo). O apresentador gira a coroa digital do relógio passando pelas telas de insight preventivo da Cosmo, chat local e sincronia com a Terra.
* **Fala do Apresentador:** *"Estamos no dia 140 de trânsito em direção a Marte. A latência de rádio bidirecional é de 16 minutos. O controle da missão em Houston não consegue intervir em tempo real. A saúde da tripulação precisa de autonomia."*
* **Ação no Console de Houston:** A tela de Houston exibe em destaque o aviso visual de telemetria atrasada: *"Você está visualizando dados gerados a bordo há 8 minutos e 20 segundos"*.

### Segundo 20 a 40: O Sensor Solto e o Filtro de Alarmes Falsos
* **Ação Visual:** Injeta-se uma leitura ruidosa na simulação. O modelo M2 identifica sinal degradado com perda de acoplamento óptico.
* **Comportamento do Relógio:** O relógio da Sarah vibra suavemente e apresenta a mensagem: *"Seu relógio está folgado? Por favor, ajuste o fecho"*. Nenhum alarme sonoro toca; nenhum alerta é enviado à enfermaria.
* **Fala do Apresentador:** *"No espaço, sensores ópticos perdem contato na microgravidade. Antes de acordar o médico ou gerar pânico, o modelo M2 valida a integridade física do sinal, filtrando o falso alarme."*

### Segundo 40 a 65: A Emergência Cardíaca e a Decisão do Médico
* **Ação Visual:** Sarah ajusta o relógio e inicia uma crise súbita de fibrilação atrial gerada a partir do dataset real do CinC 2017. Em menos de um segundo, o classificador M1 detecta arritmia sustentada com frequência cardíaca de 168 bpm e \\(SpO_2\\) em 88%.
* **No Relógio:** Alerta crítico P1 com instrução imediata em linguagem direta: *"Pare sua atividade e sente-se imediatamente. Médico alertado"*.
* **No Painel de Bordo (Enfermaria):** O terminal do Dr. Marcus soa alerta sonoro em menos de 2 segundos. A tela abre o traçado em tempo real, as derivações de ECG e o card explicativo *"Por que a Cosmo sugeriu isso?"*.
* **Fala do Apresentador:** *"Em menos de dois segundos, o Oficial Médico tem em mãos o traçado, o nível de confiança de 87% e a evidência clínica objetiva. A Cosmo recomenda o protocolo de suporte respiratório e repouso, fundamentado no manual médico de bordo."*
* **Ação do Médico:** O Dr. Marcus clica em *Confirmar Protocolo* e, em uma tela protegida separada, autentica com assinatura eletrônica a dosagem e liberação do medicamento.

### Segundo 65 a 90: Tolerância a Atraso e Privacidade Familiar
* **Ação Visual:** O motor de decisões fecha o ciclo a bordo e despacha o pacote prioritário P1 para o Gateway DTN. O pacote entra na fila de espaço profundo.
* **No Console de Houston:** Após o atraso simulado, o alerta chega ao *Flight Surgeon* terrestre, acompanhado de carimbo com a hora de origem a bordo e a decisão já executada pelo Dr. Marcus. Houston valida o procedimento e emite parecer favorável assíncrono.
* **No App da Família:** A família recebe no celular uma mensagem humanizada: *"A Sarah está em repouso e sendo assistida pelo oficial médico"*. Nenhuma métrica numérica, ECG ou diagnóstico invasivo é exposto.
* **Fechamento do Apresentador:** *"A tripulação resolveu a emergência antes de Houston receber o primeiro bit. Decisão humana, inteligência local e dignidade para quem explora o universo. Este é o AstroHealth OS."*

---

## 7. Matriz de Defesa: Respostas Técnicas para a Sabatina

A banca avaliadora da NASA ou de desafios de inovação costuma pressionar os times em vulnerabilidades clássicas de projetos de saúde e inteligência artificial. Utilize as respostas estruturadas abaixo:

### Pergunta 1: "O AstroHealth OS é considerado um dispositivo médico certificado?"
* **Resposta do Time:** *"Não. O AstroHealth OS é um protótipo de software de suporte à decisão clínica e telemetria operacional desenvolvido para fins de pesquisa e demonstração no NASA Space Apps Challenge. Em conformidade com as boas práticas de engenharia biomédica, o sistema exibe avisos expressos em todas as interfaces de que não substitui o julgamento clínico profissional e não deve ser utilizado como equipamento diagnóstico certificado sem ensaios clínicos rigorosos e aprovação regulatória prévia."*

### Pergunta 2: "Por que vocês não deixaram um agente de modelo de linguagem (LLM) tomar as decisões médicas sozinho?"
* **Resposta do Time:** *"Modelos de linguagem generativa são probabilísticos e suscetíveis a alucinações, variações de contexto e respostas imprevisíveis, o que é inaceitável em suporte de vida interplanetário. Nossa arquitetura adota a ADR-002: separamos a geração de linguagem do motor de decisões. O LLM atua estritamente como copiloto explicativo (RAG sobre protocolos indexados), enquanto o motor que gerencia estados, alarmes e escalonamentos é um autômato determinístico, formalmente verificável, testável e imune a desvios conceituais."*

### Pergunta 3: "O dataset do PhysioNet CinC 2017 foi coletado na Terra com aparelhos segurados pelos dedos. Como vocês justificam o uso dele para um relógio no espaço?"
* **Resposta do Time:** *"Reconhecemos explicitamente essa limitação de domínio tanto no slide de modelos quanto em nossa documentação. Não existem bases de dados abertas contendo milhares de horas de fibrilação atrial registradas por smartwatches em astronautas durante voos orbitais. O PhysioNet CinC 2017 foi escolhido por ser o padrão ouro aberto com licença ODC-By para ECG de uma única derivação, demonstrando a viabilidade computacional de extrair atributos de intervalos RR em tempo real na borda. No espaço, a camada M3 de linha de base pessoal e a camada M2 de qualidade de sinal mitigam as variações individuais decorrentes da redistribuição de fluidos."*

### Pergunta 4: "Como o modelo lida com o desbalanceamento severo de classes da base de arritmia?"
* **Resposta do Time:** *"A base de treino do CinC 2017 possui 5.154 traçados normais contra apenas 771 de fibrilação atrial. Avaliar o sistema por acurácia geral seria um erro grosseiro que mascararia falsos negativos críticos. Por isso, aplicamos penalização de pesos proporcionais às classes inversas no algoritmo de Random Forest, calibramos os limiares de decisão exclusivamente no conjunto de validação estratificada e reportamos nosso desempenho medido pelo F1-score específico da classe de fibrilação atrial no conjunto de teste isolado."*

### Pergunta 5: "E se o link com a Terra cair por duas semanas inteiras durante uma tempestade solar?"
* **Resposta do Time:** *"O AstroHealth OS foi concebido sob a premissa de tolerância total a atrasos e desconexões. Todas as rotinas de proteção à vida, avaliação diagnóstica, alertas e banco vetorial local funcionam sem qualquer perda de capacidade a bordo. Nosso gateway DTN armazena todos os pacotes em uma base embarcada com fila priorizada. Quando a janela de contato reabrir, os pacotes de classe P1 (emergências médicas) são transmitidos primeiro com garantia de entrega e custódia, e a ferramenta de telemetria de Houston reconstrói toda a cronologia ocorrida durante o apagão."*

### Pergunta 6: "Por que a família não pode ver a frequência cardíaca ou a oximetria do astronauta?"
* **Resposta do Time:** *"Por respeito à psicologia de isolamento e ética médica. O atraso de sinal de até 22 minutos significa que qualquer métrica anormal vista pela família na Terra já teria ocorrido há quase meia hora, gerando estresse e desespero desnecessários a milhares de quilômetros de distância sem que a família pudesse agir. O App da Família implementa um filtro estrito de privacidade gerenciado no servidor da Terra que traduz a situação em frases simples de acolhimento e status humano, preservando o sigilo médico da tripulação."*

---

## 8. Checklist de Prontidão Técnica para o Pitch

Antes de iniciar a gravação do vídeo ou a apresentação presencial para os avaliadores, a equipe deve checar os seguintes itens:

* **Aviso Regulatório:** O rótulo *"Protótipo Experimental — Não é um Dispositivo Médico Homologado"* está visível no rodapé dos slides e nas quatro telas da demonstração.
* **Atribuição Acadêmica ODC-By:** O dataset PhysioNet CinC Challenge 2017 e a publicação original de Clifford et al. (2017) estão devidamente creditados no slide de metodologia de dados e no repositório GitHub.
* **Execução dos Quatro Ativos:** O navegador está com as quatro telas abertas em abas pré-configuradas (Relógio, Painel de Bordo, Console de Houston e App da Família).
* **Plano B Ativo:** Caso o ambiente de execução local com Ollama enfrente lentidão de inferência na máquina de apresentação, o botão de chaveamento para respostas pré-sintetizadas do mock está funcional no arquivo de front-end.
* **Demonstração do M2:** O clique de teste para o evento *"Sensor Solto"* confirma a exibição da mensagem de pulseira folgada sem disparar o protocolo de arritmia médica.
* **Controle do Cronômetro:** O roteiro narrativo foi cronometrado e não excede os 90 segundos estipulados para a demonstração principal.
---

## 9. Referências Bibliográficas e Fontes de Dados

Para assegurar a rastreabilidade acadêmica, a integridade metodológica e o rigor de engenharia exigidos perante a banca avaliadora, o projeto AstroHealth OS fundamenta-se nas seguintes fontes bibliográficas, normas de missão e repositórios de dados abertos:

### 9.1. Medicina Aeroespacial e Saúde Autônoma no Espaço Profundo

1. **Gupta, R., & Ghosh, P. S. (2025).** *Advancements in health monitoring technologies for astronauts in deep space missions: A Review.* Life Sciences in Space Research (Elsevier / PubMed). DOI: 10.1016/j.lssr.2025.06.011 (PMID: 41136019).
   * **Contribuição ao Projeto:** Revisão sistemática sobre biossensores miniaturizados, inteligência artificial preditiva e a transição da telemedicina síncrona para a tomada de decisão médica autônoma a bordo durante viagens interplanetárias.
2. **Kerremans, S., Dobney, W., Ferreira da Silva Miranda, S., Cinelli, I., Baatout, S., et al. (2026).** *Leveraging artificial intelligence for autonomous space healthcare: current evidence, operational architecture and research priorities for deep-space exploration.* Frontiers in Space Technologies, 7, 1741121. DOI: 10.3389/frspt.2026.1741121.
   * **Contribuição ao Projeto:** Mapeamento de arquitetura operacional de suporte médico com IA, modelos de aprendizado profundo para triagem de arritmias cardíacas por ECG e diretrizes mandatórias de supervisão e veto humano no espaço profundo.
3. **Lacinski, R. A., Steller, J. G., Anderson, A., & Nelson, A. M. (2024).** *Harnessing artificial intelligence for medical diagnosis and treatment during space exploration missions.* NASA Technical Reports Server (NTRS), Documento Técnico NASA/TM-20240004315.
   * **Contribuição ao Projeto:** Relatório técnico da NASA avaliando sistemas de apoio à decisão clínica (CDSS), modelos de linguagem supervisionados e algoritmos de triagem para mitigar o atraso de rádio de até 40 minutos em missões a Marte.
4. **Smith, N., Barrett, E., Jay, C., Peters, D., Ryan, R., et al. (2023).** *Off-World Mental Health: Considerations for the Design of Well-being–Supportive Technologies for Deep Space Exploration.* JMIR Formative Research, 7, e37784. DOI: 10.2196/37784 (PMC9975927).
   * **Contribuição ao Projeto:** Diretrizes de psicologia de isolamento e design de suporte não invasivo ao bem-estar e saúde mental em ambientes confinados e extremos (ICE), integrando o modelo teórico METUX e agentes conversacionais de suporte emocional.

### 9.2. Missões Orbitais, Consórcios Espaciais e Validação Operacional

5. **Jones, C. W., Urquieta, E., Donoviel, D. B., Mateus, J., Sargsyan, A. E., et al. (2024).** *Molecular and physiological changes in the SpaceX Inspiration4 civilian crew.* Nature, 632, 1155–1164. DOI: 10.1038/s41586-024-07648-x (PMC11357997).
   * **Contribuição ao Projeto:** Estudo de referência do consórcio SOMA / TRISH sobre a tripulação civil da Inspiration4, avaliando alterações fisiológicas agudas através de smartwatches, ultrassom portátil (Butterfly iQ+) e biomarcadores moleculares.
6. **Agência Espacial Canadense (CSA / ASC) & NASA.** *Bio-Monitor: Keeping an eye on astronauts' vital signs.* Carré Technologies / Astroskin. Programa Operacional na Estação Espacial Internacional (ISS).
   * **Contribuição ao Projeto:** Especificação do sistema de vestuário inteligente com eletrodos secos condutores de ECG de 3 derivações e cintas de indutância respiratória operando continuamente a bordo da ISS.
7. **NASA Spinoff & TRISH (2024).** *Medical-Grade Smartwatch Can Monitor Astronauts, Patients.* National Aeronautics and Space Administration, Johnson Space Center.
   * **Contribuição ao Projeto:** Relatório de transferência de tecnologia do relógio médico EmbracePlus (Empatica), financiado pelo consórcio TRISH/NASA para monitoramento de estresse autonômico (EDA/GSR), oximetria e sono no programa Artemis.
8. **Garmin Newsroom & TRISH (2024).** *Garmin smartwatches reach new heights with Polaris Dawn space mission.* Programa EXPAND, Baylor College of Medicine.
   * **Contribuição ao Projeto:** Aplicação de smartwatches comerciais de alta autonomia (Garmin fēnix 7) durante a missão orbital Polaris Dawn para coleta biométrica contínua em ambiente espacial de alta radiação.

### 9.3. Biossinais, Estresse, Ansiedade e Carga Cognitiva com Vestíveis

9. **Pinge, A., et al. (2024).** *Detection and monitoring of stress using wearables: a systematic review.* Frontiers in Computer Science, 6, 1478851. DOI: 10.3389/fcomp.2024.1478851.
   * **Contribuição ao Projeto:** Revisão sistemática sobre o estado da arte no processamento de sinais fisiológicos (VFC, EDA e temperatura) e pipelines de aprendizado de máquina para rastreamento de estresse e fadiga mental.
10. **Gorgan, R.-A., & Ștefănuț, T.-T. (2025).** *Cognitive Load Detection Using Physiological Data from Commercial Smartwatches.* Proceedings of the 22nd International Conference on User-Centered System Interactivity (ICUSI / RoCHI 2025), pp. 141–148. DOI: 10.37789/icusi.2025.20.
    * **Contribuição ao Projeto:** Demonstração experimental de que métricas de variabilidade da frequência cardíaca obtidas por smartwatches comerciais correlacionam-se de forma estatisticamente significante com picos de carga cognitiva e esforço mental.
11. **Fernandes, R. M. M., et al. (2026).** *Predição de Níveis de Ansiedade Utilizando Dados de Smartwatches em Ambiente Não Controlado.* Anais do Simpósio Brasileiro de Computação Aplicada à Saúde (SBCAS). DOI: 10.5753/sbcas.2026.21603.
    * **Contribuição ao Projeto:** Investigação sobre redes neurais e aprendizado profundo aplicados a dados de acelerômetros em dispositivos vestíveis para predição contínua e não invasiva de estados de ansiedade em ambientes livres de laboratório.
12. **Franceschina, M. A., et al. (2025).** *Identificação de Esforço Cognitivo com Auxílio de Dispositivos Vestíveis e Inteligência Artificial.* Anais da Escola Regional de Engenharia de Software (ERES). DOI: 10.5753/eres.2025.15429.
    * **Contribuição ao Projeto:** Comparativo de desempenho entre vestíveis comerciais e equipamentos clínicos na identificação de sobrecarga de trabalho mental em tarefas de engenharia de software.
13. **Scheffler, N. (2024).** *Detecção de ansiedade por meio de machine learning a partir de sinais vitais.* Trabalho de Conclusão de Curso, Instituto Federal do Rio Grande do Sul (IFRS). Repositório Institucional: dspace.ifrs.edu.br/xmlui/handle/123456789/3046.
    * **Contribuição ao Projeto:** Extração e classificação de parâmetros autonômicos em tempo real a partir de biossensores comerciais para suporte a diagnósticos precoces de crises de ansiedade.
14. **Coelho, V. C., & Oliveira, M. E. R. (2024).** *Da Pesquisa à Clínica: Neurometria e suas Contribuições no Manejo da Ansiedade, do Estresse e do TDAH.* Aya Editora. DOI: 10.47573/aya.5379.3.24.27.
    * **Contribuição ao Projeto:** Fundamentos fisiológicos da neurometria funcional, integrando eletrodos de condutância dérmica e traçados autonômicos em protocolos objetivos de biofeedback e neurofeedback.
15. **Sunarya, P. A., et al. (2024).** *Anxiety Prediction Model Based on Smartwatch Activity Data and Self-Reported Affect Scale in Adolescents.* Journal of Orange Technology, 2(1), 43. DOI: 10.68012/jot.v2i1.43.
    * **Contribuição ao Projeto:** Modelagem preditiva cruzando dados objetivos de actigrafia e sensores de pulso com escalas psicológicas padronizadas de afeto.
16. **Ranze, M. G. (2024).** *E-Health: Avaliação da Qualidade de Vida Através de Informações de Dispositivos Vestíveis.* Dissertação de Mestrado, Instituto Politécnico de Bragança (ProQuest ID: 31292147).
    * **Contribuição ao Projeto:** Framework de avaliação de saúde preventiva e índices de bem-estar contínuo a partir de telemetria agregada de vestíveis.

### 9.4. Repositórios Abertos de Dados e Especificações de Engenharia de Bordo

17. **Clifford, G. D., Liu, C., Moody, B., Lehman, L. H., Silva, I., Li, Q., Johnson, A. E., & Mark, R. G. (2017).** *AF Classification from a Short Single Lead ECG Recording: The PhysioNet/Computing in Cardiology Challenge 2017.* Computing in Cardiology, 44, 1–4. Licença aberta ODC-By. Repositório PhysioNet (physionet.org/content/challenge-2017/1.0.0/).
    * **Contribuição ao Projeto:** Dataset de padrão ouro com 8.528 traçados de ECG de 1 derivação utilizado para treinamento e teste do modelo M1 de detecção de fibrilação atrial do AstroHealth OS.
18. **Documentação Arquitetural e Especificações Técnicas AstroHealth OS (2026):**
    * *Arquitetura de Software (ADR-001 a ADR-012):* Especificação formal da arquitetura orientada a eventos, isolamento do motor determinístico, barramento DTN, trilha de auditoria criptográfica com hash encadeado e linha de base do M3 com z robusto e Isolation Forest (ADR-012).
    * *MVP — Dados, Modelos e Telas:* Definição dos contratos de dados JSON, pipelines dos modelos M1/M2/M3, governança de autonomia de Níveis 0 a 4 e especificações de interface dos quatro ativos (Relógio, Painel de Bordo, Console de Houston e App da Família).
    * *Plano Operacional da Equipe:* Cronograma de entrega de 48 horas, matriz de riscos técnicos e divisão de papéis da equipe no NASA Space Apps Challenge.

### 9.5. Parceria em potencial e precedente brasileiro em voo

19. **Alisson, E. (2026, 29 de abril).** *Tecnologia brasileira ajuda a Nasa a melhorar o bem-estar de astronautas em missões no espaço.* Jornal da USP. https://jornal.usp.br/universidade/tecnologia-brasileira-ajuda-a-nasa-a-melhorar-o-bem-estar-de-astronautas-em-missoes-no-espaco/
    * **Contribuição ao Projeto:** Precedente de um actígrafo de pulso brasileiro, da Condor Instruments, a bordo da Artemis II para sono, atividade e ritmo circadiano. A Condor é parceria em potencial do hardware de actigrafia. A ficha de uso no pitch, com o que a banca pode ouvir, está em [parcerias.md](parcerias.md). A reprodução da matéria pede a citação do Jornal da USP e de Elton Alisson (Agência Fapesp).
