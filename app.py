import io
import re
import unicodedata

import pandas as pd
import streamlit as st
import plotly.express as px


st.set_page_config(
    page_title="Dashboard de Chamados",
    page_icon="📊",
    layout="wide"
)


def normalizar_texto(texto):
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join([c for c in texto if not unicodedata.combining(c)])
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return texto.strip()


def encontrar_coluna(df, opcoes):
    colunas_norm = {col: normalizar_texto(col) for col in df.columns}

    for opcao in opcoes:
        opcao_norm = normalizar_texto(opcao)
        for col, col_norm in colunas_norm.items():
            if opcao_norm == col_norm:
                return col

    for opcao in opcoes:
        opcao_norm = normalizar_texto(opcao)
        for col, col_norm in colunas_norm.items():
            if opcao_norm in col_norm:
                return col

    return None


def ler_arquivo(uploaded_file):
    nome = uploaded_file.name.lower()

    if nome.endswith(".csv"):
        try:
            return pd.read_csv(uploaded_file, sep=None, engine="python", encoding="utf-8")
        except Exception:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, sep=None, engine="python", encoding="latin1")

    if nome.endswith(".xls"):
        return pd.read_excel(uploaded_file, engine="xlrd")

    return pd.read_excel(uploaded_file)


def preparar_datas(df, coluna):
    df[coluna] = pd.to_datetime(df[coluna], errors="coerce", dayfirst=True)
    return df


