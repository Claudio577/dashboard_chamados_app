import streamlit as st
import pandas as pd

def injetar_css_cards():
    """
    Injeta o estilo CSS comum para os cards personalizados e elementos estilo Power BI.
    """
    st.markdown("""
    <style>
    /* Estilos globais e fontes se necessário */
    .dashboard-title {
        font-size: 32px;
        font-weight: 700;
        color: #1F4E78;
        margin-bottom: 2px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .dashboard-subtitle {
        font-size: 14px;
        color: #555555;
        margin-bottom: 15px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .header-divider {
        height: 4px;
        background: linear-gradient(90deg, #1F4E78 0%, #10B981 100%);
        border-radius: 2px;
        margin-bottom: 25px;
    }
    </style>
    """, unsafe_allow_html=True)


def render_header(titulo, subtitulo=None, periodo=None):
    """
    Renderiza um cabeçalho executivo elegante.
    """
    injetar_css_cards()
    st.markdown(f'<div class="dashboard-title">{titulo}</div>', unsafe_allow_html=True)
    
    sub_text = ""
    if subtitulo:
        sub_text += f"{subtitulo}"
    if periodo:
        if sub_text:
            sub_text += f" | Período: **{periodo}**"
        else:
            sub_text += f"Período: **{periodo}**"
            
    if sub_text:
        st.markdown(f'<div class="dashboard-subtitle">{sub_text}</div>', unsafe_allow_html=True)
        
    st.markdown('<div class="header-divider"></div>', unsafe_allow_html=True)


