#no terminal (ctrl+j) executar: streamlit run .\mombak_imovel.py



#BIBLIOTECAS
#conexão com o 'site'
import streamlit as st #framework de desenvolvimento de dashboards interativos
#manuseio de geo arquivos
import geopandas as gpd
import pandas as pd
#criar gráficos
import plotly.express as px
#biblioteca de confecção de mapas
import folium
#criar mapas com o streamlit
from streamlit_folium import folium_static #integra o streamlit com o folium
#manipulação de nomes de arquivos
import os


#adicionar um titulo nível 1
st.title('Análise do Imóvel')
#adicionar um titulo nínel 3 (para nível 2, basta digitar st.header)
#adicionar uma barra lateral
st.sidebar.title('Menu')



#adicionando uma caixa para upload do shp. Porém estou adicionando essa caixa dentro da sidebar
arquivo_subido = st.sidebar.file_uploader('Selecione seu shp') #*se for um shp, precisa estar zipado* #SRC SIRGAS 2000



#Como será selecionado o meu tipo de visualização? radio: aparecem todas as opções para o usuário escolher / selectbox: precisa clicar em uma caixa para ver as opções
elemento= st.sidebar.radio('Selecione o elemento a ser visualizado',
                                    options=['Mapa', 'Resumo', 'Cabeçalho', 'Gráfico'])



