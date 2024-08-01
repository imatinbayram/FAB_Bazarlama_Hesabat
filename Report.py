import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

#Hesabata daxil olan aylar
hesabat_aylar = ['Yanvar','Fevral','Mart','Aprel','May','İyun']

#Sehifenin nastroykasi
st.set_page_config(
    page_title='FAB Bazarlama Hesabat',
    page_icon='logo.png',
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# FAB Bazarlama \n Bu hesabat FAB şirkətlər qrupunun Bazarlama bölməsi üçün hazırlanmışdır."
    }
)

#Excel melumati oxuyuruq
@st.cache_data
def load_data():
    data = pd.read_excel('BazarlamaData.xlsx')
    mallar = pd.read_excel('Mallar.xlsx')
    return data, mallar

#Melumat yenilemek ucun knopka
res_button = st.sidebar.button(':red[🗘 Məlumatları Yenilə]')
if res_button:
    st.cache_data.clear()
with st.spinner('Məlumatlar yüklənir...'):
    data, mallar = load_data()

#Bolgelerin, qollarin, bolgeye gore carilerin adini gotururuk
group_list = data['GROUP'].unique()
qol_list = mallar['QOL'].unique()
group_cari_ad = dict()
for group in group_list:
    cari_ad = data[data['GROUP'] == group]['C_AD'].unique().tolist()
    group_cari_ad[group] = cari_ad

#Cəmi sütünun yaradılması
data['CƏMİ'] = data[hesabat_aylar].sum(axis=1)


#sidebar secimleri
SELECT_GROUP = st.sidebar.selectbox('Bölgə', sorted(group_list),
                                    label_visibility='visible')
SELECT_S_AD = st.sidebar.selectbox('Müştəri adı',
                                   sorted(group_cari_ad[SELECT_GROUP]),
                                   label_visibility='visible')
SELECT_QOL = st.sidebar.selectbox('Satış qolu', qol_list,
                                  label_visibility='visible')
TOP_NUMBER = st.sidebar.slider('TOP satılan mallar', 0, 500, 250, 50)

# TOP satış mallarinin siyahisi
top_sales_products = data.groupby('S_KOD')['CƏMİ'].sum().reset_index()
top_sales_products = top_sales_products.sort_values(by='CƏMİ', ascending=False)
top_sales_products_list = top_sales_products.iloc[:TOP_NUMBER, 0].tolist()

#Sehifenin adini tablari duzeldirik
st.header(f'{SELECT_GROUP} - {SELECT_S_AD} -  {SELECT_QOL}', divider='rainbow', anchor=False)
tab2, tab1 = st.tabs([':file_folder: Qollar üzrə mallar',':file_folder: Bütün satdığı mallar'])

#sidebara gore umumi cedvelin yaradilmasi
select_data = data[(data['GROUP']==SELECT_GROUP) & (data['C_AD']==SELECT_S_AD)]
filter_data_all_column = select_data.drop(['GROUP','C_KOD','C_AD','S_AD'], axis=1)
#filter_data aylari gosterib gostermemeye gore uygunlasdiririq
show_aylar = st.sidebar.checkbox("Ancaq :red[CƏMİ] göstər")
if show_aylar:
    filter_data = filter_data_all_column.drop(hesabat_aylar, axis=1)
else:
    filter_data = filter_data_all_column
    
filter_data.index = np.arange(1, len(filter_data)+1)

#sidebara gore secilen mallarin excelini yaradiqi
secilmis_mallar = pd.merge(mallar, filter_data, on='S_KOD', how='left')
secilmis_mallar.fillna(0, inplace=True)
secilmis_mallar = secilmis_mallar[secilmis_mallar['QOL']==SELECT_QOL]
secilmis_mallar.index = np.arange(1, len(secilmis_mallar)+1)

