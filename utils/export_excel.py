import io
import re
import pandas as pd

def limpar_nome_aba(nome):
    """
    Limpa e encurta nomes de abas do Excel para respeitar o limite máximo de 31 caracteres.
    """
    # Remover caracteres inválidos para abas do Excel: \ / ? * : [ ]
    for char in [r"\\", r"/", r"\?", r"\*", r":", r"\[", r"\]"]:
        nome = re.sub(char, "", nome)
    if len(nome) > 31:
        nome = nome[:31]
    return nome

def gerar_excel_resultado(resultado_atual, resultado_anterior=None, label_mes_atual="Mês atual", label_mes_anterior="Mês anterior", df_matrix=None, df_historico=None, df_historico_bases=None):
    """
    Gera uma planilha Excel em memória (.xlsx) com múltiplas abas formatadas,
    contendo os resumos, comparativos detalhados, matriz de auditoria e bases tratadas.
    Retorna o valor binário do arquivo gerado para download direto no Streamlit.
    """
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        # 1. ABA RESUMO ATUAL
        df_ind_atual = pd.DataFrame(
            list(resultado_atual["indicadores"].items()),
            columns=["Indicador", label_mes_atual]
        )
        df_ind_atual.to_excel(writer, sheet_name=limpar_nome_aba("Resumo_Atual"), index=False)

        # 2. ABA BASE TRATADA ATUAL
        resultado_atual["df"].to_excel(writer, sheet_name=limpar_nome_aba("Base_Tratada_Atual"), index=False)

        # Se houver base do mês anterior para comparação
        if resultado_anterior is not None:
            # 3. ABA RESUMO ANTERIOR
            df_ind_anterior = pd.DataFrame(
                list(resultado_anterior["indicadores"].items()),
                columns=["Indicador", label_mes_anterior]
            )
            df_ind_anterior.to_excel(writer, sheet_name=limpar_nome_aba("Resumo_Anterior"), index=False)

            # 4. ABA COMPARATIVO GERAL DE INDICADORES
            if "comparativo_indicadores" in resultado_atual:
                df_comp = resultado_atual["comparativo_indicadores"].copy()
                df_comp = df_comp.rename(columns={"Mês anterior": label_mes_anterior, "Mês atual": label_mes_atual})
                df_comp.to_excel(writer, sheet_name=limpar_nome_aba("Comparativo_Geral"), index=False)

            # 5. ABAS COMPARATIVAS DE SLA E 72H
            # SLA Comparativo
            if "resumo_sla" in resultado_anterior and "resumo_sla" in resultado_atual:
                sla_ant = resultado_anterior["resumo_sla"].rename(columns={"Chamados": label_mes_anterior})
                sla_at = resultado_atual["resumo_sla"].rename(columns={"Chamados": label_mes_atual})
                sla_comp = pd.merge(sla_ant, sla_at, on="Status SLA", how="outer").fillna(0)
                sla_comp.to_excel(writer, sheet_name=limpar_nome_aba("SLA_Comparativo"), index=False)

            # 72h Comparativo
            if "resumo_72h" in resultado_anterior and "resumo_72h" in resultado_atual:
                h72_ant = resultado_anterior["resumo_72h"].rename(columns={"Chamados": label_mes_anterior})
                h72_at = resultado_atual["resumo_72h"].rename(columns={"Chamados": label_mes_atual})
                h72_comp = pd.merge(h72_ant, h72_at, on="Status 72h", how="outer").fillna(0)
                h72_comp.to_excel(writer, sheet_name=limpar_nome_aba("72h_Comparativo"), index=False)

            # FCR Comparativo (se disponível)
            fcr_disponivel = (resultado_atual["indicadores"].get("fcr_tratado", 0) > 0) or \
                             (resultado_anterior["indicadores"].get("fcr_tratado", 0) > 0)
            if fcr_disponivel and "resumo_fcr_1h" in resultado_anterior and "resumo_fcr_1h" in resultado_atual:
                fcr_ant = resultado_anterior["resumo_fcr_1h"].rename(columns={"Chamados": label_mes_anterior})
                fcr_at = resultado_atual["resumo_fcr_1h"].rename(columns={"Chamados": label_mes_atual})
                fcr_comp = pd.merge(fcr_ant, fcr_at, on="Status FCR 1h", how="outer").fillna(0)
                fcr_comp.to_excel(writer, sheet_name=limpar_nome_aba("FCR_Comparativo"), index=False)

            # 6. ABAS COMPARATIVAS DE DISTRIBUIÇÃO (Clientes, Categorias e Solicitações)
            if "comp_clientes" in resultado_atual:
                df_comp_cli = resultado_atual["comp_clientes"].copy()
                df_comp_cli = df_comp_cli.rename(columns={"Mês anterior": label_mes_anterior, "Mês atual": label_mes_atual})
                df_comp_cli.to_excel(writer, sheet_name=limpar_nome_aba("Clientes_Comparativo"), index=False)

            if "comp_categorias" in resultado_atual:
                df_comp_cat = resultado_atual["comp_categorias"].copy()
                df_comp_cat = df_comp_cat.rename(columns={"Mês anterior": label_mes_anterior, "Mês atual": label_mes_atual})
                df_comp_cat.to_excel(writer, sheet_name=limpar_nome_aba("Categorias_Comparativo"), index=False)

            if "comp_solicitacoes" in resultado_atual:
                df_comp_sol = resultado_atual["comp_solicitacoes"].copy()
                df_comp_sol = df_comp_sol.rename(columns={"Mês anterior": label_mes_anterior, "Mês atual": label_mes_atual})
                df_comp_sol.to_excel(writer, sheet_name=limpar_nome_aba("Solicitacoes_Comparativo"), index=False)

            # 7. ABA BASE ANTERIOR TRATADA
            resultado_anterior["df"].to_excel(writer, sheet_name=limpar_nome_aba("Base_Tratada_Anterior"), index=False)

        else:
            # Se não houver comparação, exportar frequências do mês atual
            resultado_atual["resumo_clientes"].to_excel(writer, sheet_name=limpar_nome_aba("Clientes_Atual"), index=False)
            resultado_atual["resumo_categorias"].to_excel(writer, sheet_name=limpar_nome_aba("Categorias_Atual"), index=False)
            resultado_atual["resumo_solicitacoes"].to_excel(writer, sheet_name=limpar_nome_aba("Solicitacoes_Atual"), index=False)
            resultado_atual["df_responsaveis"].to_excel(writer, sheet_name=limpar_nome_aba("Responsaveis_Atual"), index=False)

        # 8. ABAS DE HISTÓRICO (Se existirem)
        if df_matrix is not None:
            df_matrix.to_excel(writer, sheet_name=limpar_nome_aba("Matriz_Auditoria"), index=True)
        if df_historico is not None:
            df_historico.to_excel(writer, sheet_name=limpar_nome_aba("Historico_12_Meses"), index=False)

        # 9. BASES TRATADAS HISTÓRICAS (Se existirem)
        if df_historico_bases is not None:
            for lbl, df_m in df_historico_bases.items():
                aba_name = limpar_nome_aba(f"Base_{lbl.replace('/', '_')}")
                df_m.to_excel(writer, sheet_name=aba_name, index=False)

    output.seek(0)
    return output.getvalue()
