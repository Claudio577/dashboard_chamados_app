# 📊 Dashboard Executivo de Chamados (Estilo Power BI)

Este é um sistema desenvolvido em Python e **Streamlit** com interface executiva profissional para processamento, tratamento de dados e visualização de indicadores operacionais de chamados. A solução é estruturada em módulos, garantindo consistência matemática e visualização limpa e premium.

## 🚀 Funcionalidades

- **Upload de Planilha:** Leitura nativa de arquivos `.xlsx`, `.xls`, `.xlsm` e `.csv`.
- **Base Tratada Única:** Todo o processamento de dados é executado em uma base limpa antes da renderização para garantir consistência perfeita entre cartões e gráficos.
- **Filtros Globais:** Barra lateral com filtros interativos de Cliente, Categoria, Solicitação, Responsável, Status SLA, Status 72h e Período de abertura.
- **Abas Temáticas:**
  1. **Visão Executiva:** Indicadores principais (KPIs) com cartões estilizados em CSS e gráficos de rosca/barras do Plotly.
  2. **Comparação Mensal:** Comparativos com deltas numéricos e percentuais dinâmicos, gráficos agrupados e análise automática consolidada (melhoras, pioras e pontos de atenção).
  3. **Atendimento por Responsável:** Tabela de analistas, distribuição de produtividade e ranking de qualidade (SLA %) filtrado para profissionais com no mínimo 5 chamados finalizados.
  4. **Clientes e Categorias:** Detalhes de volume por clientes, solicitações e identificação de causas de estouro de SLA e atrasos.
  5. **Qualidade da Base (Auditoria):** Quadro para identificar registros sem cliente, sem datas ou sem responsável na planilha bruta e reconciliação matemática entre base filtrada e resumos.
  6. **Base Analítica:** Tabela tratada final e exportador completo formatado em múltiplas abas de Excel.

---

## 📐 Regras de Negócio e Cálculos

### 1. Status SLA
- **Em aberto / Em tratamento:** Chamados onde a data de `Encerramento` está vazia.
- **SLA não informado:** Chamados onde o `Encerramento` está preenchido, mas o `Vencimento` (SLA original) está vazio.
- **Dentro do SLA:** Chamados encerrados dentro do prazo (`Encerramento` <= `Vencimento`).
- **Fora do SLA:** Chamados encerrados após o prazo (`Encerramento` > `Vencimento`).

### 2. Status 72 Horas
- **Em aberto / Em tratamento:** Chamados sem `Encerramento`.
- **72h não informado:** Chamados com `Encerramento` preenchido, mas sem `Abertura`.
- **Tratado até 72h:** Chamados com tempo entre `Abertura` e `Encerramento` menor ou igual a 72 horas.
- **Tratado acima de 72h:** Chamados com tempo maior que 72 horas.

### 3. Normalização de Clientes (Regra Especial CBLOC)
- Se a coluna `De` contiver `"CBLOC"`, é consolidado como `CBLOC BRASIL LOCAÇÃO DE EQUIPAMENTOS LTDA`.
- Se a coluna de Empresa contiver `"CBLOC"` mas a coluna `De` contiver `"Casa do Construtor"`, o chamado é consolidado sob o cliente `CASA DO CONSTRUTOR`.

### 4. Responsável e Finalizador
- O sistema varre e prioriza colunas de finalização específica (`Finalizado por`, `Encerrado por`, `Atendente finalizador`). Se ausente, usa as colunas gerais de atendimento (`Responsável`, `Atendente`, `Analista`) e exibe uma notificação amigável sobre a aproximação utilizada.

---

## 📂 Estrutura Modular

- `app.py`: Arquivo central que gerencia filtros laterais, lógica de sessão e renderiza as abas.
- `utils/data_processing.py`: Algoritmos de limpeza, tratamento de data, mapeamento de colunas, indicadores e normalizações.
- `utils/charts.py`: Biblioteca de gráficos Plotly configurados com paleta de cores corporativa.
- `utils/ui_components.py`: Folha de estilo CSS e blocos HTML customizados para cartões de KPI.
- `utils/export_excel.py`: Motor de exportação que consolida as bases tratadas em um arquivo Excel multi-aba de forma consistente.

---

## 💻 Como Rodar Localmente

1. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Execute o Streamlit:**
   ```bash
   streamlit run app.py
   ```
