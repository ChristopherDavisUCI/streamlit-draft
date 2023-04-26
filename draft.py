import streamlit as st

import pandas as pd
import altair as alt
import pickle

with open("draft-order.pickle", "rb") as f:
    draft_order = pickle.load(f)

df_pre = pd.read_csv("draft2023c.csv")
df_pre.index.name = "id"
df_pre = df_pre.reset_index()
df = df_pre.melt(id_vars=["source", "date", "author", "url", "id"], var_name="pick")
df["pick"] = df["pick"].astype(int)
df["value"] = df["value"].map(eval, na_action="ignore")
df = df.dropna(axis=0).copy()
df["date"] = pd.to_datetime(df["date"], format='%m/%d/%y')
df[["team", "player", "pos", "sch", "conf"]] = pd.DataFrame(df["value"].tolist(), index=df.index)
df["team"] = df["team"].map(lambda s: s.split("-")[-1].capitalize())
df = df[df["team"].isin(draft_order)].copy()
df["week"] = df["date"].dt.round("7D")
df["ref"] = ["-".join(pair) for pair in df[["source", "author"]].values]

ind = df["player"].value_counts().index

player = st.selectbox(
    'What player are you interested in?',
    ind,
    index=ind.get_loc("Quentin Johnston"))

use_all = st.checkbox('Use all drafts?', value=True)

if not use_all:
    options = st.multiselect(
        'What drafts do you want to use?',
        sorted(df["ref"].unique()),
        ["Bleacher Nation-Andy Molitor", "NFL.com-Lance Zierlein", 
        "Walter Football-Charlie Campbell", "The Athletic-Dane Brugler",
        "NFL.com-Daniel Jeremiah", "CBS-Will Brinson", "Draftwire-Jeff Risdon"])
else:
    options = df["ref"].unique()

df_temp = df[df["player"].str.contains(player)
              & df["ref"].isin(options)].copy()

df_list = []
for pick, df_mini in df_temp.groupby(["pick", "week"]):
    ht = len(df_mini)
    df_mini["rank"] = range(1, ht+1)
    df_list.append(df_mini)
    
df_cat = pd.concat(df_list, axis=0)
df_cat = df_cat.sort_values("week", ascending=False)

chart_list = []
for wk, df_mini in df_cat.groupby("week", sort=False):
    ch = alt.Chart(df_mini).mark_circle().encode(
        x=alt.X("pick"),
        y=alt.Y("rank:N", sort="descending", title=None),
        tooltip=["source", "date", "author", "pick", "team"],
        href="url",
    ).properties(title=f"Week of {wk:%m-%d-%Y}")
    chart_list.append(ch)

st.altair_chart(alt.vconcat(*chart_list).configure_view(
    strokeOpacity=0
).configure_axis(
    grid=False
))