def gerar_excel_dashboard(indicadores, resumo_empresas, resumo_qualificacoes, resumo_sla, resumo_72h):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet("Dashboard")
        writer.sheets["Dashboard"] = worksheet

        fmt_titulo = workbook.add_format({
            "bold": True,
            "font_size": 20,
            "align": "center",
            "valign": "vcenter",
            "font_color": "white",
            "bg_color": "#1F4E78"
        })

        fmt_card = workbook.add_format({
            "bold": True,
            "font_size": 13,
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "bg_color": "#D9EAF7"
        })

        fmt_card_valor = workbook.add_format({
            "bold": True,
            "font_size": 20,
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "bg_color": "#F2F2F2"
        })

        fmt_secao = workbook.add_format({
            "bold": True,
            "font_size": 12,
            "font_color": "white",
            "bg_color": "#4472C4",
            "border": 1
        })

        fmt_header = workbook.add_format({
            "bold": True,
            "bg_color": "#B4C6E7",
            "border": 1,
            "align": "center"
        })

        fmt_cell = workbook.add_format({"border": 1})

        worksheet.set_column("A:A", 4)
        worksheet.set_column("B:B", 35)
        worksheet.set_column("C:C", 18)
        worksheet.set_column("D:D", 18)
        worksheet.set_column("E:E", 18)
        worksheet.set_column("F:F", 35)
        worksheet.set_column("G:G", 18)
        worksheet.set_column("H:H", 18)
        worksheet.set_column("I:I", 18)
        worksheet.set_column("J:J", 18)

        worksheet.merge_range("B2:J3", "DASHBOARD DE CHAMADOS", fmt_titulo)

        cards = [
            ("Total de chamados", indicadores["total_chamados"]),
            ("Empresas com chamados", indicadores["total_empresas"]),
            ("SLA tratado", indicadores["sla_tratado"]),
            ("Dentro do SLA", indicadores["dentro_sla"]),
            ("Fora do SLA", indicadores["fora_sla"]),
            ("% dentro SLA", f'{indicadores["percentual_dentro_sla"]:.1f}%'),
            ("Tratados até 72h", indicadores["ate_72h"]),
            ("Acima de 72h / abertos", indicadores["acima_72h"]),
        ]

        posicoes = [
            ("B5", "C5", "B6", "C6"),
            ("D5", "E5", "D6", "E6"),
            ("F5", "G5", "F6", "G6"),
            ("H5", "I5", "H6", "I6"),
            ("B8", "C8", "B9", "C9"),
            ("D8", "E8", "D9", "E9"),
            ("F8", "G8", "F9", "G9"),
            ("H8", "I8", "H9", "I9"),
        ]

        for (titulo, valor), pos in zip(cards, posicoes):
            worksheet.merge_range(f"{pos[0]}:{pos[1]}", titulo, fmt_card)
            worksheet.merge_range(f"{pos[2]}:{pos[3]}", valor, fmt_card_valor)

        worksheet.merge_range("B11:E11", "Empresa com mais chamados", fmt_secao)
        worksheet.merge_range("B12:E12", indicadores["empresa_top"], fmt_cell)
        worksheet.write("F11", "Qtd.", fmt_secao)
        worksheet.write("F12", indicadores["empresa_top_qtd"], fmt_cell)

        worksheet.merge_range("B14:E14", "Qualificação mais solicitada", fmt_secao)
        worksheet.merge_range("B15:E15", indicadores["qualificacao_top"], fmt_cell)
        worksheet.write("F14", "Qtd.", fmt_secao)
        worksheet.write("F15", indicadores["qualificacao_top_qtd"], fmt_cell)

        linha = 18
        worksheet.merge_range(linha, 1, linha, 3, "Top empresas por chamados", fmt_secao)
        linha += 1
        worksheet.write(linha, 1, "Empresa", fmt_header)
        worksheet.write(linha, 2, "Chamados", fmt_header)

        for _, row in resumo_empresas.head(10).iterrows():
            linha += 1
            worksheet.write(linha, 1, str(row["Empresa"]), fmt_cell)
            worksheet.write(linha, 2, int(row["Chamados"]), fmt_cell)

        linha = 18
        worksheet.merge_range(linha, 5, linha, 8, "Top qualificações solicitadas", fmt_secao)
        linha += 1
        worksheet.write(linha, 5, "Qualificação", fmt_header)
        worksheet.write(linha, 6, "Chamados", fmt_header)

        for _, row in resumo_qualificacoes.head(10).iterrows():
            linha += 1
            worksheet.write(linha, 5, str(row["Qualificação"]), fmt_cell)
            worksheet.write(linha, 6, int(row["Chamados"]), fmt_cell)

        linha_sla = 32
        worksheet.merge_range(linha_sla, 1, linha_sla, 3, "Resumo SLA", fmt_secao)
        linha_sla += 1
        worksheet.write(linha_sla, 1, "Status SLA", fmt_header)
        worksheet.write(linha_sla, 2, "Chamados", fmt_header)

        for _, row in resumo_sla.iterrows():
            linha_sla += 1
            worksheet.write(linha_sla, 1, str(row["Status SLA"]), fmt_cell)
            worksheet.write(linha_sla, 2, int(row["Chamados"]), fmt_cell)

        linha_72 = 32
        worksheet.merge_range(linha_72, 5, linha_72, 8, "Resumo tratamento em 72 horas", fmt_secao)
        linha_72 += 1
        worksheet.write(linha_72, 5, "Status 72h", fmt_header)
        worksheet.write(linha_72, 6, "Chamados", fmt_header)

        for _, row in resumo_72h.iterrows():
            linha_72 += 1
            worksheet.write(linha_72, 5, str(row["Status 72h"]), fmt_cell)
            worksheet.write(linha_72, 6, int(row["Chamados"]), fmt_cell)

        chart_72h = workbook.add_chart({"type": "pie"})
        chart_72h.add_series({
            "name": "Tratamento em 72 horas",
            "categories": ["Dashboard", 34, 5, 35, 5],
            "values": ["Dashboard", 34, 6, 35, 6],
            "data_labels": {"percentage": True, "category": True}
        })
        chart_72h.set_title({"name": "Chamados tratados em até 72 horas"})
        worksheet.insert_chart("H32", chart_72h, {"x_scale": 1.2, "y_scale": 1.2})

        chart_empresas = workbook.add_chart({"type": "bar"})
        chart_empresas.add_series({
            "name": "Chamados",
            "categories": ["Dashboard", 20, 1, 29, 1],
            "values": ["Dashboard", 20, 2, 29, 2],
            "data_labels": {"value": True}
        })
        chart_empresas.set_title({"name": "Top empresas por chamados"})
        worksheet.insert_chart("B38", chart_empresas, {"x_scale": 1.5, "y_scale": 1.5})

        chart_qual = workbook.add_chart({"type": "bar"})
        chart_qual.add_series({
            "name": "Chamados",
            "categories": ["Dashboard", 20, 5, 29, 5],
            "values": ["Dashboard", 20, 6, 29, 6],
            "data_labels": {"value": True}
        })
        chart_qual.set_title({"name": "Top qualificações solicitadas"})
        worksheet.insert_chart("G38", chart_qual, {"x_scale": 1.5, "y_scale": 1.5})

    output.seek(0)
    return output


st.title("📊 Dashboard de Chamados")
st.write("Envie a planilha do mês para gerar o dashboard atualizado automaticamente.")