def metric_card(title, value, delta=None, delta_direction=None, card_type="blue"):
    """
    Renderiza um cartão de KPI estilo Power BI.
    - card_type: 'blue' (neutro), 'green' (sucesso), 'red' (atenção/erro), 'orange' (pendência)
    - delta_direction: 'up' (positivo para métrica boa), 'down' (negativo para métrica boa), 'neutral'
    """
    color_map = {
        "blue": "#1F4E78",
        "green": "#10B981",
        "red": "#EF4444",
        "orange": "#F59E0B"
    }
    border_color = color_map.get(card_type, "#1F4E78")
    
    delta_html = ""
    if delta:
        if delta_direction == "up":
            delta_html = f'<div style="color: #10B981; font-size: 13px; font-weight: 600; margin-top: 4px; display: flex; align-items: center;">▲ {delta}</div>'
        elif delta_direction == "down":
            delta_html = f'<div style="color: #EF4444; font-size: 13px; font-weight: 600; margin-top: 4px; display: flex; align-items: center;">▼ {delta}</div>'
        elif delta_direction == "green-down":
            delta_html = f'<div style="color: #10B981; font-size: 13px; font-weight: 600; margin-top: 4px; display: flex; align-items: center;">▼ {delta}</div>'
        elif delta_direction == "red-up":
            delta_html = f'<div style="color: #EF4444; font-size: 13px; font-weight: 600; margin-top: 4px; display: flex; align-items: center;">▲ {delta}</div>'
        else:
            delta_html = f'<div style="color: #6B7280; font-size: 13px; font-weight: 600; margin-top: 4px; display: flex; align-items: center;">{delta}</div>'
            
    card_html = f"""
    <div style="
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -1px rgba(0, 0, 0, 0.04);
        border-left: 5px solid {border_color};
        margin: 8px 0px;
        min-height: 105px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        border-top: 1px solid #F3F4F6;
        border-right: 1px solid #F3F4F6;
        border-bottom: 1px solid #F3F4F6;
    ">
        <div style="font-size: 12px; color: #6B7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">{title}</div>
        <div style="font-size: 28px; font-weight: 700; color: #111827; line-height: 1.1;">{value}</div>
        {delta_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def highlight_block(title, name, value, percentage=None, card_type="blue"):
    """
    Renderiza um painel de destaque para top entidades.
    """
    color_map = {
        "blue": "#1F4E78",
        "green": "#10B981",
        "red": "#EF4444",
        "orange": "#F59E0B"
    }
    border_color = color_map.get(card_type, "#1F4E78")
    
    pct_html = f'<span style="font-size: 14px; font-weight: normal; color: #6B7280;"> ({percentage:.1f}%)</span>' if percentage is not None else ""
    
    card_html = f"""
    <div style="
        background-color: #F9FAFB;
        border-radius: 8px;
        padding: 16px;
        box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.04);
        border: 1px solid #E5E7EB;
        border-top: 4px solid {border_color};
        margin: 8px 0px;
        min-height: 125px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    ">
        <div style="font-size: 11px; color: #6B7280; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px;">{title}</div>
        <div style="font-size: 15px; font-weight: 600; color: #1F2937; margin: 8px 0px; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; line-height: 1.3;">{name}</div>
        <div style="font-size: 18px; font-weight: 700; color: {border_color};">{value}{pct_html} <span style="font-size: 12px; font-weight: 500; color: #9CA3AF;">chamados</span></div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def comparative_metric_card(
    title,
    label_atual,
    val_atual,
    label_anterior,
    val_anterior,
    diff,
    pct_change,
    semantic_type
):
    """
    Renderiza um cartão comparativo executivo estilo Power BI.
    - title: Nome do indicador
    - label_atual: Nome do mês atual (ex: Maio/2026)
    - val_atual: Valor no mês atual
    - label_anterior: Nome do mês anterior (ex: Abril/2026)
    - val_anterior: Valor no mês anterior
    - diff: Diferença absoluta
    - pct_change: Variação percentual
    - semantic_type: 'total', 'positive', 'negative'
    """
    try:
        diff_val = float(diff)
    except (ValueError, TypeError):
        diff_val = 0.0

    is_good = False
    is_neutral = False
    
    if semantic_type == "total":
        # Redução é verde, aumento é laranja/vermelho de atenção
        if diff_val < 0:
            is_good = True
        elif diff_val > 0:
            is_good = False
        else:
            is_neutral = True
    elif semantic_type == "positive":
        # Aumento é verde, redução é vermelha
        if diff_val > 0:
            is_good = True
        elif diff_val < 0:
            is_good = False
        else:
            is_neutral = True
    elif semantic_type == "negative":
        # Redução é verde, aumento é vermelho
        if diff_val < 0:
            is_good = True
        elif diff_val > 0:
            is_good = False
        else:
            is_neutral = True
    else:
        is_neutral = True

    if is_neutral:
        delta_color = "#6B7280"  # cinza
        border_color = "#1F4E78" # azul
        icon = "="
    elif is_good:
        delta_color = "#10B981"  # verde
        border_color = "#10B981" # verde
        icon = "▲" if diff_val > 0 else "▼"
    else:
        delta_color = "#EF4444"  # vermelho
        border_color = "#EF4444" # vermelho
        icon = "▲" if diff_val > 0 else "▼"
        if semantic_type == "total" and diff_val > 0:
            delta_color = "#F59E0B"  # laranja para aumento no total
            border_color = "#F59E0B"

    # Se for porcentagem, mostrar diferença em p.p. (pontos percentuais)
    is_percentage = "%" in title or "taxa" in title.lower() or "percentual" in title.lower()
    
    if is_percentage:
        delta_text = f"{icon} {diff:+.1f} p.p." if isinstance(diff, (int, float)) and not pd.isna(diff) else f"{diff}"
    else:
        delta_text = f"{icon} {diff:+.0f}" if isinstance(diff, (int, float)) and not pd.isna(diff) else f"{diff}"
        if pct_change is not None and not pd.isna(pct_change):
            delta_text += f" ({pct_change:+.1f}%)" if isinstance(pct_change, (int, float)) else f" ({pct_change})"

    # Formatar valores para exibição se forem numéricos
    def formatar_valor(val):
        if isinstance(val, (int, float)):
            if pd.isna(val):
                return "-"
            if int(val) == val:
                return f"{int(val):,}".replace(",", ".")
            return f"{val:.1f}%" if is_percentage else f"{val:.1f}"
        return str(val)

    val_at_str = formatar_valor(val_atual)
    val_ant_str = formatar_valor(val_anterior)

    card_html = f"""
    <div style="
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -1px rgba(0, 0, 0, 0.04);
        border-left: 5px solid {border_color};
        margin: 8px 0px;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        border-top: 1px solid #F3F4F6;
        border-right: 1px solid #F3F4F6;
        border-bottom: 1px solid #F3F4F6;
    ">
        <div>
            <div style="font-size: 11px; color: #6B7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">{title}</div>
            <div style="font-size: 15px; color: #111827; font-weight: 700; margin-bottom: 4px;">{label_atual}: <span style="font-size: 18px; font-weight: 800;">{val_at_str}</span></div>
            <div style="font-size: 13px; color: #6B7280; font-weight: 500;">{label_anterior}: {val_ant_str}</div>
        </div>
        <div style="color: {delta_color}; font-size: 13px; font-weight: 600; margin-top: 6px; display: flex; align-items: center;">
            Variação: {delta_text}
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


