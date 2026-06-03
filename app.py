import streamlit as st
import pandas as pd
import numpy as np
import datetime
from utils.data_processing import (
    tratar_planilha,
    calcular_indicadores,
    obter_tabela_responsaveis,
    comparar_frequencias,
    montar_comparativo_indicadores,
    calcular_variacao_percentual
)
from utils.ui_components import render_header, metric_card, highlight_block, comparative_metric_card
from utils.charts import (
    plot_donut_chart,
    plot_horizontal_bar,
    plot_grouped_bar_comparison,
    plot_grouped_status_comparison,
    plot_stacked_bar_status,
    plot_simple_vertical_bar,
    plot_historical_line,
    plot_historical_bar,
    COLOR_MAP_SLA,
    COLOR_MAP_72H,
    COLOR_MAP_FCR
)
from utils.comparison import (
    detectar_mes_arquivo,
    gerar_label_mes,
    gerar_periodo_ordem,
    gerar_resumo_executivo
)
from utils.export_excel import gerar_excel_resultado

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Dashboard Executivo de Chamados",
    page_icon="📊",
    layout="wide",
)

# Constantes de ordenação
ORDEM_SLA = ["Dentro do SLA", "Fora do SLA", "SLA não informado", "Em aberto / Em tratamento"]
ORDEM_72H = ["Tratado até 72h", "Tratado acima de 72h", "72h não informado", "Em aberto / Em tratamento"]

@st.cache_data
def carregar_e_tratar_base(uploaded_file, nome_base):
    return tratar_planilha(uploaded_file, nome_base)


# =========================
# BARRA LATERAL (UPLOADER E FILTROS GLOBAIS)
# =========================
st.sidebar.image("https://img.icons8.com/color/96/000000/dashboard.png", width=80)
st.sidebar.title("Painel de Controle")

arquivo_atual = st.sidebar.file_uploader(
    "1. Planilha do Mês Atual (Obrigatório)",
    type=["xls", "xlsx", "xlsm", "csv"],
)

if not arquivo_atual:
    render_header("📊 Dashboard Executivo de Chamados", "Envie o arquivo do Mês Atual para começar")
    st.info("👋 **Bem-vindo!** Para gerar os dashboards executivos estilo Power BI, faça o upload da planilha do mês atual no menu lateral.")
    st.markdown("""
    ---
    ### 📂 Como rodar e preparar seus arquivos:
    1. **Upload da Base Atual:** Carregue a planilha mensal principal. O sistema reconhece automaticamente arquivos `.xls`, `.xlsx`, `.xlsm` e `.csv`.
    2. **Filtros Globais:** Após carregar a base atual, utilize os filtros de Cliente, Categoria, Responsável e Período de abertura para refinar a análise de todo o dashboard.
    3. **Aba Comparação:** Carregue a planilha do mês anterior dentro da Aba 2 para ver deltas percentuais, gráficos lado a lado e análise de insights escrita automaticamente por IA.
    4. **Controle de Responsáveis:** Veja quem são os analistas líderes de volume e produtividade de SLA (filtrados para um mínimo de 5 chamados finalizados).
    5. **Exportação:** Baixe a planilha Excel consolidada e tratada de forma consistente na Aba de Base Analítica.
    """)
    st.stop()

# Carregar base atual
try:
    df_atual_clean, colunas_atual = carregar_e_tratar_base(arquivo_atual, "Mês atual")
except Exception as e:
    st.sidebar.error("Erro ao processar Mês Atual.")
    st.error(f"❌ **Falha ao ler os dados da planilha do Mês Atual:** {str(e)}")
    st.stop()

# Seleção/Confirmação manual de Mês e Ano para a Base Atual
list_meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
list_anos = list(range(2020, 2031))

mes_det_at, ano_det_at = detectar_mes_arquivo(arquivo_atual.name)
st.sidebar.markdown("#### Confirmar Mês Atual")
col_sidebar_m, col_sidebar_a = st.sidebar.columns(2)
with col_sidebar_m:
    mes_idx_at = (mes_det_at - 1) if (mes_det_at and 1 <= mes_det_at <= 12) else 0
    mes_sel_at = st.selectbox("Mês", options=list_meses, index=mes_idx_at, key="sidebar_mes_atual")
with col_sidebar_a:
    ano_idx_at = list_anos.index(ano_det_at) if (ano_det_at and ano_det_at in list_anos) else list_anos.index(datetime.date.today().year)
    ano_sel_at = st.selectbox("Ano", options=list_anos, index=ano_idx_at, key="sidebar_ano_atual")

label_mes_atual = gerar_label_mes(mes_sel_at, ano_sel_at)

# Extrair opções para os filtros a partir da base limpa única
clientes_opcoes = sorted([x for x in df_atual_clean["Cliente Análise"].dropna().unique() if x != "Não informado"])
categorias_opcoes = sorted([x for x in df_atual_clean["Categoria Principal"].dropna().unique() if x != "Não informado"])
solicitacoes_opcoes = sorted([x for x in df_atual_clean["Solicitação Específica"].dropna().unique() if x != "Não informado"])
responsaveis_opcoes = sorted([x for x in df_atual_clean["Responsável Análise"].dropna().unique() if x != "Não informado"])
status_sla_opcoes = sorted(df_atual_clean["Status SLA"].dropna().unique().tolist())
status_72h_opcoes = sorted(df_atual_clean["Status 72h"].dropna().unique().tolist())

# Construir os filtros na Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filtros Globais")

clientes_sel = st.sidebar.multiselect("Clientes / Empresas", options=["Não informado"] + clientes_opcoes, placeholder="Todos")
categorias_sel = st.sidebar.multiselect("Categorias Principais", options=["Não informado"] + categorias_opcoes, placeholder="Todas")
solicitacoes_sel = st.sidebar.multiselect("Solicitações Específicas", options=["Não informado"] + solicitacoes_opcoes, placeholder="Todas")
responsaveis_sel = st.sidebar.multiselect("Responsáveis / Finalizadores", options=["Não informado"] + responsaveis_opcoes, placeholder="Todos")
status_sla_sel = st.sidebar.multiselect("Status SLA", options=status_sla_opcoes, placeholder="Todos")
status_72h_sel = st.sidebar.multiselect("Status 72h", options=status_72h_opcoes, placeholder="Todos")

# Slider de data de abertura
col_abert = colunas_atual["col_abertura"]
min_data = df_atual_clean[col_abert].dropna().min()
max_data = df_atual_clean[col_abert].dropna().max()

if pd.isna(min_data) or pd.isna(max_data):
    min_date_val = datetime.date.today()
    max_date_val = datetime.date.today()
else:
    min_date_val = min_data.to_pydatetime().date()
    max_date_val = max_data.to_pydatetime().date()

if min_date_val == max_date_val:
    data_inicio, data_fim = min_date_val, max_date_val
