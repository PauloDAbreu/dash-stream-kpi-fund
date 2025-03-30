import pandas as pd
import streamlit as st
import yfinance as yf
import fundamentus as fd
from datetime import timedelta
import math

@st.cache_data
def carregar_tickers_acoes():
    base_tickers = pd.read_csv("IBOV.CSV", sep=";")
    tickers = list(base_tickers['Código'])
    tickers = [item + ".SA" for item in tickers]
    return tickers

#P/L
@st.cache_data
def carregar_dados(empresas):
    resultados = {}
    
    for empresa in empresas:
        try:
            # Cria o objeto de ação
            dados_acao = yf.Ticker(empresa)
            
            # Tenta acessar as informações da ação
            info_acao = dados_acao.info
            if info_acao is None:
                st.warning(f"Informações não encontradas para a ação {empresa}.")
                resultados[empresa] = None
                continue  # Pula para a próxima ação

            # Verificar se o EPS está disponível
            eps = info_acao.get("trailingEps", None)
            if eps is None:
                st.warning(f"EPS não disponível para a ação {empresa}.")
                resultados[empresa] = None
                continue

            # Tenta obter a cotação mais recente
            cotacao_acao = dados_acao.history(period="1mo")
            if cotacao_acao.empty:
                #st.warning(f"Sem dados de cotação para a ação {empresa}.")
                cotacao_acao = None
            else:
                cotacao_acao = cotacao_acao["Close"].iloc[-1]  # Último preço de fechamento

            # Calcular o P/L (Preço/Lucro), se os dados existirem
            pl_ratio = cotacao_acao / eps if cotacao_acao and eps else None
            resultados[empresa] = pl_ratio

        except Exception as e:
            # Se ocorrer qualquer erro, exibe uma mensagem no Streamlit
            st.error(f"Erro ao acessar os dados da ação {empresa}: {e}")
            resultados[empresa] = None  # Retorna None se ocorrer algum erro

    return resultados  # Retorna um dicionário com o P/L ou None para cada ação 

@st.cache_data
def carregar_preco(empresas):
    texto_tickers = " ".join(empresas)
    dados_açoes = yf.Tickers(texto_tickers)
    precos_acao = dados_açoes.history(period='1d', start='2000-01-01')
    print(precos_acao)
    precos_acao = precos_acao["Close"]
    return precos_acao

#dividend yield
@st.cache_data
def carregar_dy(empresas):
    resultados = {}
    for empresa in empresas:
        acao = yf.Ticker(empresa)
        dados = acao.info

        dividend_rate = dados.get('dividendRate', 0)
        current_price = dados.get('currentPrice', 0)

        if current_price > 0:
            dividend_yield = (dividend_rate / current_price) * 100
        else:
            dividend_yield = None

        resultados[empresa] = dividend_yield  # Salva os resultados por empresa

    return resultados  # Retorna um dicionário com os dividend yields

@st.cache_data
def carregar_ebitda(empresas):
    resultado = {}

    for empresa in empresas:
        acao = yf.Ticker(empresa)
        dados = acao.info

        total_revenue = dados.get('totalRevenue')
        ebitda_margins = dados.get('ebitdaMargins')

        print(f"{empresa} -> Receita Total: {total_revenue}, Margem EBITDA: {ebitda_margins}")  # Debug

        if total_revenue and ebitda_margins:
            ebitda = total_revenue * ebitda_margins
        else:
            ebitda = None

        resultado[empresa] = ebitda

    return resultado

@st.cache_data
def carregar_graham(empresas):
    dados_graham = {}

    for empresa in empresas:
        acao = yf.Ticker(empresa)
        dados_historicos = acao.history(period='1d', start='2000-01-01')
        info = acao.info

        eps = info.get('trailingEps', 0)
        bv = info.get('bookValue', 0)

        # Verifica se os valores são válidos
        if isinstance(eps, (int, float)) and isinstance(bv, (int, float)) and eps > 0 and bv > 0:
            graham = math.sqrt(22.5 * eps * bv)
            
            # Adiciona a coluna "Graham" se houver dados históricos
            if not dados_historicos.empty:
                dados_historicos = dados_historicos.copy()  # Evita Warning ao modificar cópia
                dados_historicos["Graham"] = graham
                
                # Certifica-se de que a coluna "Close" existe antes de selecionar
                colunas_disponiveis = [col for col in ["Close", "Graham"] if col in dados_historicos.columns]
                
                if colunas_disponiveis:
                    dados_graham[empresa] = dados_historicos[colunas_disponiveis]

    return dados_graham


lista_acoes = carregar_tickers_acoes()
dados = carregar_dados(lista_acoes)
dados_preco = carregar_preco(lista_acoes)
dados_dy = carregar_dy(lista_acoes)
dados_ebitda = carregar_dados(lista_acoes)
dados_b_graham = carregar_graham(lista_acoes)