arquivo = st.file_uploader(
    "Faça upload da planilha",
    type=["xls", "xlsx", "xlsm", "csv"]
)

if arquivo is not None:
    try:
        df = ler_arquivo(arquivo)

        col_empresa = encontrar_coluna(df, [
            "Empresa", "Cliente", "Nome Fantasia", "Razão Social", "Razao Social"
        ])

        col_abertura = encontrar_coluna(df, [
            "Abertura", "Data Abertura", "Data de Abertura", "Criado em", "Data de Criação"
        ])

        col_encerramento = encontrar_coluna(df, [
            "Encerramento", "Data Encerramento", "Data de Encerramento", "Fechado em", "Resolvido em"
        ])

        col_vencimento = encontrar_coluna(df, [
            "Vencimento", "Data Vencimento", "SLA", "Prazo", "Data SLA"
        ])

        col_qualificacao = encontrar_coluna(df, [
            "Categoria", "Qualificação", "Qualificacao", "Tipo", "Item", "Assunto", "Serviço", "Servico"
        ])

        colunas_obrigatorias = {
            "Empresa": col_empresa,
            "Abertura": col_abertura,
            "Encerramento": col_encerramento,
            "Vencimento": col_vencimento,
            "Qualificação/Categoria": col_qualificacao,
        }

        colunas_faltando = [nome for nome, coluna in colunas_obrigatorias.items() if coluna is None]

        if colunas_faltando:
            st.error("Não consegui identificar automaticamente algumas colunas.")
            st.write("Colunas faltando:")
            st.write(colunas_faltando)
            st.write("Colunas encontradas na planilha:")
            st.write(list(df.columns))
            st.stop()

        st.success("Arquivo carregado com sucesso!")

        df = preparar_datas(df, col_abertura)
        df = preparar_datas(df, col_encerramento)
        df = preparar_datas(df, col_vencimento)

        df[col_empresa] = df[col_empresa].fillna("Não informado").astype(str).str.strip()
        df[col_qualificacao] = df[col_qualificacao].fillna("Não informado").astype(str).str.strip()

        total_chamados = len(df)
        total_empresas = df[col_empresa].nunique()

        df["Status SLA"] = "Não tratado"

        mask_fechado_com_prazo = df[col_encerramento].notna() & df[col_vencimento].notna()

        df.loc[
            mask_fechado_com_prazo & (df[col_encerramento] <= df[col_vencimento]),
            "Status SLA"
        ] = "Dentro do SLA"

        df.loc[
            mask_fechado_com_prazo & (df[col_encerramento] > df[col_vencimento]),
            "Status SLA"
        ] = "Fora do SLA"

        sla_tratado = int(mask_fechado_com_prazo.sum())
        dentro_sla = int((df["Status SLA"] == "Dentro do SLA").sum())
        fora_sla = int((df["Status SLA"] == "Fora do SLA").sum())
        percentual_dentro_sla = (dentro_sla / sla_tratado * 100) if sla_tratado > 0 else 0

        df["Horas para tratamento"] = None
        mask_fechado_com_abertura = df[col_abertura].notna() & df[col_encerramento].notna()

        df.loc[mask_fechado_com_abertura, "Horas para tratamento"] = (
            (
                df.loc[mask_fechado_com_abertura, col_encerramento]
                - df.loc[mask_fechado_com_abertura, col_abertura]
            ).dt.total_seconds() / 3600
        )

        df["Status 72h"] = "Acima de 72h ou em aberto"

        df.loc[
            mask_fechado_com_abertura & (df["Horas para tratamento"] <= 72),
            "Status 72h"
        ] = "Tratado até 72h"

        ate_72h = int((df["Status 72h"] == "Tratado até 72h").sum())
        acima_72h = int((df["Status 72h"] == "Acima de 72h ou em aberto").sum())

        resumo_empresas = (
            df.groupby(col_empresa)
            .size()
            .reset_index(name="Chamados")
            .rename(columns={col_empresa: "Empresa"})
            .sort_values("Chamados", ascending=False)
        )

        resumo_qualificacoes = (
            df.groupby(col_qualificacao)
            .size()
            .reset_index(name="Chamados")
            .rename(columns={col_qualificacao: "Qualificação"})
            .sort_values("Chamados", ascending=False)
        )

        resumo_sla = (
            df.groupby("Status SLA")
            .size()
            .reset_index(name="Chamados")
        )

        resumo_72h = (
            df.groupby("Status 72h")
            .size()
            .reset_index(name="Chamados")
        )

        empresa_top = resumo_empresas.iloc[0]["Empresa"]
        empresa_top_qtd = int(resumo_empresas.iloc[0]["Chamados"])

        qualificacao_top = resumo_qualificacoes.iloc[0]["Qualificação"]
        qualificacao_top_qtd = int(resumo_qualificacoes.iloc[0]["Chamados"])

        indicadores = {
            "total_chamados": total_chamados,
            "total_empresas": total_empresas,
            "sla_tratado": sla_tratado,
            "dentro_sla": dentro_sla,
            "fora_sla": fora_sla,
            "percentual_dentro_sla": percentual_dentro_sla,
            "ate_72h": ate_72h,
            "acima_72h": acima_72h,
            "empresa_top": empresa_top,
            "empresa_top_qtd": empresa_top_qtd,
            "qualificacao_top": qualificacao_top,
            "qualificacao_top_qtd": qualificacao_top_qtd,
        }

        st.subheader("Dashboard atualizado")

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total de chamados", total_chamados)
        k2.metric("Empresas com chamados", total_empresas)
        k3.metric("SLA tratado", sla_tratado)
        k4.metric("% dentro SLA", f"{percentual_dentro_sla:.1f}%")

        k5, k6, k7, k8 = st.columns(4)
        k5.metric("Dentro do SLA", dentro_sla)
        k6.metric("Fora do SLA", fora_sla)
        k7.metric("Tratados até 72h", ate_72h)
        k8.metric("Acima de 72h / abertos", acima_72h)

        st.info(f"Empresa com mais chamados: **{empresa_top}** — {empresa_top_qtd} chamados.")
        st.info(f"Qualificação mais solicitada: **{qualificacao_top}** — {qualificacao_top_qtd} chamados.")

        g1, g2 = st.columns(2)

        with g1:
            st.write("### Tratamento em 72 horas")
            fig_72h = px.pie(
                resumo_72h,
                names="Status 72h",
                values="Chamados",
                hole=0.35,
                title="Tratados até 72h x acima de 72h / abertos"
            )
            st.plotly_chart(fig_72h, use_container_width=True)

        with g2:
            st.write("### SLA")
            fig_sla = px.bar(
                resumo_sla,
                x="Status SLA",
                y="Chamados",
                text="Chamados",
                title="Resumo SLA"
            )
            st.plotly_chart(fig_sla, use_container_width=True)

        g3, g4 = st.columns(2)

        with g3:
            st.write("### Top empresas por chamados")
            fig_empresas = px.bar(
                resumo_empresas.head(10),
                x="Chamados",
                y="Empresa",
                orientation="h",
                text="Chamados",
                title="Top empresas"
            )
            fig_empresas.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_empresas, use_container_width=True)

        with g4:
            st.write("### Top qualificações")
            fig_qual = px.bar(
                resumo_qualificacoes.head(10),
                x="Chamados",
                y="Qualificação",
                orientation="h",
                text="Chamados",
                title="Top qualificações solicitadas"
            )
            fig_qual.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_qual, use_container_width=True)

        st.subheader("Tabelas de conferência")

        t1, t2 = st.columns(2)

        with t1:
            st.write("Empresas")
            st.dataframe(resumo_empresas, use_container_width=True)

        with t2:
            st.write("Qualificações")
            st.dataframe(resumo_qualificacoes, use_container_width=True)

        total_resumo_72h = int(resumo_72h["Chamados"].sum())
        total_resumo_sla = int(resumo_sla["Chamados"].sum())

        st.subheader("Conferência dos totais")

        if total_resumo_72h == total_chamados:
            st.success(f"Resumo 72h está batendo: {total_resumo_72h} chamados.")
        else:
            st.error(f"Resumo 72h não está batendo. Base: {total_chamados} | Resumo: {total_resumo_72h}")

        if total_resumo_sla == total_chamados:
            st.success(f"Resumo SLA está batendo: {total_resumo_sla} chamados.")
        else:
            st.warning(f"Resumo SLA precisa verificar. Base: {total_chamados} | Resumo: {total_resumo_sla}")

        excel_dashboard = gerar_excel_dashboard(
            indicadores,
            resumo_empresas,
            resumo_qualificacoes,
            resumo_sla,
            resumo_72h
        )

        st.download_button(
            label="📥 Baixar dashboard em Excel",
            data=excel_dashboard,
            file_name="dashboard_chamados_atualizado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error("Erro ao processar a planilha.")
        st.exception(e)

else:
    st.warning("Envie uma planilha para começar.")