#Tab2 gosterilmesi
#filter_data aylari gosterib gostermemeye gore uygunlasdiririq
filter_secilmis_radio_options = {
    'Bütün': 0,
    'Satılan': 1,
    'Satılmayan': 2,
    ':red[TOP] Satılan': 3,
    ':red[TOP] Satılmayan': 4
}
filter_secilmis_radio_select = tab2.radio(
    label = '',
    label_visibility = 'collapsed',
    options = list(filter_secilmis_radio_options.keys()),
    horizontal = True
)

if filter_secilmis_radio_options[filter_secilmis_radio_select] == 0:
    secilmis_mallar = secilmis_mallar
elif filter_secilmis_radio_options[filter_secilmis_radio_select] == 1:
    secilmis_mallar = secilmis_mallar[secilmis_mallar['CƏMİ']>0]
elif filter_secilmis_radio_options[filter_secilmis_radio_select] == 2:
    secilmis_mallar = secilmis_mallar[secilmis_mallar['CƏMİ']<=0]
elif filter_secilmis_radio_options[filter_secilmis_radio_select] == 3:
        secilmis_mallar = secilmis_mallar[(secilmis_mallar['CƏMİ']>0) & (secilmis_mallar['S_KOD'].isin(top_sales_products_list))]
elif filter_secilmis_radio_options[filter_secilmis_radio_select] == 4:
        secilmis_mallar = secilmis_mallar[(secilmis_mallar['CƏMİ']<=0) & (secilmis_mallar['S_KOD'].isin(top_sales_products_list))]
secilmis_mallar.index = np.arange(1, len(secilmis_mallar)+1)

# Cedvelin reqemlerini formatini duzeltmek ucun
def accounting_format(x):
    if x == 0:
        return ' '
    else:
        return f'{x:,.0f}'.replace(',', ' ')

# Cedvele formati tetbiq edib yeni styled_filter_data yaradiriq
styled1_filter_data = filter_data.style.format({ay: accounting_format for ay in hesabat_aylar})
styled1_secilmis_mallar = secilmis_mallar.style.format({ay: accounting_format for ay in hesabat_aylar})

# TOP satilan mallari sari elemek ucun funksiya
def top_sold_color(row):
    if row['CƏMİ'] < 0:
        return ['background-color: green; color:red' if row['S_KOD'] in top_sales_products_list else 'color:red' for _ in row]
    else:
        return ['background-color: green' if row['S_KOD'] in top_sales_products_list else '' for _ in row]

#funksiyani tetbiq edirik
styled_filter_data = styled1_filter_data.apply(top_sold_color, axis=1)
styled_secilmis_mallar = styled1_secilmis_mallar.apply(top_sold_color, axis=1)

#Fayli excele yuklemek
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    styled_secilmis_mallar.to_excel(writer, index=False, sheet_name='Hesabat')
excel_data = output.getvalue()
tab2.download_button(
    label=":green[Cədvəli Excel'ə yüklə] :floppy_disk:",
    data=excel_data,
    file_name=f'{SELECT_GROUP} - {SELECT_S_AD} - {SELECT_QOL}.xlsx',
)

#Tablarda dizayn olunmus cedvellerin gosterilmesi
tab1.table(styled_filter_data)
tab2.table(styled_secilmis_mallar)

_comment = '''
#DataFrame olsa download knopkasini yoxa cixardiriq
st.markdown(
    """
    <style>
    [data-testid="stElementToolbar"] {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)
'''

css_slider_hide_number = """
<style>
    .stSlider [data-testid="stTickBar"] {
        display: none;
    }
    .stSlider label {
        display: block;
        text-align: left;
    }
    
    .stSelectbox label {
        text-align: left;
        display: block;
        width: 100%;
    }

    [data-testid="stHeader"] {
        display: none;
    }
    
    [class="viewerBadge_container__r5tak"] {
        display: none;
    }
</style>
"""

st.markdown(css_slider_hide_number, unsafe_allow_html=True)