st.write("""
# Indicadores Fundamentalistas
###### Indicadores fundamentalistas são métricas utilizadas para avaliar a saúde financeira e o valor de uma empresa. Eles ajudam a identificar boas oportunidades de investimento ao analisar seus fundamentos e desempenho econômico.         
""")#markdown

#Filtros
st.sidebar.header("Filtros")

lista_acoes_sct = st.sidebar.multiselect("Escolha as ações para visualizar",dados_preco.columns)
if lista_acoes_sct:
   dados_preco = dados_preco[lista_acoes_sct]
   if len(lista_acoes_sct)==1:
    acao_unica = lista_acoes_sct[0]
    dados_preco = dados_preco.rename(columns = {acao_unica:"Close"})

if lista_acoes_sct:
    dados = {acao: dados[acao] for acao in lista_acoes_sct if acao in dados}

if lista_acoes_sct:
    dados_dy = {acao: dados_dy[acao] for acao in lista_acoes_sct if acao in dados_dy}

if lista_acoes_sct:
    dados_ebitda = {acao: dados_ebitda[acao] for acao in lista_acoes_sct if acao in dados_ebitda}

if lista_acoes_sct:
    dados_b_graham = {acao: dados_b_graham[acao] for acao in lista_acoes_sct if acao in dados_b_graham}
   
#filtro datas
data_inicial = dados_preco.index.min().to_pydatetime()
data_final = dados_preco.index.max().to_pydatetime()
intervalo_data = st.sidebar.slider("Selecione o período", min_value=data_inicial, max_value=data_final, value=(data_final,data_final),step=timedelta(days=1))
#print(lista_acoes_sct)
#print(dados)
print(intervalo_data[1])
dados_preco = dados_preco.loc[intervalo_data[0]:intervalo_data[1]]

# Remover qualquer informação de fuso horário
dados_preco.index = dados_preco.index.tz_localize(None)

# Converter intervalo de data para tz-naive
intervalo_data = (intervalo_data[0].replace(tzinfo=None), intervalo_data[1].replace(tzinfo=None))

# Aplicar o filtro de data em todos os dados
dados_preco = dados_preco.loc[intervalo_data[0]:intervalo_data[1]]

for acao in lista_acoes_sct:
    if acao in dados_b_graham:
        dados_acao = dados_b_graham[acao]
        if not dados_acao.empty:
            # Remover qualquer informação de fuso horário antes de aplicar o filtro
            dados_acao.index = dados_acao.index.tz_localize(None)
            dados_b_graham[acao] = dados_acao.loc[intervalo_data[0]:intervalo_data[1]]
             
            

st.write("""
## Evolução do Preço de Ações 
""")
st.line_chart(dados_preco)

st.write("""
## Indice P/L (Preço / Lucro)
###### Um P/L alto pode apontar para o fato de que o mercado está disposto a pagar mais pelos lucros da empresa, especialmente se tiver expectativas de crescimento.         
""")

#criar o card
for acao, pl in dados.items():
    st.metric(label=f"📊 Índice P/L - {acao}", value=f"{pl:.2f}%" if pl else "N/A")

st.write("""
## DY (Dividend Yield)
###### Dividend Yield (DY) é um índice que mede a rentabilidade dos dividendos de uma empresa em relação ao preço de suas ações. É uma métrica que ajuda a avaliar a performance de uma empresa e a prever os dividendos que ela pagará no futuro. 
""")
for acao, pl in dados_dy.items():
    st.metric(label=f"📊 Índice P/L - {acao}", value=f"{pl:.2f}%" if pl else "N/A")

st.write("""
## EBITDA 
###### EBITDA é um indicador financeiro que calcula o lucro de uma empresa antes de descontar juros, impostos, depreciação e amortização. A sigla vem do inglês Earnings Before Interest, Taxes, Depreciation and Amortization.          
""")
for acao, ebt in dados_ebitda.items():
    st.metric(label=f"📊 Índice P/L - {acao}", value=f"{ebt:.2f}%" if ebt else "N/A")

st.write("""
## Metodo de Graham
###### O Método de Graham é uma abordagem de avaliação de ações que busca identificar empresas subvalorizadas, comparando o preço de mercado com o valor intrínseco calculado com base em fundamentos sólidos
###### Quando o preço da ação está acima do valor intrínseco, ela é sobrevalorizada, indicando risco de queda. Quando está abaixo, a ação é subvalorizada, representando uma oportunidade de compra com potencial de valorização.
""")

if lista_acoes_sct:
    for acao in lista_acoes_sct:
        if acao in dados_b_graham:
            dados_acao = dados_b_graham[acao]
            if not dados_acao.empty:
                st.line_chart(dados_acao)
            else:
                st.warning(f"Sem dados suficientes para {acao}.")
else:
    st.warning("Selecione ao menos uma ação para visualizar o gráfico.")