#checagem para saber se o arquivo foi subido, se não foi, não aparece a mensagem de erro e sim, um pequeno aviso
if arquivo_subido:

    # Extrai o nome do arquivo sem a extensão para usar no subheader
    nome_arquivo = os.path.splitext(arquivo_subido.name)[0]
    st.subheader(nome_arquivo)  # Nome dinâmico baseado no arquivo carregado
    
    #salvando o arquivo anterior em geodataframe
    gdf = gpd.read_file(arquivo_subido)
    

    #conversão do geodataframe em dataframe
    #removendo a coluna de geometria, pois não é necessária e é muito pesada
    df = pd.DataFrame(gdf).drop(columns=['geometry'])
    
    
    #plotando a tabela de atributos do shp no 'site'
    #st.write(gdf)

    #inserir planilha com resumo estatístico
    #st.write(gdf.describe())



    #CADA ELEMENTO NA TELA, FOI ORGANIZADO EM FUNÇÕES PARA FACILITAR O MANUSEIO POSTERIORMENTE.
    def resumo():
        # Verifica colunas necessárias
        area_col = 'AreaHa'
        class_col = 'Classe'
        
        if area_col in gdf.columns and class_col in gdf.columns:
            total_ha = gdf[area_col].sum()
            
            # TABELA 1: DISTRIBUIÇÃO POR CLASSE (nova primeira tabela)
            st.subheader("Fine Scale Mapping")
            
            # Agrupa por classe e soma a área
            classe_area = gdf.groupby(class_col)[area_col].sum().reset_index()
            classe_area['% do Total'] = (classe_area[area_col] / total_ha) * 100
            
            # Ordena do maior para o menor
            classe_area = classe_area.sort_values(by=area_col, ascending=False)
            
            # Adiciona linha de total
            total_row = pd.DataFrame({
                class_col: ['TOTAL'],
                area_col: [total_ha],
                '% do Total': [100]
            })
            classe_area = pd.concat([classe_area, total_row], ignore_index=True)
            
            # Exibindo a tabela
            st.dataframe(
                classe_area.style.format({
                    area_col: '{:,.2f}',
                    '% do Total': '{:.2f}%'
                }),
                height=min(400, 150 + len(classe_area) * 35)
            )
            
            
            # TABELA 2: RESUMO (segunda tabela)
            st.subheader("Resumo")
            
            # Cálculo das estatísticas
            classes_1 = gdf[gdf[class_col].astype(str).str.startswith('1')]
            classes_0 = gdf[gdf[class_col].astype(str).str.startswith('0')]
            
            total_ha_1 = classes_1[area_col].sum()
            total_ha_0 = classes_0[area_col].sum()
            
            # Criando DataFrame de resumo
            resumo_ha = pd.DataFrame({
                'Categoria': ['Área de Projeto', 'Fora do Projeto', 'Total'],
                'Área (ha)': [total_ha_1, total_ha_0, total_ha],
                '% do Total': [
                    (total_ha_1/total_ha)*100 if total_ha > 0 else 0,
                    (total_ha_0/total_ha)*100 if total_ha > 0 else 0,
                    100
                ]
            })
            
            # Exibindo a tabela de resumo
            st.dataframe(
                resumo_ha.style.format({'Área (ha)': '{:,.2f}', '% do Total': '{:.2f}%'}),
                height=150
            )
            
            # Linha divisória
            st.divider()
            
            # TABELA 3: ÁREAS INELEGÍVEIS (terceira tabela)
            st.subheader("Áreas Inelegíveis")
            
            if 'inel_stats' in gdf.columns:
                # Filtra áreas inelegíveis
                inelegiveis = gdf[gdf['inel_stats'].notna()]
                
                if not inelegiveis.empty:
                    # Calcula totais por categoria
                    verra = inelegiveis[inelegiveis['inel_stats'].str.lower() == 'verra'][area_col].sum()
                    juquira = inelegiveis[inelegiveis['inel_stats'].str.lower() == 'juquira'][area_col].sum()
                    total_inelegiveis = inelegiveis[area_col].sum()
                    
                    # Criando DataFrame
                    resumo_inelegiveis = pd.DataFrame({
                        'Tipo': ['Verra', 'Semas', 'Total Inelegível'],
                        'Área (ha)': [verra, juquira, total_inelegiveis],
                        '% do Total': [
                            (verra/total_inelegiveis)*100 if total_inelegiveis > 0 else 0,
                            (juquira/total_inelegiveis)*100 if total_inelegiveis > 0 else 0,
                            100
                        ]
                    })
                    
                    st.dataframe(
                        resumo_inelegiveis.style.format({'Área (ha)': '{:,.2f}', '% do Total': '{:.2f}%'}),
                        height=150
                    )
                else:
                    st.warning("Nenhuma área inelegível encontrada")
            else:
                st.warning("Coluna 'inel_stats' não encontrada")
            
            
            
            # TABELA 4: DADOS BRUTOS (última tabela)
            st.subheader("Dados Brutos")
            st.dataframe(gdf, height=320)
        
        else:
            st.warning(f"Colunas básicas não encontradas: {area_col} e {class_col}") 

    

    def cabecalho ():
        #convertendo o gdf em apenas df (data frame, ou seja, não precisa das informações de geometria). Fizemos isso pois ao trabalhar com gráficos, o PANDAS tem funções melhores que o GEO PANDAS
        st.dataframe(df)



    def grafico ():
        #criando os dois grupos de informações (eixo x e y) que serão usados no gráfico
        col1_gra, col2_gra, col3_gra = st.columns(3)

        #declarando quem serão os eixos: serão as colunas criada acima, de modo que tenha a opção do usuário selecionar qual coluna usar
        tipo_grafico = col1_gra.selectbox('Selecione o tipo de gráfico', options=['histogram', 'box', 'bar', 'line', 'scatter', 'violin'], index=0)#esse índex é para estabelecer qual será o primeiro tipo de gráfico a ser mostrado inicialmente, para não ficar mostrando algo feio ao usuário
        plot_func = getattr(px, tipo_grafico)

        #criando opções para os eixos
        x_val = col2_gra.selectbox('Selecione o eixo x', options=df.columns)
        y_val = col3_gra.selectbox('Selecione o eixo y', options=df.columns)

        #criação do gráfico
        plot = plot_func(df, x=x_val, y=y_val)#criando a plotagem
        st.plotly_chart(plot, use_container_width=True)#fazendo de fato a plotagem, pois somente agora estamos usando o streamlit

    
    
    def mapa ():
        #criando o mapa
        m = folium.Map(location=[-14,-54], zoom_start=4, control_scale=True, tiles='Esri World Imagery')

        #adicionando coisas ao mapa:
        #adicionando o gdf ao mapa
        folium.GeoJson(gdf).add_to(m)

        #identificando os limites do gdf para plotar o mapa com o melhor zoom possível
        bounds = gdf.total_bounds#calculo dos limites da shp
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])#ajusto o limite do mapa de acordo com o calculado

        #adiciono um controle de camadas
        folium.LayerControl().add_to(m)

        #plotando o mapa no 'site'
        folium_static(m, width=700, height=500)



    #condicional para mostrar os elementos na tela
    if elemento == 'Cabeçalho':
        cabecalho()
    elif elemento == 'Resumo':
        resumo()
    elif elemento == 'Gráfico':
        grafico()
    elif elemento == 'Mapa':
        mapa()



else:
    st.warning('Selecione um arquivo para iniciar o dashboard')
