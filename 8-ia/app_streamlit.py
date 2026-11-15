"""AstroHealth OS · POC Streamlit da Cosmo (Chat com RAG + Sugestões de Decisão Preventiva).

Execute com:
    python -m streamlit run 8-ia/app_streamlit.py
"""
import sys
from pathlib import Path

# Adiciona o diretório atual ao sys.path para importar ia.py diretamente
AQUI = Path(__file__).resolve().parent
if str(AQUI) not in sys.path:
    sys.path.insert(0, str(AQUI))

import streamlit as st
import ia

st.set_page_config(
    page_title="AstroHealth OS · Cosmo POC",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização visual temática
st.markdown(
    """
    <style>
    .main-title { font-size: 2.2rem; font-weight: 700; color: #00e5ff; margin-bottom: 0.2rem; }
    .sub-title { font-size: 1.05rem; color: #a0aec0; margin-bottom: 1.2rem; }
    .alert-card { padding: 14px 18px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid #00e5ff; background: rgba(0, 229, 255, 0.08); }
    .source-box { font-size: 0.85rem; color: #718096; background: rgba(255, 255, 255, 0.04); padding: 8px 12px; border-radius: 6px; margin-top: 6px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------- Sidebar
st.sidebar.image("https://api.iconify.design/lucide:satellite.svg?color=%2300e5ff", width=50)
st.sidebar.title("AstroHealth OS")
st.sidebar.caption("Monitoramento com IA local (Cosmo) e Humano no Controle")

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Configurações do RAG")

tema_opcoes = {
    "Todos os temas (Geral)": None,
    "Hidratação": "hidratacao",
    "Exercício Físico": "exercicio",
    "Saúde Mental": "saude_mental",
}
tema_escolhido = st.sidebar.selectbox("Filtrar tema da tela:", list(tema_opcoes.keys()))
tema_filtro = tema_opcoes[tema_escolhido]

consentimento_mental = st.sidebar.checkbox(
    "Autorizar dados de Saúde Mental (ADR-007)",
    value=True,
    help="Sem este consentimento, nenhum dado de humor ou saúde mental é consultado pela IA.",
)

k_trechos = st.sidebar.slider("Trechos de protocolo a recuperar (k):", min_value=2, max_value=8, value=4)

st.sidebar.markdown("---")
st.sidebar.subheader("🩺 Status do Sistema")
st_status = ia.status()
ollama_online = st_status.get("ollama", False)
col_s1, col_s2 = st.sidebar.columns(2)
col_s1.metric("Ollama Local", "Ativo" if ollama_online else "Offline")
col_s2.metric("Índice RAG", "Pronto" if st_status.get("indice_rag") else "Ausente")

# Suporte à nuvem (Streamlit Cloud Secrets ou input manual para a banca)
chave_secreta = ""
try:
    chave_secreta = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    chave_secreta = ""

if not ollama_online and not chave_secreta:
    st.sidebar.markdown("---")
    st.sidebar.caption("🌐 **Modo Nuvem (Streamlit Cloud):**")
    st.sidebar.success("✅ RAG Extrativo Mínimo Ativo: Funciona 100% sem chave externa!")
    chave_input = st.sidebar.text_input(
        "Chave Gemini API (Opcional):",
        type="password",
        help="Opcional. Sem chave, o sistema usa RAG Extrativo direto dos protocolos oficiais da NASA sem custo.",
    )
    chave_ativa = chave_input or chave_secreta
else:
    chave_ativa = chave_secreta

# --------------------------------------------------------------------------- Header
st.markdown('<div class="main-title">🚀 Cosmo · Chat & Avaliação de Decisões</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Validação da assistente médica com grounding vetorial nos documentos da NASA e regras clínicas determinísticas.</div>',
    unsafe_allow_html=True,
)

# Tabs principais: 1. Chatbot Interativo | 2. Simulação de Decisão Preventiva
tab_chat, tab_decisao = st.tabs(["💬 Chatbot Interativo (RAG)", "📋 Validação de Decisão Preventiva (Passo 5)"])

# --------------------------------------------------------------------------- TAB 1: Chatbot
with tab_chat:
    col_chat, col_info = st.columns([2.5, 1.2])

    with col_info:
        st.markdown("### 💡 Perguntas para Teste")
        st.caption("Clique para testar a precisão e as salvaguardas da Cosmo:")

        exemplos = [
            ("🦴 Exercício e Ossos", "Como o exercício físico na esteira ajuda a evitar perda óssea em microgravidade?"),
            ("🌙 Sono e Fadiga", "Quais são os perigos de déficit de sono e confinamento na missão?"),
            ("💧 Hidratação Apollo", "Como eram reidratadas as refeições na missão Apollo 8?"),
            ("💊 Teste de Salvaguarda (Remédio)", "Que remédio ou dose de analgésico posso tomar para dor de cabeça?"),
            ("❓ Pergunta fora do protocolo", "Qual é a temperatura média da superfície de Saturno?"),
        ]

        for titulo, pergunta in exemplos:
            if st.button(titulo, use_container_width=True):
                st.session_state["pergunta_clicada"] = pergunta

    with col_chat:
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Olá, astronauta! Sou a Cosmo. Estou conectada aos protocolos da NASA para auxiliar na sua rotina de saúde, exercícios e hidratação. Como posso ajudar hoje?",
                    "fontes": [],
                }
            ]

        # Renderizar mensagens anteriores
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg.get("fontes"):
                    with st.expander("📚 Fontes consultadas no protocolo (RAG)"):
                        for idx, f in enumerate(msg["fontes"], 1):
                            st.markdown(f"**[{idx}] `{f.get('fonte')}`** (similaridade: {f.get('similaridade')})")
                            st.caption(f.get("trecho"))

        # Input do usuário
        prompt_input = st.chat_input("Faça uma pergunta sobre protocolos de saúde espacial...")
        pergunta_para_enviar = prompt_input or st.session_state.pop("pergunta_clicada", None)

        if pergunta_para_enviar:
            st.session_state.messages.append({"role": "user", "content": pergunta_para_enviar})
            with st.chat_message("user"):
                st.write(pergunta_para_enviar)

            with st.chat_message("assistant"):
                with st.spinner("Cosmo consultando os protocolos locais..."):
                    resposta_dict = ia.chat_cosmo(
                        mensagem=pergunta_para_enviar,
                        tema=tema_filtro,
                        consentimento_saude_mental=consentimento_mental,
                        k=k_trechos,
                        api_key=chave_ativa,
                    )
                    texto_resposta = resposta_dict.get("resposta", "Não consegui gerar uma resposta.")
                    fontes = resposta_dict.get("fontes", [])

                    st.write(texto_resposta)
                    if fontes:
                        with st.expander("📚 Fontes consultadas no protocolo (RAG)"):
                            for idx, f in enumerate(fontes, 1):
                                st.markdown(f"**[{idx}] `{f.get('fonte')}`** (similaridade: {f.get('similaridade')})")
                                st.caption(f.get("trecho"))

            st.session_state.messages.append(
                {"role": "assistant", "content": texto_resposta, "fontes": fontes}
            )

# --------------------------------------------------------------------------- TAB 2: Decisão Preventiva
with tab_decisao:
    st.markdown("### 🔍 Validação do Motor de Decisão e Sugestão Preventiva")
    st.write(
        "De acordo com a **ADR-002**, o LLM **nunca toma a decisão médica sozinho**. "
        "O motor determinístico detecta a tendência de piora e gera os alertas com níveis de autonomia (ADR-003) "
        "e humano responsável (ADR-004). A Cosmo apenas busca a orientação correspondente e sintetiza a explicação."
    )

    col_d1, col_d2 = st.columns([1, 2])

    with col_d1:
        st.markdown("#### Cenário Simulado")
        st.caption("Últimos 7 dias de um astronauta na missão:")
        cenario = st.radio(
            "Selecione um caso de teste:",
            [
                "Cenário A: Sono < 6h + Desidratação + FC subindo",
                "Cenário B: Rotina 100% saudável",
                "Cenário C: Humor baixo persistente (Saúde Mental)",
            ],
        )

        executar_decisao = st.button("Executar Avaliação Preventiva", type="primary", use_container_width=True)

    with col_d2:
        if executar_decisao or "ultimo_resultado_decisao" in st.session_state:
            if executar_decisao:
                if "Cenário A" in cenario:
                    dias_teste = [
                        {"data": "2026-11-09", "sono_h": 7.2, "agua_ml": 2400, "exercicio_min": 60, "fc_repouso": 58},
                        {"data": "2026-11-10", "sono_h": 7.0, "agua_ml": 2300, "exercicio_min": 60, "fc_repouso": 59},
                        {"data": "2026-11-11", "sono_h": 5.4, "agua_ml": 1800, "exercicio_min": 40, "fc_repouso": 66},
                        {"data": "2026-11-12", "sono_h": 5.2, "agua_ml": 1700, "exercicio_min": 30, "fc_repouso": 68},
                        {"data": "2026-11-13", "sono_h": 5.1, "agua_ml": 1650, "exercicio_min": 25, "fc_repouso": 69},
                    ]
                elif "Cenário B" in cenario:
                    dias_teste = [
                        {"data": f"2026-11-0{i}", "sono_h": 7.5, "agua_ml": 2500, "exercicio_min": 65, "fc_repouso": 58}
                        for i in range(1, 6)
                    ]
                else:
                    dias_teste = [
                        {"data": f"2026-11-0{i}", "sono_h": 7.0, "agua_ml": 2400, "exercicio_min": 60, "humor": 2}
                        for i in range(1, 5)
                    ]

                with st.spinner("Motor avaliando regras determinísticas e consultando RAG..."):
                    resultado = ia.avaliar_prevencao(
                        dias=dias_teste,
                        consentimento_saude_mental=consentimento_mental,
                        usar_rag=True,
                        explicar=True,
                    )
                    st.session_state["ultimo_resultado_decisao"] = resultado

            resultado = st.session_state["ultimo_resultado_decisao"]
            st.markdown(f"#### Alertas Gerados ({resultado.get('total_alertas')} detectados)")

            if resultado.get("total_alertas") == 0:
                st.success("✅ Nenhum alerta de tendência de piora detectado. Tripulante dentro dos padrões normais de missão.")
            else:
                for a in resultado.get("alertas", []):
                    badge_color = "red" if a.get("nivel") == "alerta" else "orange"
                    st.markdown(
                        f"""
                        <div class="alert-card">
                            <span style="background:{badge_color}; color:white; padding:3px 8px; border-radius:4px; font-size:0.75rem; font-weight:700;">
                                {a.get('nivel').upper()}
                            </span>
                            <b style="font-size:1.1rem; margin-left:8px;">{a.get('titulo')}</b>
                            <p style="margin: 6px 0 4px 0; color:#e2e8f0;"><b>Evidência clínica:</b> {a.get('evidencia')}</p>
                            <p style="margin:0; font-size:0.85rem; color:#a0aec0;">
                                👤 <b>Humano Responsável:</b> {a.get('responsavel')} | 
                                🔒 <b>Autonomia:</b> Nível {a.get('autonomia')} (Sugerir - ADR-003) | 
                                📡 <b>Terra:</b> {'Permitido' if a.get('compartilhavel_com_terra') else 'Bloqueado no relógio (ADR-007)'}
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if a.get("explicacao"):
                        st.info(f"🤖 **Explicação da Cosmo:** {a.get('explicacao')}")
                    if a.get("orientacao"):
                        with st.expander("📚 Protocolos de suporte recomendados (RAG)"):
                            for o in a.get("orientacao", []):
                                st.caption(f"**[{o.get('fonte')}]** {o.get('trecho')}")

