import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

st.set_page_config(page_title="Chemical Trading System", layout="wide")

# --- GOOGLE SHEETS CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # Reads the live data from your Google Sheet
    return conn.read(ttl="0m")

def save_data(df):
    # Updates the Google Sheet with the new dataframe
    conn.update(data=df)

st.sidebar.title("🧪 Chemical Trading System")
menu = st.sidebar.radio(
    "Navigation",
    ["➕ Add Transaction", "📒 Company Ledger", "📊 Overall Report"]
)

# ---------------- ADD TRANSACTION ---------------- #
if menu == "➕ Add Transaction":
    st.title("➕ Add New Transaction")

    with st.form("transaction_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            txn_date = st.date_input("Date", value=date.today())
            material = st.text_input("Material Name")
            supplier = st.text_input("Purchased From (Supplier)")
            purchase_price = st.number_input("Purchase Price", min_value=0.0)

        with col2:
            transport_cost = st.number_input("Transportation Cost", min_value=0.0)
            buyer = st.text_input("Delivered To (Buyer)")
            delivery_price = st.number_input("Delivery Price", min_value=0.0)

        with col3:
            pay_supplier = st.selectbox("Payment To Supplier", ["Pending", "Paid"])
            pay_received = st.selectbox("Payment Received From Buyer", ["Pending", "Received"])

        submit = st.form_submit_button("Save Transaction")

    if submit:
        net_amount = delivery_price - (purchase_price + transport_cost)

        new_row = {
            "Date": str(txn_date),
            "Material": material,
            "Purchased From": supplier,
            "Purchase Price": purchase_price,
            "Transportation Cost": transport_cost,
            "Delivered To": buyer,
            "Delivery Price": delivery_price,
            "Payment To Supplier": pay_supplier,
            "Payment Received From Buyer": pay_received,
            "Net Amount": net_amount
        }

        df = load_data()
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)

        st.success(f"Transaction saved successfully ✅ Net Amount: ₹{net_amount}")

# ---------------- COMPANY LEDGER ---------------- #
elif menu == "📒 Company Ledger":
    st.title("📒 Company Ledger")

    df = load_data()
    if not df.empty:
        companies = pd.unique(df[["Purchased From", "Delivered To"]].values.ravel("K"))
        company = st.selectbox("Select Company", companies)

        ledger_df = df[
            (df["Purchased From"] == company) |
            (df["Delivered To"] == company)
        ].copy()

        ledger_df["Role"] = ledger_df.apply(
            lambda x: "Supplier" if x["Purchased From"] == company else "Buyer",
            axis=1
        )

        st.dataframe(
            ledger_df[
                ["Date", "Material", "Role",
                 "Purchase Price", "Delivery Price",
                 "Payment To Supplier", "Payment Received From Buyer"]
            ],
            use_container_width=True
        )
    else:
        st.info("No data found in the spreadsheet.")

# ---------------- OVERALL REPORT ---------------- #
elif menu == "📊 Overall Report":
    st.title("📊 Overall Trading Report")

    df = load_data()
    if not df.empty:
        total_profit = df["Net Amount"].sum()
        st.metric("💰 Total Net Profit", f"₹ {total_profit}")

        st.dataframe(
            df[
                ["Date", "Material",
                 "Purchased From", "Purchase Price",
                 "Transportation Cost",
                 "Delivered To", "Delivery Price",
                 "Net Amount"]
            ],
            use_container_width=True
        )
    else:
        st.info("No data found in the spreadsheet.")
