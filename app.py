import io, json
import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

st.set_page_config(page_title="Peta Gambut Indonesia",page_icon="🌿",layout="wide")
st.markdown("<style>.block-container{padding-top:1.3rem;max-width:1500px}div[data-testid='stMetric']{background:#f4f2ef;padding:14px 16px;border-radius:14px}</style>",unsafe_allow_html=True)
st.title("Peta Gambut dan Restorasi Indonesia")
st.caption("Dashboard per provinsi berdasarkan workbook Kumpulan Data.xlsx")
REPO_API="https://api.github.com/repos/mashadinoor/Indonesia-Geojson-2026/contents/Provinsi"
@st.cache_data(ttl=86400,show_spinner="Mengunduh batas provinsi Indonesia...")
def fetch_geo():
    res=requests.get(REPO_API,timeout=30); res.raise_for_status()
    files=[x for x in res.json() if x.get("name","").lower().endswith((".json",".geojson"))]
    features=[]
    for item in files:
        r=requests.get(item["download_url"],timeout=20); r.raise_for_status(); obj=r.json()
        if obj.get("type")=="FeatureCollection": features.extend(obj.get("features",[]))
        elif obj.get("type")=="Feature": features.append(obj)
    if not features: raise ValueError("GeoJSON kosong")
    return {"type":"FeatureCollection","features":features},len(files)
def norm(x):
    if pd.isna(x): return ""
    s=str(x).strip().lower().replace("provinsi ","")
    return {"di yogyakarta":"yogyakarta","daerah istimewa yogyakarta":"yogyakarta","dki jakarta":"jakarta","kepulauan bangka belitung":"bangka belitung"}.get(s,s)
with st.sidebar:
    st.header("Data dan tampilan")
    upload=st.file_uploader("Unggah workbook gambut (.xlsx)",type=["xlsx"])
    metric=st.selectbox("Indikator tinggi 3D",["Luas_Gambut_Ha","Jumlah_KHG","Jumlah_APTMAT","Total_Program_Tercatat"],format_func=lambda x:{"Luas_Gambut_Ha":"Luas gambut (ha)","Jumlah_KHG":"Jumlah KHG","Jumlah_APTMAT":"Jumlah APTMAT","Total_Program_Tercatat":"Catatan program restorasi"}[x])
    scale=st.slider("Skala tinggi peta",100,10000,1800,100)
if upload: data=io.BytesIO(upload.getvalue())
else:
    try: data=open("Data_Gambut_dan_Restorasi_per_Provinsi.xlsx","rb")
    except FileNotFoundError: st.error("Unggah workbook Excel dari paket atau letakkan file ringkasan di folder aplikasi."); st.stop()
try: df=pd.read_excel(data,sheet_name="Ringkasan per Provinsi")
except Exception as e: st.error("Excel harus memiliki sheet 'Ringkasan per Provinsi'. "+str(e)); st.stop()
cols=["Luas_Gambut_Ha","Jumlah_KHG","Jumlah_APTMAT","Program_Revitalisasi","Infrastruktur_Restorasi","Demplot_Revegetasi","DMPG_2022","DMPG_2023","Total_Program_Tercatat"]
for c in cols:
    if c not in df: df[c]=0
    df[c]=pd.to_numeric(df[c],errors="coerce").fillna(0)
