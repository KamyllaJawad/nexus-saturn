# 9. Segurança e privacidade

Os maiores riscos são um comando médico falso entrando na rede da nave e dados clínicos chegando a quem não deveria. As ameaças seguem o modelo STRIDE, mais duas específicas de IA.

| Ameaça | Exemplo no AstroHealth | Mitigação |
| --- | --- | --- |
| Falsificação de identidade | Um nó falso injeta leituras ou confirma um protocolo | Chave por dispositivo, autenticação mútua e decisões médicas assinadas |
| Adulteração | Alguém altera a trilha de auditoria depois de um erro | Log só de inclusão com hash encadeado, copiado para a Terra |
| Repúdio | "Não fui eu que liberei a medicação" | Cada decisão leva a identidade do humano (biometria do tablet + PIN) |
| Vazamento de informação | A família ou terceiros veem dados clínicos | Filtro de privacidade no servidor da Terra, cifragem e consentimento para saúde mental |
| Negação de serviço | Telemetria de rotina satura o link na janela de contato | Fila por prioridade, cota por classe e banda reservada para prioridade 1 |
| Elevação de privilégio | O app da família tenta acessar a API clínica | Papéis por ator; a família só lê o feed já filtrado |
| Injeção de instruções na IA | Uma mensagem externa tenta fazer o LLM "aprovar" algo | O LLM não tem permissão de ação; tudo passa pelo motor de decisões; texto externo é tratado como dado |
| Deriva do modelo | Um modelo novo começa a errar arritmias | Modo sombra e aprovação do oficial médico antes de entrar em uso |

## Regras de privacidade

- **Consentimento granular e revogável:** por tipo de dado (sinais vitais, saúde mental, ciclo hormonal, localização) e por destinatário (oficial médico, Houston, família).
- **Exceção única:** risco de vida vai ao médico sem consentimento, e isso fica registrado na auditoria.
- **Minimização:** a família recebe frases prontas, nunca números; Houston recebe o necessário para o parecer.
- **Dado de saúde é dado sensível:** tratar com o rigor da LGPD (art. 11) no Brasil, usando a HIPAA como referência de mercado nos EUA.

## Matriz de acesso

| Dado | Astronauta | Oficial médico | Comandante | Houston | Família |
| --- | --- | --- | --- | --- | --- |
| Sinais vitais próprios | Sim | Sim | Só estado (ótimo/atenção/crítico) | Sim, com atraso | Não |
| ECG bruto | Sim | Sim | Não | Sim, com atraso | Não |
| Alerta de saúde mental | Sim | Só com consentimento | Não | Só com consentimento | Não |
| Ciclo hormonal (fase, sintomas, método) | Sim | Só com consentimento | Não | Não | Não |
| Dose de radiação | Sim | Sim | Sim | Sim | Não |
| Status em frases | Sim | Sim | Sim | Sim | Sim |
| Trilha de auditoria | Própria | Sim | Sim | Sim | Não |
