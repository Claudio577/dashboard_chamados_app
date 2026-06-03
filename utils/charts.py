import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Cores padrão corporativas (estilo Power BI)
PALETA_CATEGORIAS = ["#1F4E78", "#2F5597", "#8FAADC", "#D9E1F2", "#10B981", "#F59E0B"]
PALETA_MESES = {"Mês anterior": "#A6C8E0", "Mês atual": "#1F4E78"}

COLOR_MAP_SLA = {
    "Dentro do SLA": "#10B981",
    "Fora do SLA": "#EF4444",
    "SLA não informado": "#9CA3AF",
    "Em aberto / Em tratamento": "#F59E0B"
}

COLOR_MAP_72H = {
    "Tratado até 72h": "#10B981",
    "Tratado acima de 72h": "#EF4444",
    "72h não informado": "#9CA3AF",
    "Em aberto / Em tratamento": "#F59E0B"
}

COLOR_MAP_FCR = {
    "Resolvido até 1h": "#10B981",
    "Resolvido acima de 1h": "#EF4444",
    "FCR não informado": "#9CA3AF",
    "Em aberto / Em tratamento": "#F59E0B"
}


def plot_donut_chart(df, names_col, title, color_map=None):
    """
    Gera um gráfico de rosca (Donut) interativo.
    """
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title=title)
        return fig
        
    counts = df[names_col].value_counts().reset_index(name="Chamados")
    
    fig = px.pie(
        counts,
        names=names_col,
        values="Chamados",
        hole=0.45,
        title=title,
        color=names_col,
        color_discrete_map=color_map
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        margin=dict(t=50, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    return fig


def plot_horizontal_bar(df, category_col, title, top_n=10, color="#1F4E78"):
    """
    Gera um gráfico de barras horizontal de ranking.
    """
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title=title)
        return fig

    counts = df[category_col].value_counts().reset_index(name="Chamados")
    counts = counts.head(top_n)

    fig = px.bar(
        counts,
        x="Chamados",
        y=category_col,
        orientation="h",
        text="Chamados",
        title=title,
    )
    
    fig.update_traces(
        marker_color=color,
        texttemplate='%{text}',
        textposition='outside'
    )
    
    fig.update_layout(
        yaxis={"categoryorder": "total ascending", "title": ""},
        xaxis={"title": "Quantidade de Chamados"},
        margin=dict(t=50, b=10, l=10, r=10)
    )
    return fig


def plot_grouped_bar_comparison(df_comp_melt, category_col, title, label_mes_anterior, label_mes_atual, height=400):
    """
    Gera um gráfico de comparação de barra horizontal agrupado (Mês anterior vs Mês atual) com legendas reais.
    """
    if df_comp_melt.empty:
        fig = go.Figure()
        fig.update_layout(title=title)
        return fig

    color_map = {
        label_mes_anterior: "#A6C8E0",
        label_mes_atual: "#1F4E78"
    }

    fig = px.bar(
        df_comp_melt,
        x="Chamados",
        y=category_col,
        color="Mês",
        barmode="group",
        orientation="h",
        text="Chamados",
        title=title,
        color_discrete_map=color_map,
        category_orders={"Mês": [label_mes_anterior, label_mes_atual]}
    )
    
    fig.update_traces(textposition='outside')
    fig.update_layout(
        yaxis={"categoryorder": "total ascending", "title": ""},
        xaxis={"title": "Chamados"},
        height=height,
        margin=dict(t=50, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
    )
    return fig


def plot_grouped_status_comparison(df_status, status_col, title, order_list, color_map, label_mes_anterior, label_mes_atual):
    """
    Gera comparação agrupada de status vertical (SLA ou 72h) entre meses usando nomes de meses reais.
    """
    if df_status.empty:
        fig = go.Figure()
        fig.update_layout(title=title)
        return fig

    # Contagem de status por mês
    grouped = df_status.groupby(["Mês", status_col]).size().reset_index(name="Chamados")

    color_map_meses = {
        label_mes_anterior: "#A6C8E0",
        label_mes_atual: "#1F4E78"
    }

    fig = px.bar(
        grouped,
        x=status_col,
        y="Chamados",
        color="Mês",
        barmode="group",
        text="Chamados",
        title=title,
        category_orders={status_col: order_list, "Mês": [label_mes_anterior, label_mes_atual]},
        color_discrete_map=color_map_meses
    )
    
    fig.update_traces(textposition='outside')
    fig.update_layout(
        xaxis={"title": ""},
        yaxis={"title": "Chamados"},
        margin=dict(t=50, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
    )
    return fig


def plot_stacked_bar_status(df, x_col, status_col, title, color_map, top_n=10):
    """
    Gera um gráfico de barras empilhadas por responsável ou cliente para ver a distribuição de status.
    """
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title=title)
        return fig

    # Descobrir top X por volume total para não lotar o gráfico
    top_items = df[x_col].value_counts().head(top_n).index
    df_filtered = df[df[x_col].isin(top_items)]
    
    grouped = df_filtered.groupby([x_col, status_col]).size().reset_index(name="Chamados")

    fig = px.bar(
        grouped,
        x=x_col,
        y="Chamados",
        color=status_col,
        title=title,
        text="Chamados",
        color_discrete_map=color_map
    )
    
    fig.update_layout(
        xaxis={"title": "", "tickangle": -25},
        yaxis={"title": "Chamados"},
        margin=dict(t=50, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )
    return fig


def plot_simple_vertical_bar(df, x_col, y_col, title, color="#1F4E78"):
    """
    Gráfico de barras vertical simples para tempo médio ou rankings numéricos.
    """
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title=title)
        return fig

    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        text=y_col,
        title=title
    )
    
    fig.update_traces(
        marker_color=color,
        textposition='outside'
    )
    
    fig.update_layout(
        xaxis={"title": "", "tickangle": -25},
        yaxis={"title": y_col},
        margin=dict(t=50, b=10, l=10, r=10)
    )
    return fig


def plot_historical_line(df_hist, x_col, y_col, title, y_axis_format=None):
    """
    Gera um gráfico de linha interativo para o histórico de meses.
    """
    if df_hist.empty:
        fig = go.Figure()
        fig.update_layout(title=title)
        return fig
        
    fig = px.line(
        df_hist,
        x=x_col,
        y=y_col,
        text=y_col,
        title=title,
        markers=True
    )
    
    if y_axis_format == "percent":
        fig.update_traces(texttemplate='%{y:.1f}%', textposition="top center", line_color="#1F4E78", marker=dict(size=8, color="#10B981"))
        fig.update_layout(yaxis_ticksuffix="%")
    else:
        fig.update_traces(texttemplate='%{y}', textposition="top center", line_color="#1F4E78", marker=dict(size=8, color="#10B981"))
        
    fig.update_layout(
        margin=dict(t=50, b=10, l=20, r=20),
        xaxis={"title": "Período", "type": "category"},
        yaxis={"title": y_col}
    )
    return fig


def plot_historical_bar(df_hist, x_col, y_col, title, color="#1F4E78"):
    """
    Gera um gráfico de barras vertical interativo para o histórico de meses.
    """
    if df_hist.empty:
        fig = go.Figure()
        fig.update_layout(title=title)
        return fig
        
    fig = px.bar(
        df_hist,
        x=x_col,
        y=y_col,
        text=y_col,
        title=title
    )
    
    fig.update_traces(
        marker_color=color,
        texttemplate='%{y}',
        textposition="outside"
    )
    
    fig.update_layout(
        margin=dict(t=50, b=10, l=20, r=20),
        xaxis={"title": "Período", "type": "category"},
        yaxis={"title": y_col}
    )
    return fig