else:
    dates = st.sidebar.date_input(
        "Período de Abertura",
        value=[min_date_val, max_date_val],
        min_value=min_date_val,
        max_value=max_date_val
    )
    if isinstance(dates, list) or isinstance(dates, tuple):
        if len(dates) == 2:
            data_inicio, data_fim = dates[0], dates[1]
        elif len(dates) == 1:
            data_inicio, data_fim = dates[0], dates[0]
        else:
            data_inicio, data_fim = min_date_val, max_date_val
    else:
        data_inicio, data_fim = dates, dates

st.sidebar.markdown("---")
aplicar_anterior_sel = st.sidebar.radio(
    "Aplicar filtros globais também ao mês anterior/histórico?",
    ["Sim", "Não"],
    index=0
)
aplicar_anterior = (aplicar_anterior_sel == "Sim")


# =========================
# APLICAÇÃO DOS FILTROS GLOBAIS
# =========================
def aplicar_filtros_globais(df, col_abertura, ignorar_datas=False):
    df_filt = df.copy()
    if df_filt.empty:
        return df_filt
        
    if clientes_sel:
        df_filt = df_filt[df_filt["Cliente Análise"].isin(clientes_sel)]
    if categorias_sel:
        df_filt = df_filt[df_filt["Categoria Principal"].isin(categorias_sel)]
    if solicitacoes_sel:
        df_filt = df_filt[df_filt["Solicitação Específica"].isin(solicitacoes_sel)]
    if responsaveis_sel:
        df_filt = df_filt[df_filt["Responsável Análise"].isin(responsaveis_sel)]
    if status_sla_sel:
        df_filt = df_filt[df_filt["Status SLA"].isin(status_sla_sel)]
    if status_72h_sel:
        df_filt = df_filt[df_filt["Status 72h"].isin(status_72h_sel)]
        
    if not ignorar_datas:
        if col_abertura and col_abertura in df_filt.columns:
            col_dt = pd.to_datetime(df_filt[col_abertura])
            df_filt = df_filt[col_dt.notna() & (col_dt.dt.date >= data_inicio) & (col_dt.dt.date <= data_fim)]
        
    return df_filt



# Obter base filtrada única do mês atual
df_atual_filtered = aplicar_filtros_globais(df_atual_clean, colunas_atual["col_abertura"])

# Calcular resumos e indicadores da base atual filtrada
ind_atual = calcular_indicadores(df_atual_filtered)
df_resp_atual = obter_tabela_responsaveis(df_atual_filtered)

# Tabelas de frequência da base filtrada atual
resumo_clientes_atual = df_atual_filtered.groupby("Cliente Análise").size().reset_index(name="Chamados").rename(columns={"Cliente Análise": "Cliente"}).sort_values("Chamados", ascending=False)
resumo_categorias_atual = df_atual_filtered.groupby("Categoria Principal").size().reset_index(name="Chamados").sort_values("Chamados", ascending=False)
resumo_solicitacoes_atual = df_atual_filtered.groupby("Solicitação Específica").size().reset_index(name="Chamados").sort_values("Chamados", ascending=False)
resumo_sla_atual = df_atual_filtered["Status SLA"].value_counts().reindex(ORDEM_SLA, fill_value=0).reset_index(name="Chamados")
resumo_72h_atual = df_atual_filtered["Status 72h"].value_counts().reindex(ORDEM_72H, fill_value=0).reset_index(name="Chamados")


# =========================
# CABEÇALHO DA INTERFACE
# =========================
periodo_texto = f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
render_header("📊 Dashboard Executivo de Chamados", f"Mês de Referência: {label_mes_atual}", periodo_texto)


# =========================
# GERENCIAMENTO DE ABAS
# =========================
tab_visao, tab_comp, tab_resp, tab_cli, tab_qual, tab_base = st.tabs([
    "Visão Executiva",
    "Comparação Mensal",
    "Atendimento por Responsável",
    "Clientes e Categorias",
    "Qualidade da Base",
    "Base Analítica"
])


# ---------------------------------------------
# ABA 1: VISÃO EXECUTIVA
# ---------------------------------------------
with tab_visao:
    st.markdown("### 🗝️ Indicadores Chave de Desempenho (KPIs)")
    
    # Grid de cartões KPI personalizados
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total de Chamados", f"{ind_atual['total_chamados']:,}".replace(",", "."), card_type="blue")
    with c2:
        metric_card("Empresas com Chamados", f"{ind_atual['total_empresas']:,}", card_type="blue")
    with c3:
        metric_card("SLA Tratado", f"{ind_atual['sla_tratado']:,}", card_type="blue")
    with c4:
        pct_sla = ind_atual["percentual_dentro_sla"]
        card_t = "green" if pct_sla >= 90 else ("red" if pct_sla < 80 else "orange")
        metric_card("% Dentro do SLA", f"{pct_sla:.1f}%", card_type=card_t)

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        metric_card("Dentro do SLA", f"{ind_atual['dentro_sla']:,}", card_type="green")
    with c6:
        metric_card("Fora do SLA", f"{ind_atual['fora_sla']:,}", card_type="red")
    with c7:
        metric_card("SLA Não Informado", f"{ind_atual['sla_nao_informado']:,}", card_type="blue")
    with c8:
        metric_card("Em Aberto / Em Tratamento", f"{ind_atual['em_aberto']:,}", card_type="orange")

    fcr_exist = (ind_atual.get("fcr_tratado", 0) > 0)
    if fcr_exist:
        c9, c10, c11, c12 = st.columns(4)
    else:
        c9, c10, c11 = st.columns(3)
        
    with c9:
        metric_card("Tratados até 72h", f"{ind_atual['ate_72h']:,}", card_type="green")
    with c10:
        metric_card("Tratados acima de 72h", f"{ind_atual['acima_72h']:,}", card_type="red")
    with c11:
        metric_card("72h Não Informado", f"{ind_atual['nao_informado_72h']:,}", card_type="blue")
    if fcr_exist:
        with c12:
            metric_card("% FCR (1 Hora)", f"{ind_atual['percentual_fcr_1h']:.1f}%", card_type="blue")

    # Blocos de Destaque
    st.markdown("---")
    st.markdown("### 🏆 Líderes de Volume e Recorrência")
    h1, h2, h3 = st.columns(3)
    
    total_ch = ind_atual["total_chamados"]
    with h1:
        pct_cli = (ind_atual["cliente_top_qtd"] / total_ch * 100) if total_ch > 0 else 0
        highlight_block("Cliente Líder de Volume", ind_atual["cliente_top"], ind_atual["cliente_top_qtd"], pct_cli, "blue")
    with h2:
        pct_cat = (ind_atual["categoria_top_qtd"] / total_ch * 100) if total_ch > 0 else 0
        highlight_block("Categoria Principal Líder", ind_atual["categoria_top"], ind_atual["categoria_top_qtd"], pct_cat, "blue")
    with h3:
        pct_sol = (ind_atual["solicitacao_top_qtd"] / total_ch * 100) if total_ch > 0 else 0
        highlight_block("Solicitação Mais Recorrente", ind_atual["solicitacao_top"], ind_atual["solicitacao_top_qtd"], pct_sol, "blue")

    # Gráficos da aba executiva
    st.markdown("---")
    st.markdown("### 📊 Visão Gráfica Operacional")
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(plot_donut_chart(df_atual_filtered, "Status SLA", "Distribuição por Status SLA", COLOR_MAP_SLA), use_container_width=True)
    with g2:
        st.plotly_chart(plot_donut_chart(df_atual_filtered, "Status 72h", "Distribuição por Tempo de Tratamento (72h)", COLOR_MAP_72H), use_container_width=True)

    st.markdown("---")
    st.plotly_chart(plot_horizontal_bar(df_atual_filtered, "Cliente Análise", "Top 10 Clientes por Volume de Chamados", 10, "#1F4E78"), use_container_width=True)
    
    g3, g4 = st.columns(2)
    with g3:
        st.plotly_chart(plot_horizontal_bar(df_atual_filtered, "Categoria Principal", "Top 10 Categorias Principais", 10, "#2F5597"), use_container_width=True)
    with g4:
        st.plotly_chart(plot_horizontal_bar(df_atual_filtered, "Solicitação Específica", "Top 10 Solicitações Específicas", 10, "#8FAADC"), use_container_width=True)


