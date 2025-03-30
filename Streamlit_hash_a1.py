#importar as bibliotecas
import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import timedelta

#criar funçoes de carregamentos de dados
    #cotações do itau
@st.cache_data
def carregar_dados(empresas):
    texto_tickers = " ".join(empresas) #vai juntar as empresas e separar por um espaço como separador" "
    dados_acao = yf.Tickers(texto_tickers)
    cotacao_acao = dados_acao.history(period="1d", start="2010-01-01", end="2025-01-01")
    print(cotacao_acao)
    cotacao_acao = cotacao_acao['Close']
    return cotacao_acao

@st.cache_data
def carregar_tickers_acoes():
    base_tickers = pd.read_csv("IBOV.csv", sep=";")
    tickers = list(base_tickers["Código"])
    tickers = [item + ".SA" for item in tickers]
    return tickers


acoes = carregar_tickers_acoes()
dados = carregar_dados(acoes)


# criar a interface do streamlit

st.write("""
# App Preço de Ações
O gráfico abaixo representa a evolução do preço das ações ao longo dos anos
""")#markdown

#preparar as visualizações - filtros
st.sidebar.header("Filtros")

#filtro de acoes
lista_ac_sel = st.sidebar.multiselect("Escolha as ações para visualizar",dados.columns)
#print(lista_ac_sel)
if lista_ac_sel:
    dados = dados[lista_ac_sel]
    if len(lista_ac_sel)==1:
       acao_unica= lista_ac_sel[0]
       dados = dados.rename(columns = {acao_unica: "Close"})  

#filtro de datas
data_inicial = dados.index.min().to_pydatetime()
data_final = dados.index.max().to_pydatetime()
intervalo_data = st.sidebar.slider("Seleciono o periodo", min_value= data_inicial, max_value= data_final, value=(data_inicial, data_final),step=timedelta(days=1))    
print(intervalo_data[1])
#filtro da tabela
dados = dados.loc[intervalo_data[0]:intervalo_data[1]]


#Criar grafico
st.line_chart(dados)

#calculo de performance
texto_performance_ativos = ""

if len(lista_ac_sel)==0:
    lista_ac_sel = list(dados)
if len(lista_ac_sel)==1:
    dados = dados.rename(columns = {"Close": acao_unica})

carteira = [1000 for acao in lista_ac_sel]
total_inicial_carteira = sum(carteira)

for i, acao in enumerate(lista_ac_sel):
    performance_ativo = dados[acao].iloc[-1] / dados[acao].iloc[0] - 1
    performance_ativo = float(performance_ativo)

    carteira[i] = carteira[i] * (1 + performance_ativo)
   
    if performance_ativo > 0: 
        #:cor[texto]
        texto_performance_ativos = texto_performance_ativos + f"  \n{acao}: :green[{performance_ativo:.2%}]"
    elif performance_ativo <0:
        texto_performance_ativos = texto_performance_ativos + f"  \n{acao}: :red[{performance_ativo:.2%}]"
    else:
        texto_performance_ativos = texto_performance_ativos + f"  \n{acao}: :yellow[{performance_ativo:.2%}]"

total_final_carteira = sum(carteira)
perfomance_carteira = total_final_carteira / total_inicial_carteira - 1        

if perfomance_carteira > 0: 
        #:cor[texto]
    texto_performance_carteira = f"Performance da carteira com todos os ativos: :green[{perfomance_carteira:.2%}]"
elif performance_ativo <0:
    texto_performance_carteira = f"Performance da carteira com todos os ativos: :red[{perfomance_carteira:.2%}]"
else:
    texto_performance_carteira = f"Performance da carteira com todos os ativos: :yellow[{perfomance_carteira:.2%}]"


st.write(F"""
### Performance
Essa foi a perfomance de cada ativo no período selecionado:
         
{texto_performance_ativos}


{texto_performance_carteira}
""")#markdown