a,b,c,d=st.columns(4)
a.metric("Luas gambut terdata",f"{df.Luas_Gambut_Ha.sum()/1e6:,.2f} juta ha")
b.metric("Jumlah KHG",f"{int(df.Jumlah_KHG.sum()):,}")
c.metric("Catatan APTMAT",f"{int(df.Jumlah_APTMAT.sum()):,}")
d.metric("Catatan program restorasi",f"{int(df.Total_Program_Tercatat.sum()):,}")
left,right=st.columns([1.8,1])
with left:
    st.subheader("Peta 3D Indonesia")
    try:
        geo,nfiles=fetch_geo(); lookup={norm(r.Provinsi):r for _,r in df.iterrows()}
        for feat in geo["features"]:
            p=feat.setdefault("properties",{})
            keys=["name","NAME","Provinsi","provinsi","PROVINSI","Propinsi","NAME_1","PROVINSI_N","NAME_ENG"]
            name=next((p.get(k) for k in keys if p.get(k)),None); row=lookup.get(norm(name)) if name else None
            p["provinsi_label"]=str(name or "Provinsi")
            val=float(row[metric]) if row is not None else 0
            p["elevation"]=max(val,0)**0.5*scale if metric=="Luas_Gambut_Ha" else max(val,0)*scale
            p["area_tip"]=f'{row["Luas_Gambut_Ha"]:,.0f} ha' if row is not None else "Tidak ada data"
            p["khg_tip"]=str(int(row["Jumlah_KHG"])) if row is not None else "—"
            p["apt_tip"]=str(int(row["Jumlah_APTMAT"])) if row is not None else "—"
            p["program_tip"]=str(int(row["Total_Program_Tercatat"])) if row is not None else "—"
        layer=pdk.Layer("GeoJsonLayer",data=geo,pickable=True,stroked=True,filled=True,extruded=True,wireframe=True,get_elevation="properties.elevation",get_fill_color=[190,205,185,240],get_line_color=[255,255,255,220],line_width_min_pixels=1,auto_highlight=True)
        deck=pdk.Deck(layers=[layer],initial_view_state=pdk.ViewState(latitude=-2.5,longitude=118,zoom=3,pitch=48,bearing=0),tooltip={"html":"<b>{provinsi_label}</b><br/>Luas gambut: {area_tip}<br/>Jumlah KHG: {khg_tip}<br/>APTMAT: {apt_tip}<br/>Catatan program: {program_tip}","style":{"backgroundColor":"#242424","color":"white"}})
        st.pydeck_chart(deck,use_container_width=True); st.caption(f"GeoJSON dimuat dari repositori publik; {nfiles} file sumber terdeteksi.")
    except Exception as e:
        st.error("Peta gagal dimuat. Pastikan koneksi internet aktif dan akses GitHub tidak diblokir."); st.caption(str(e))
with right:
    st.subheader("Provinsi dengan luas gambut terbesar")
    top=df.sort_values("Luas_Gambut_Ha",ascending=False).head(5); maxv=top.Luas_Gambut_Ha.max()
    for i,(_,r) in enumerate(top.iterrows(),1):
        st.markdown(f"**{i}. {r.Provinsi}**"); st.caption(f'{r.Luas_Gambut_Ha:,.0f} ha · {int(r.Jumlah_KHG)} KHG')
        st.progress(float(r.Luas_Gambut_Ha/maxv) if maxv else 0)
    st.divider(); selected=st.selectbox("Detail provinsi",sorted(df.Provinsi.astype(str).unique())); r=df[df.Provinsi.astype(str)==selected].iloc[0]
    st.markdown(f"### {selected}"); st.metric("Luas gambut",f'{r.Luas_Gambut_Ha:,.0f} ha')
    x,y=st.columns(2); x.metric("Jumlah KHG",int(r.Jumlah_KHG)); y.metric("APTMAT",int(r.Jumlah_APTMAT))
    for label,col in [("Revitalisasi","Program_Revitalisasi"),("Infrastruktur","Infrastruktur_Restorasi"),("Demplot revegetasi","Demplot_Revegetasi"),("DMPG 2022","DMPG_2022"),("DMPG 2023","DMPG_2023")]: st.write(f"- {label}: {int(r[col])}")
st.divider(); st.subheader("Ringkasan per provinsi")
show=["Provinsi","Luas_Gambut_Ha","Jumlah_KHG","Jumlah_APTMAT","Program_Revitalisasi","Infrastruktur_Restorasi","Demplot_Revegetasi","DMPG_2022","DMPG_2023"]
st.dataframe(df[show].sort_values("Luas_Gambut_Ha",ascending=False),use_container_width=True,hide_index=True)
st.download_button("Unduh ringkasan CSV",df.to_csv(index=False).encode("utf-8-sig"),"ringkasan_gambut_per_provinsi.csv","text/csv")
st.caption("Sumber: workbook pengguna. Jumlah catatan tidak otomatis sama dengan jumlah lokasi unik; periksa sheet Definisi Data sebelum publikasi.")