# ---------------------------------------------
# ABA 2: COMPARAÇÃO MENSAL
# ---------------------------------------------
with tab_comp:
    # Seleção da subvisão
    opcao_comp = st.radio(
        "Selecione o tipo de análise comparativa:",
        ["Comparação de 2 Meses", "Histórico Multimensal / Auditoria Mensal"],
        horizontal=True,
        key="comp_sub_tab_select"
    )

    if opcao_comp == "Comparação de 2 Meses":
        st.markdown("### ⚖️ Comparação Direta de Desempenho (Mês de Análise x Mês de Comparação)")
        st.write("Faça o upload da planilha do mês anterior para habilitar a comparação.")
        
        arquivo_anterior = st.file_uploader(
            "2. Planilha do Mês de Comparação (Opcional)",
            type=["xls", "xlsx", "xlsm", "csv"],
            key="uploader_anterior_aba",
        )

        if not arquivo_anterior:
            st.info("ℹ️ **Aguardando base comparativa.** Faça o upload da planilha de comparação acima para liberar a análise executiva.")
        else:
            try:
                df_anterior_clean, colunas_anterior = carregar_e_tratar_base(arquivo_anterior, "Mês anterior")
                st.success("Planilha do Mês Anterior carregada com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro ao ler a base do Mês Anterior: {str(e)}")
                st.stop()

            # Confirmar o Mês/Ano do arquivo anterior
            mes_det_ant, ano_det_ant = detectar_mes_arquivo(arquivo_anterior.name)
            st.markdown("#### Confirmar Mês Anterior")
            col_m_ant, col_a_ant = st.columns(2)
            with col_m_ant:
                mes_idx_ant = (mes_det_ant - 1) if (mes_det_ant and 1 <= mes_det_ant <= 12) else 0
                mes_sel_ant = st.selectbox("Mês", options=list_meses, index=mes_idx_ant, key="comp_mes_anterior")
            with col_a_ant:
                ano_idx_ant = list_anos.index(ano_det_ant) if (ano_det_ant and ano_det_ant in list_anos) else list_anos.index(datetime.date.today().year)
                ano_sel_ant = st.selectbox("Ano", options=list_anos, index=ano_idx_ant, key="comp_ano_anterior")

            label_mes_anterior = gerar_label_mes(mes_sel_ant, ano_sel_ant)

            df_atual_bruto = df_atual_clean
            df_atual_filtrado = df_atual_filtered
            df_anterior_bruto = df_anterior_clean
            
            # A base anterior usada na comparação ignora o filtro de período de abertura do mês atual
            if aplicar_anterior:
                df_anterior_usado_na_comparacao = aplicar_filtros_globais(df_anterior_bruto, colunas_anterior["col_abertura"], ignorar_datas=True)
            else:
                df_anterior_usado_na_comparacao = df_anterior_bruto

            df_anterior_filtrado = df_anterior_usado_na_comparacao
            df_anterior_filtered = df_anterior_filtrado

            ind_anterior = calcular_indicadores(df_anterior_filtered)

            # Salvar no session_state para que a aba 6 (download) e outras visualizações usem
            st.session_state["resultado_anterior"] = {
                "df": df_anterior_filtered,
                "indicadores": ind_anterior,
                "resumo_sla": df_anterior_filtered["Status SLA"].value_counts().reindex(ORDEM_SLA, fill_value=0).reset_index(name="Chamados"),
                "resumo_72h": df_anterior_filtered["Status 72h"].value_counts().reindex(ORDEM_72H, fill_value=0).reset_index(name="Chamados"),
                "resumo_fcr_1h": df_anterior_filtered["Status FCR 1h"].value_counts().reindex(["Resolvido até 1h", "Resolvido acima de 1h", "FCR não informado", "Em aberto / Em tratamento"], fill_value=0).reset_index(name="Chamados")
            }
            st.session_state["label_mes_anterior"] = label_mes_anterior
            st.session_state["arquivo_anterior_nome"] = arquivo_anterior.name

            # AVISO DE RECORTE SE FILTROS ATIVOS
            filtros_ativos = bool(
                clientes_sel or categorias_sel or solicitacoes_sel or 
                responsaveis_sel or status_sla_sel or status_72h_sel or
                (data_inicio != min_date_val or data_fim != max_date_val)
            )
            label_linhas = "linhas após filtros" if filtros_ativos else "linhas utilizadas na comparação"

            # -------------------
            # CABEÇALHO EXECUTIVO
            # -------------------
            st.markdown(f"""
            <div style="background-color: #F8FAFC; padding: 24px; border-radius: 8px; border-left: 5px solid #1F4E78; margin-bottom: 20px; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05); border-top: 1px solid #E2E8F0; border-right: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0;">
                <h3 style="margin-top: 0; color: #1F4E78; font-size: 20px; font-weight: 700; margin-bottom: 16px; font-family: 'Segoe UI', sans-serif;">⚖️ Comparação em Análise: {label_mes_anterior} x {label_mes_atual}</h3>
                <div style="display: flex; gap: 32px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 250px; background-color: #FFFFFF; padding: 16px; border-radius: 6px; border: 1px solid #E2E8F0;">
                        <h4 style="margin-top: 0; color: #475569; font-size: 14px; font-weight: 600; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">Mês Anterior ({label_mes_anterior})</h4>
                        <div style="font-size: 13px; color: #64748B; margin-bottom: 4px;"><strong>Arquivo:</strong> <span style="font-family: monospace;">{arquivo_anterior.name}</span></div>
                        <div style="font-size: 13px; color: #64748B; margin-bottom: 4px;"><strong>Mês selecionado:</strong> {label_mes_anterior}</div>
                        <div style="font-size: 13px; color: #64748B; margin-bottom: 4px;"><strong>{label_mes_anterior} linhas brutas:</strong> {len(df_anterior_clean):,}</div>
                        <div style="font-size: 13px; color: #64748B;"><strong>{label_mes_anterior} {label_linhas}:</strong> {len(df_anterior_filtered):,}</div>
                    </div>
                    <div style="flex: 1; min-width: 250px; background-color: #FFFFFF; padding: 16px; border-radius: 6px; border: 1px solid #E2E8F0;">
                        <h4 style="margin-top: 0; color: #1F4E78; font-size: 14px; font-weight: 600; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">Mês Atual ({label_mes_atual})</h4>
                        <div style="font-size: 13px; color: #64748B; margin-bottom: 4px;"><strong>Arquivo:</strong> <span style="font-family: monospace;">{arquivo_atual.name}</span></div>
                        <div style="font-size: 13px; color: #64748B; margin-bottom: 4px;"><strong>Mês selecionado:</strong> {label_mes_atual}</div>
                        <div style="font-size: 13px; color: #64748B; margin-bottom: 4px;"><strong>{label_mes_atual} linhas brutas:</strong> {len(df_atual_clean):,}</div>
                        <div style="font-size: 13px; color: #64748B;"><strong>{label_mes_atual} {label_linhas}:</strong> {len(df_atual_filtered):,}</div>
                    </div>
                </div>
                <div style="margin-top: 16px; font-size: 11px; color: #94A3B8;">
                    <strong>Data/Hora de processamento:</strong> {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if filtros_ativos:
                st.warning("⚠️ **Atenção: comparação exibida com filtros aplicados. Os números representam um recorte da base.**")
                st.markdown(f"""
                * **Base atual:** {len(df_atual_filtered)} de {len(df_atual_clean)} chamados
                * **Base anterior:** {len(df_anterior_filtered)} de {len(df_anterior_clean)} chamados
                """)

            # -------------------
            # DELTAS E CARDS COMPARATIVOS
            # -------------------
            st.markdown("### 🗝️ Deltas Comparativos Executivos")

            diff_total = ind_atual["total_chamados"] - ind_anterior["total_chamados"]
            pct_total = calcular_variacao_percentual(ind_atual["total_chamados"], ind_anterior["total_chamados"])
            
            diff_dentro = ind_atual["dentro_sla"] - ind_anterior["dentro_sla"]
            pct_dentro = calcular_variacao_percentual(ind_atual["dentro_sla"], ind_anterior["dentro_sla"])
            
            diff_fora = ind_atual["fora_sla"] - ind_anterior["fora_sla"]
            pct_fora = calcular_variacao_percentual(ind_atual["fora_sla"], ind_anterior["fora_sla"])
            
            diff_sla_pct = ind_atual["percentual_dentro_sla"] - ind_anterior["percentual_dentro_sla"]
            
            diff_72h = ind_atual["ate_72h"] - ind_anterior["ate_72h"]
            pct_72h = calcular_variacao_percentual(ind_atual["ate_72h"], ind_anterior["ate_72h"])
            
            diff_acima = ind_atual["acima_72h"] - ind_anterior["acima_72h"]
            pct_acima = calcular_variacao_percentual(ind_atual["acima_72h"], ind_anterior["acima_72h"])
            
            diff_abertos = ind_atual["em_aberto"] - ind_anterior["em_aberto"]
            pct_abertos = calcular_variacao_percentual(ind_atual["em_aberto"], ind_anterior["em_aberto"])
            
            diff_emp = ind_atual["total_empresas"] - ind_anterior["total_empresas"]
            pct_emp = calcular_variacao_percentual(ind_atual["total_empresas"], ind_anterior["total_empresas"])
            
            diff_fcr = ind_atual["fcr_1h"] - ind_anterior["fcr_1h"]
            pct_fcr = calcular_variacao_percentual(ind_atual["fcr_1h"], ind_anterior["fcr_1h"])
            
            diff_fcr_pct = ind_atual["percentual_fcr_1h"] - ind_anterior["percentual_fcr_1h"]

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                comparative_metric_card(
                    "Total de Chamados",
                    label_mes_atual, ind_atual["total_chamados"],
                    label_mes_anterior, ind_anterior["total_chamados"],
                    diff_total, pct_total,
                    "total"
                )
            with c2:
                comparative_metric_card(
                    "Dentro do SLA",
                    label_mes_atual, ind_atual["dentro_sla"],
                    label_mes_anterior, ind_anterior["dentro_sla"],
                    diff_dentro, pct_dentro,
                    "positive"
                )
            with c3:
                comparative_metric_card(
                    "Fora do SLA",
                    label_mes_atual, ind_atual["fora_sla"],
                    label_mes_anterior, ind_anterior["fora_sla"],
                    diff_fora, pct_fora,
                    "negative"
                )
            with c4:
                comparative_metric_card(
                    "% SLA Dentro",
                    label_mes_atual, ind_atual["percentual_dentro_sla"],
                    label_mes_anterior, ind_anterior["percentual_dentro_sla"],
                    diff_sla_pct, None,
                    "positive"
                )

            c5, c6, c7, c8 = st.columns(4)
            with c5:
                comparative_metric_card(
                    "Tratados até 72h",
                    label_mes_atual, ind_atual["ate_72h"],
                    label_mes_anterior, ind_anterior["ate_72h"],
                    diff_72h, pct_72h,
                    "positive"
                )
            with c6:
                comparative_metric_card(
                    "Tratados acima de 72h",
                    label_mes_atual, ind_atual["acima_72h"],
                    label_mes_anterior, ind_anterior["acima_72h"],
                    diff_acima, pct_acima,
                    "negative"
                )
            with c7:
                comparative_metric_card(
                    "Em Aberto / Em Tratamento",
                    label_mes_atual, ind_atual["em_aberto"],
                    label_mes_anterior, ind_anterior["em_aberto"],
                    diff_abertos, pct_abertos,
                    "negative"
                )
            with c8:
                comparative_metric_card(
                    "Clientes/Empresas",
                    label_mes_atual, ind_atual["total_empresas"],
                    label_mes_anterior, ind_anterior["total_empresas"],
                    diff_emp, pct_emp,
                    "total"
                )

            # Se FCR 1h estiver disponível, exibir cartões de FCR
            if ind_atual["fcr_tratado"] > 0 or ind_anterior["fcr_tratado"] > 0:
                c9, c10 = st.columns(2)
                with c9:
                    comparative_metric_card(
                        "FCR até 1h",
                        label_mes_atual, ind_atual["fcr_1h"],
                        label_mes_anterior, ind_anterior["fcr_1h"],
                        diff_fcr, pct_fcr,
                        "positive"
                    )
                with c10:
                    comparative_metric_card(
                        "% FCR até 1h",
                        label_mes_atual, ind_atual["percentual_fcr_1h"],
                        label_mes_anterior, ind_anterior["percentual_fcr_1h"],
                        diff_fcr_pct, None,
                        "positive"
                    )

            # -------------------
            # RESUMO EXECUTIVO E TEXTO DE EVOLUÇÃO
            # -------------------
            comp_cat = comparar_frequencias(df_atual_filtered, df_anterior_filtered, "Categoria Principal", "Categoria Principal")
            comp_cli = comparar_frequencias(df_atual_filtered, df_anterior_filtered, "Cliente Análise", "Cliente")
            comp_sol = comparar_frequencias(df_atual_filtered, df_anterior_filtered, "Solicitação Específica", "Solicitação Específica")

            try:
                resumo_exec_texto, melhoras, pioras, atencoes = gerar_resumo_executivo(
                    ind_atual, ind_anterior, label_mes_atual, label_mes_anterior, comp_cat, comp_cli, comp_sol
                )
            except Exception as e:
                st.warning("⚠️ Não foi possível gerar a análise textual automática da evolução devido a dados inconsistentes ou insuficientes para este recorte.")
                resumo_exec_texto = "Não foi possível gerar o resumo executivo automaticamente para este recorte."
                melhoras = []
                pioras = []
                atencoes = ["Verifique os dados de comparação mensal e os percentuais calculados."]


            st.markdown("---")
            st.markdown("### 🧠 Resumo Executivo da Evolução")
            st.info(resumo_exec_texto)

            col_m, col_p, col_a = st.columns(3)
            with col_m:
                st.success("##### 🟢 Evoluções Positivas (Melhorou)")
                if melhoras:
                    for item in melhoras:
                        st.markdown(f"- {item}")
                else:
                    st.markdown("- Nenhuma alteração positiva registrada.")

            with col_p:
                st.error("##### 🔴 Pontos de Regressão (Piorou)")
                if pioras:
                    for item in pioras:
                        st.markdown(f"- {item}")
                else:
                    st.markdown("- Nenhuma regressão registrada.")

            with col_a:
                st.warning("##### ⚠️ Pontos de Atenção (Gestão)")
                if atencoes:
                    for item in atencoes:
                        st.markdown(f"- {item}")
                else:
                    st.markdown("- Nenhum ponto crítico de atenção reportado no período.")

            # -------------------
            # GRÁFICOS LADO A LADO COM NOME REAL DOS MESES
            # -------------------
            st.markdown("---")
            st.markdown("### 📊 Gráficos Comparativos de Status (Legendas Reais)")
            
            df_atual_status = df_atual_filtered[["Status SLA", "Status 72h"]].copy()
            df_atual_status["Mês"] = label_mes_atual
            df_anterior_status = df_anterior_filtered[["Status SLA", "Status 72h"]].copy()
            df_anterior_status["Mês"] = label_mes_anterior
            df_combined_status = pd.concat([df_atual_status, df_anterior_status], ignore_index=True)

            df_atual_fcr = df_atual_filtered[["Status FCR 1h"]].copy()
            df_atual_fcr["Mês"] = label_mes_atual
            df_anterior_fcr = df_anterior_filtered[["Status FCR 1h"]].copy()
            df_anterior_fcr["Mês"] = label_mes_anterior
            df_combined_fcr = pd.concat([df_atual_fcr, df_anterior_fcr], ignore_index=True)

            g1, g2 = st.columns(2)
            with g1:
                st.plotly_chart(
                    plot_grouped_status_comparison(
                        df_combined_status,
                        "Status SLA",
                        f"SLA: {label_mes_anterior} x {label_mes_atual}",
                        ORDEM_SLA,
                        COLOR_MAP_SLA,
                        label_mes_anterior,
                        label_mes_atual
                    ),
                    use_container_width=True
                )
            with g2:
                st.plotly_chart(
                    plot_grouped_status_comparison(
                        df_combined_status,
                        "Status 72h",
                        f"Tempo de Resolução (72h): {label_mes_anterior} x {label_mes_atual}",
                        ORDEM_72H,
                        COLOR_MAP_72H,
                        label_mes_anterior,
                        label_mes_atual
                    ),
                    use_container_width=True
                )

            # Mostrar FCR se houver dados
            if ind_atual["fcr_tratado"] > 0 or ind_anterior["fcr_tratado"] > 0:
                st.plotly_chart(
                    plot_grouped_status_comparison(
                        df_combined_fcr,
                        "Status FCR 1h",
                        f"First Call Resolution (FCR 1h): {label_mes_anterior} x {label_mes_atual}",
                        ["Resolvido até 1h", "Resolvido acima de 1h", "FCR não informado", "Em aberto / Em tratamento"],
                        COLOR_MAP_FCR,
                        label_mes_anterior,
                        label_mes_atual
                    ),
                    use_container_width=True
                )

            # Rankings agrupados
            st.markdown("---")
            st.markdown("### 📈 Rankings Comparativos")
            
            g3, g4 = st.columns(2)
            with g3:
                top_cats = comp_cat.head(10)
                top_cats_renamed = top_cats.rename(columns={"Mês anterior": label_mes_anterior, "Mês atual": label_mes_atual})
                top_cats_melt = top_cats_renamed.melt(id_vars="Categoria Principal", value_vars=[label_mes_anterior, label_mes_atual], var_name="Mês", value_name="Chamados")
                st.plotly_chart(
                    plot_grouped_bar_comparison(
                        top_cats_melt, "Categoria Principal", f"Top Categorias Principais: {label_mes_anterior} x {label_mes_atual}", label_mes_anterior, label_mes_atual
                    ),
                    use_container_width=True
                )
            with g4:
                top_clis = comp_cli.head(10)
                top_clis_renamed = top_clis.rename(columns={"Mês anterior": label_mes_anterior, "Mês atual": label_mes_atual})
                top_clis_melt = top_clis_renamed.melt(id_vars="Cliente", value_vars=[label_mes_anterior, label_mes_atual], var_name="Mês", value_name="Chamados")
                st.plotly_chart(
                    plot_grouped_bar_comparison(
                        top_clis_melt, "Cliente", f"Top Clientes: {label_mes_anterior} x {label_mes_atual}", label_mes_anterior, label_mes_atual
                    ),
                    use_container_width=True
                )

            top_sols = comp_sol.head(10)
            top_sols_renamed = top_sols.rename(columns={"Mês anterior": label_mes_anterior, "Mês atual": label_mes_atual})
            top_sols_melt = top_sols_renamed.melt(id_vars="Solicitação Específica", value_vars=[label_mes_anterior, label_mes_atual], var_name="Mês", value_name="Chamados")
            st.plotly_chart(
                plot_grouped_bar_comparison(
                    top_sols_melt, "Solicitação Específica", f"Top Solicitações Específicas: {label_mes_anterior} x {label_mes_atual}", label_mes_anterior, label_mes_atual, height=450
                ),
                use_container_width=True
            )

            # Tabelas comparativas detalhadas
            st.markdown("---")
            st.markdown("### 📋 Tabelas Analíticas de Variação Mensal")
            with st.expander("Ver Tabela Comparativa de Categorias Principais"):
                st.dataframe(comp_cat, use_container_width=True)
            with st.expander("Ver Tabela Comparativa de Clientes"):
                st.dataframe(comp_cli, use_container_width=True)
            with st.expander("Ver Tabela Comparativa de Solicitações Específicas"):
                st.dataframe(comp_sol, use_container_width=True)

    else:
        # ---------------------------------------------
        # HISTÓRICO MULTIMENSAL E MATRIZ DE AUDITORIA
        # ---------------------------------------------
        st.markdown("### 📅 Balanço e Auditoria Mensal (Histórico de até 12 meses)")
        st.write("Faça o upload de múltiplos arquivos mensais para consolidar o histórico da operação.")

        arquivos_hist = st.file_uploader(
            "Upload de múltiplos arquivos mensais",
            type=["xls", "xlsx", "xlsm", "csv"],
            accept_multiple_files=True,
            key="uploader_historico_multi"
        )

        if not arquivos_hist:
            st.info("ℹ️ **Aguardando arquivos.** Carregue dois ou mais arquivos simultaneamente para gerar a matriz histórica e gráficos de tendência.")
        else:
            st.markdown("#### 📆 Confirmação dos Períodos de Cada Arquivo")
            st.caption("Abaixo estão os períodos detectados automaticamente. Você pode corrigi-los manualmente se necessário:")
            
            sorted_months_info = []
            for idx, f in enumerate(arquivos_hist):
                mes_det, ano_det = detectar_mes_arquivo(f.name)
                with st.expander(f"📁 {f.name}", expanded=True):
                    col_det_name, col_m, col_a = st.columns([2, 1, 1])
                    col_det_name.write(f"Tamanho: `{f.size / 1024:.1f} KB`")
                    
                    with col_m:
                        mes_idx = (mes_det - 1) if (mes_det and 1 <= mes_det <= 12) else 0
                        mes_sel = st.selectbox("Mês", options=list_meses, index=mes_idx, key=f"hist_m_{idx}_{f.name}")
                    with col_a:
                        ano_idx = list_anos.index(ano_det) if (ano_det and ano_det in list_anos) else list_anos.index(datetime.date.today().year)
                        ano_sel = st.selectbox("Ano", options=list_anos, index=ano_idx, key=f"hist_a_{idx}_{f.name}")
                        
                    mes_num = list_meses.index(mes_sel) + 1
                    label = f"{mes_sel[:3]}/{ano_sel}"  # ex: "Mai/2026"
                    periodo_ordem = gerar_periodo_ordem(mes_sel, ano_sel)
                    
                    sorted_months_info.append({
                        "file": f,
                        "mes_num": mes_num,
                        "ano": ano_sel,
                        "label": label,
                        "periodo_ordem": periodo_ordem,
                        "sort_key": (ano_sel, mes_num)
                    })
            # Verificar duplicidade de período (Mês/Ano)
            labels_set = set()
            duplicates = []
            for item in sorted_months_info:
                lbl = item["label"]
                if lbl in labels_set:
                    duplicates.append(lbl)
                else:
                    labels_set.add(lbl)
            
            if duplicates:
                st.error(f"❌ **Erro de Duplicidade:** Foram detectados múltiplos arquivos marcados para o mesmo período: **{', '.join(set(duplicates))}**. Ajuste a confirmação de Mês/Ano de cada arquivo nos painéis acima para que não haja duplicatas.")
            else:
                # Ordenar cronologicamente
                sorted_months_info = sorted(sorted_months_info, key=lambda x: x["sort_key"])

                # Processar cada base
                historico_data = []
                matrix_dict = {}
                df_historico_bases = {}

                progress_bar = st.progress(0)
                for idx, item in enumerate(sorted_months_info):
                    label = item["label"]
                    f = item["file"]
                    
                    try:
                        df_m_clean, col_m = carregar_e_tratar_base(f, f"Histórico {label}")
                        # Filtrar se ativado
                        df_m_filtered = aplicar_filtros_globais(df_m_clean, col_m["col_abertura"], ignorar_datas=True) if aplicar_anterior else df_m_clean
                        
                        df_historico_bases[label] = df_m_filtered
                        ind_m = calcular_indicadores(df_m_filtered)
                        
                        historico_data.append({
                            "Período": label,
                            "Periodo Ordem": item["periodo_ordem"],
                            "Total de Chamados": ind_m["total_chamados"],
                            "Dentro do SLA": ind_m["dentro_sla"],
                            "Fora do SLA": ind_m["fora_sla"],
                            "% Dentro do SLA": ind_m["percentual_dentro_sla"],
                            "Tratados até 72h": ind_m["ate_72h"],
                            "Tratados acima de 72h": ind_m["acima_72h"],
                            "Em aberto / Em tratamento": ind_m["em_aberto"],
                            "SLA não informado": ind_m["sla_nao_informado"],
                            "FCR até 1h": ind_m["fcr_1h"],
                            "% FCR 1h": ind_m["percentual_fcr_1h"]
                        })
                        
                        matrix_dict[label] = {
                            "Total de chamados": ind_m["total_chamados"],
                            "Dentro do SLA": ind_m["dentro_sla"],
                            "Fora do SLA": ind_m["fora_sla"],
                            "% dentro do SLA": f"{ind_m['percentual_dentro_sla']:.1f}%",
                            "Tratados até 72h": ind_m["ate_72h"],
                            "Tratados acima de 72h": ind_m["acima_72h"],
                            "Em aberto / Em tratamento": ind_m["em_aberto"],
                            "SLA não informado": ind_m["sla_nao_informado"],
                            "FCR até 1h": ind_m["fcr_1h"],
                            "% FCR até 1h": f"{ind_m['percentual_fcr_1h']:.1f}%",
                            "Top Categoria": ind_m["categoria_top"],
                            "Top Cliente": ind_m["cliente_top"]
                        }
                    except Exception as ex:
                        st.error(f"Erro ao processar o arquivo {f.name}: {str(ex)}")
                    
                    progress_bar.progress((idx + 1) / len(sorted_months_info))
                progress_bar.empty()

                if historico_data:
                    df_historico_resumo = pd.DataFrame(historico_data)
                    df_matrix = pd.DataFrame(matrix_dict)

                    # Se FCR não estiver disponível no histórico, remover as linhas da Matriz de Auditoria
                    if df_historico_resumo["FCR até 1h"].sum() == 0:
                        df_matrix = df_matrix.drop(index=["FCR até 1h", "% FCR até 1h"], errors="ignore")

                    # Salvar no session_state para exportação Excel
                    st.session_state["df_matrix_historico"] = df_matrix
                    st.session_state["df_resumo_historico"] = df_historico_resumo
                    st.session_state["df_historico_bases"] = df_historico_bases

                if filtros_ativos:
                    st.warning("⚠️ **Atenção: esta comparação está com filtros aplicados. Os números representam um recorte da base, não o total geral dos meses.**")
                    st.markdown("* **Histórico:** recorte aplicado")

                # Mostrar Gráficos Históricos
                st.markdown("---")
                st.markdown("### 📈 Gráficos de Evolução Histórica")
                
                st.plotly_chart(plot_historical_line(df_historico_resumo, "Período", "Total de Chamados", "Volume Total de Chamados por Mês"), use_container_width=True)
                
                g_h_sla, g_h_72h = st.columns(2)
                with g_h_sla:
                    st.plotly_chart(plot_historical_line(df_historico_resumo, "Período", "% Dentro do SLA", "Evolução do SLA % por Mês", "percent"), use_container_width=True)
                with g_h_72h:
                    df_historico_resumo["% Tratado até 72h"] = (df_historico_resumo["Tratados até 72h"] / (df_historico_resumo["Tratados até 72h"] + df_historico_resumo["Tratados acima de 72h"]) * 100).fillna(0)
                    st.plotly_chart(plot_historical_line(df_historico_resumo, "Período", "% Tratado até 72h", "Evolução de Chamados Tratados em até 72h (%)", "percent"), use_container_width=True)

                g_h_fora, g_h_ab = st.columns(2)
                with g_h_fora:
                    st.plotly_chart(plot_historical_bar(df_historico_resumo, "Período", "Fora do SLA", "Chamados Fora do SLA por Mês", "#EF4444"), use_container_width=True)
                with g_h_ab:
                    st.plotly_chart(plot_historical_bar(df_historico_resumo, "Período", "Em aberto / Em tratamento", "Chamados em Aberto por Mês", "#F59E0B"), use_container_width=True)

                # Mostrar FCR se houver
                if df_historico_resumo["FCR até 1h"].sum() > 0:
                    st.plotly_chart(plot_historical_line(df_historico_resumo, "Período", "% FCR 1h", "Evolução do First Call Resolution (%)", "percent"), use_container_width=True)

                # Tabela Matriz de Auditoria
                st.markdown("---")
                st.markdown("### 📋 Tabela Matriz de Auditoria Mensal")
                st.dataframe(df_matrix, use_container_width=True)


# ---------------------------------------------
# ABA 3: ATENDIMENTO POR RESPONSÁVEL
# ---------------------------------------------
with tab_resp:
    st.markdown("### 👥 Produtividade e Qualidade por Responsável/Analista")
    
    if colunas_atual["is_responsavel_aproximado"]:
        st.warning(
            f"⚠️ **Aproximação Ativada:** Não foi localizada na planilha uma coluna explícita de encerramento "
            f"(como *Finalizado por*, *Encerrado por* ou *Atendente finalizador*). "
            f"Usando a coluna geral **'{colunas_atual['col_responsavel']}'** como aproximação para os indicadores."
        )
    else:
        st.success(f"✔️ **Indicadores Baseados em Fechamento:** Coluna oficial de finalizador detectada e utilizada: **'{colunas_atual['col_responsavel']}'**.")

    st.write("##### Métricas Consolidadas de Atendimento")
    st.dataframe(df_resp_atual, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📈 Análises Gráficas por Analista")
    
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(
            plot_stacked_bar_status(
                df_atual_filtered,
                "Responsável Análise",
                "Status SLA",
                "Distribuição de SLA por Analista (Top 10)",
                COLOR_MAP_SLA,
                10
            ),
            use_container_width=True
        )
    with g2:
        st.plotly_chart(
            plot_stacked_bar_status(
                df_atual_filtered,
                "Responsável Análise",
                "Status 72h",
                "Distribuição de 72h por Analista (Top 10)",
                COLOR_MAP_72H,
                10
            ),
            use_container_width=True
        )

    g3, g4 = st.columns(2)
    with g3:
        df_tempo = df_resp_atual[df_resp_atual["Finalizados"] > 0].copy()
        if not df_tempo.empty:
            st.plotly_chart(
                plot_simple_vertical_bar(
                    df_tempo.head(10),
                    "Responsável",
                    "Tempo Médio (Horas)",
                    "Tempo Médio de Atendimento em Horas (Top 10)"
                ),
                use_container_width=True
            )
        else:
            st.info("Nenhum chamado finalizado para calcular tempo médio.")
    with g4:
        st.plotly_chart(
            plot_simple_vertical_bar(
                df_resp_atual.head(10),
                "Responsável",
                "Atribuídos",
                "Volume de Chamados Atribuídos (Top 10)"
            ),
            use_container_width=True
        )

    # Ranking de qualidade (SLA %) - Exigência de pelo menos 5 chamados finalizados
    st.markdown("---")
    st.markdown("### 🏆 Top Performance de SLA (Qualidade)")
    st.caption("Considera apenas os profissionais com pelo menos 5 chamados finalizados para garantir relevância estatística.")
    
    df_rank_qualidade = df_resp_atual[df_resp_atual["Finalizados"] >= 5].copy()
    if df_rank_qualidade.empty:
        st.info("ℹ️ **Métricas insuficientes:** Nenhum analista atingiu o volume mínimo de 5 chamados finalizados neste período filtrado.")
    else:
        df_rank_qualidade = df_rank_qualidade.sort_values("% Dentro SLA", ascending=False)
        st.plotly_chart(
            plot_simple_vertical_bar(
                df_rank_qualidade.head(10),
                "Responsável",
                "% Dentro SLA",
                "Top Analistas por % Dentro do SLA (Mínimo 5 Finalizados)",
                color="#10B981"
            ),
            use_container_width=True
        )


# ---------------------------------------------
# ABA 4: CLIENTES E CATEGORIAS
# ---------------------------------------------
with tab_cli:
    st.markdown("### 🏢 Análise Detalhada de Clientes e Categorias de Serviços")
    
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        st.markdown("##### Ranking de Clientes com mais Chamados")
        st.dataframe(resumo_clientes_atual, use_container_width=True)
    with c_col2:
        st.markdown("##### Ranking das Categorias Principais")
        st.dataframe(resumo_categorias_atual, use_container_width=True)

    st.markdown("---")
    st.markdown("##### Ranking de Solicitações Específicas (Tipo + Item)")
    st.dataframe(resumo_solicitacoes_atual, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🔍 Análise de Gargalos e Causas Raiz")
    
    g_col1, g_col2 = st.columns(2)
    with g_col1:
        st.markdown("##### Principal Causa de SLA Vencido")
        df_vencidos = df_atual_filtered[df_atual_filtered["Status SLA"] == "Fora do SLA"]
        if df_vencidos.empty:
            st.success("🎉 **Excelente!** Nenhum chamado fora do SLA foi registrado no período selecionado.")
        else:
            st.plotly_chart(
                plot_horizontal_bar(
                    df_vencidos,
                    "Solicitação Específica",
                    "Top Ocorrências Fora do SLA por Solicitação Específica",
                    10,
                    "#EF4444"
                ),
                use_container_width=True
            )
            
    with g_col2:
        st.markdown("##### Principal Causa de Atraso Operacional (Acima de 72h)")
        df_atrasados = df_atual_filtered[df_atual_filtered["Status 72h"] == "Tratado acima de 72h"]
        if df_atrasados.empty:
            st.success("🎉 **Excelente!** Nenhum chamado ultrapassou 72 horas para encerramento no período.")
        else:
            st.plotly_chart(
                plot_horizontal_bar(
                    df_atrasados,
                    "Solicitação Específica",
                    "Top Ocorrências Atrasadas (>72h) por Solicitação Específica",
                    10,
                    "#F59E0B"
                ),
                use_container_width=True
            )


# ---------------------------------------------
# ABA 5: QUALIDADE DA BASE (AUDITORIA)
# ---------------------------------------------
with tab_qual:
    st.markdown("### 🔍 Qualidade dos Dados e Auditoria de Registros")
    st.write("Verifique a qualidade das informações importadas e a integridade dos cálculos do dashboard.")

    total_importados = len(df_atual_clean)
    
    col_emp = colunas_atual["col_empresa"]
    col_ab = colunas_atual["col_abertura"]
    col_enc = colunas_atual["col_encerramento"]
    col_ven = colunas_atual["col_vencimento"]

    # Contagens
    sem_cliente = int((df_atual_clean["Cliente Análise"] == "Não informado").sum())
    sem_abertura = int(df_atual_clean[col_ab].isna().sum())
    sem_encerramento = int(df_atual_clean[col_enc].isna().sum())
    sem_vencimento = int(df_atual_clean[col_ven].isna().sum()) if col_ven else total_importados
    sem_responsavel = int((df_atual_clean["Responsável Análise"] == "Não informado").sum())

    # Exibição em cards
    aq1, aq2, aq3 = st.columns(3)
    with aq1:
        metric_card("Total Importado (Raw)", f"{total_importados:,}".replace(",", "."), card_type="blue")
    with aq2:
        metric_card("Registros Sem Cliente", f"{sem_cliente:,}", card_type="orange" if sem_cliente > 0 else "green")
    with aq3:
        metric_card("Registros Sem Abertura", f"{sem_abertura:,}", card_type="red" if sem_abertura > 0 else "green")

    aq4, aq5, aq6 = st.columns(3)
    with aq4:
        metric_card("Registros Sem Encerramento", f"{sem_encerramento:,}", card_type="orange" if sem_encerramento > 0 else "green")
    with aq5:
        metric_card("Registros Sem Vencimento/SLA", f"{sem_vencimento:,}", card_type="orange" if sem_vencimento > 0 else "green")
    with aq6:
        metric_card("Registros Sem Responsável", f"{sem_responsavel:,}", card_type="orange" if sem_responsavel > 0 else "green")

    # Quadro de Auditoria e Reconciliação Matemática
    st.markdown("---")
    st.markdown("### 🧩 Reconciliação Matemática de Totais (Base Filtrada)")
    st.write("Garantia de que os totais operacionais estão perfeitamente consistentes em todos os resumos e tabelas.")

    n_filt = len(df_atual_filtered)
    soma_sla = int(resumo_sla_atual["Chamados"].sum())
    soma_72h = int(resumo_72h_atual["Chamados"].sum())

    fcr_exist = (ind_atual["fcr_tratado"] > 0)
    if fcr_exist:
        resumo_fcr_atual = df_atual_filtered["Status FCR 1h"].value_counts().reindex(
            ["Resolvido até 1h", "Resolvido acima de 1h", "FCR não informado", "Em aberto / Em tratamento"], 
            fill_value=0
        ).reset_index(name="Chamados")
        soma_fcr = int(resumo_fcr_atual["Chamados"].sum())
        
        rec_col1, rec_col2, rec_col3, rec_col4 = st.columns(4)
        rec_col1.metric("Registros na Base Filtrada", n_filt)
        rec_col2.metric("Soma das Categorias SLA", soma_sla)
        rec_col3.metric("Soma das Categorias 72h", soma_72h)
        rec_col4.metric("Soma das Categorias FCR", soma_fcr)
        
        audit_pass = (n_filt == soma_sla == soma_72h == soma_fcr)
    else:
        rec_col1, rec_col2, rec_col3 = st.columns(3)
        rec_col1.metric("Registros na Base Filtrada", n_filt)
        rec_col2.metric("Soma das Categorias SLA", soma_sla)
        rec_col3.metric("Soma das Categorias 72h", soma_72h)
        
        audit_pass = (n_filt == soma_sla == soma_72h)
        soma_fcr = n_filt

    if audit_pass:
        st.success("🟢 **Status de Auditoria: OK** - Todos os totais calculados coincidem perfeitamente. Nenhuma divergência detectada.")
    else:
        st.error(
            f"🔴 **Status de Auditoria: ATENÇÃO** - Existe uma divergência matemática entre os totais! "
            f"Base: {n_filt} | SLA: {soma_sla} | 72h: {soma_72h}" + (f" | FCR: {soma_fcr}" if fcr_exist else "") + 
            ". Verifique se há registros nulos não tratados."
        )


# ---------------------------------------------
# ABA 6: BASE ANALÍTICA (COM DOWNLOAD)
# ---------------------------------------------
with tab_base:
    st.markdown("### 📂 Base Analítica Tratada e Exportações")
    st.write("Visualize a base final consolidada com todos os tratamentos aplicados e faça a exportação.")

    # Exibição do Dataframe Filtrado
    st.write("##### Base de Dados Filtrada")
    st.dataframe(df_atual_filtered, use_container_width=True)

    # Botão de Exportação Consolidada
    st.markdown("---")
    st.markdown("### 📥 Download do Painel Completo em Excel")
    st.write("O arquivo gerado conterá a base tratada filtrada e todas as tabelas de resumo e frequência organizadas em abas.")

    # Preparar dicionário com todos os dados calculados da base atual filtrada
    resultado_atual_dict = {
        "df": df_atual_filtered,
        "indicadores": ind_atual,
        "resumo_clientes": resumo_clientes_atual,
        "resumo_categorias": resumo_categorias_atual,
        "resumo_solicitacoes": resumo_solicitacoes_atual,
        "resumo_sla": resumo_sla_atual,
        "resumo_72h": resumo_72h_atual,
        "df_responsaveis": df_resp_atual
    }

    # Anexar informações do mês anterior e comparativos se existir no session_state
    resultado_anterior_dict = st.session_state.get("resultado_anterior")
    label_mes_anterior_val = st.session_state.get("label_mes_anterior", "Mês anterior")
    arquivo_anterior_nome = st.session_state.get("arquivo_anterior_nome", "")

    if resultado_anterior_dict is not None:
        resultado_atual_dict["comparativo_indicadores"] = montar_comparativo_indicadores(ind_atual, resultado_anterior_dict["indicadores"])
        resultado_atual_dict["comp_clientes"] = comparar_frequencias(df_atual_filtered, resultado_anterior_dict["df"], "Cliente Análise", "Cliente")
        resultado_atual_dict["comp_categorias"] = comparar_frequencias(df_atual_filtered, resultado_anterior_dict["df"], "Categoria Principal", "Categoria Principal")
        resultado_atual_dict["comp_solicitacoes"] = comparar_frequencias(df_atual_filtered, resultado_anterior_dict["df"], "Solicitação Específica", "Solicitação Específica")

    try:
        excel_bin = gerar_excel_resultado(
            resultado_atual_dict, 
            resultado_anterior_dict,
            label_mes_atual=label_mes_atual,
            label_mes_anterior=label_mes_anterior_val,
            df_matrix=st.session_state.get("df_matrix_historico"),
            df_historico=st.session_state.get("df_resumo_historico"),
            df_historico_bases=st.session_state.get("df_historico_bases")
        )
        
        st.download_button(
            label="📥 Baixar Painel Completo em Excel",
            data=excel_bin,
            file_name="painel_chamados_consolidado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        st.error(f"Erro ao gerar planilha Excel de download: {str(e)}")
