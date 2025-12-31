import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date

st.set_page_config(page_title="Chemical Trading System", layout="wide")

# Initialize Supabase connection
# Credentials will be fetched from Streamlit Secrets
conn = st.connection("supabase", type=SupabaseConnection)

def load_data():
    try:
        # Fetch all rows from your Supabase 'transactions' table
        response = conn.table("transactions").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception:
        # Return empty dataframe if table is empty or doesn't exist yet
        return pd.DataFrame(columns=[
            "txn_date", "material", "supplier", "purchase_price",
            "transport_cost", "buyer", "delivery_price",
            "pay_supplier", "pay_received", "net_amount"
        ])

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

        # Map your fields to Supabase column names
        new_row = {
            "txn_date": str(txn_date),
            "material": material,
            "supplier": supplier,
            "purchase_price": purchase_price,
            "transport_cost": transport_cost,
            "buyer": buyer,
            "delivery_price": delivery_price,
            "pay_supplier": pay_supplier,
            "pay_received": pay_received,
            "net_amount": net_amount
        }

        # Save directly to Supabase
        conn.table("transactions").insert(new_row).execute()

        st.success(f"Transaction saved successfully ✅ Net Amount: ₹{net_amount}")

# ---------------- COMPANY LEDGER ---------------- #
elif menu == "📒 Company Ledger":
    st.title("📒 Company Ledger")

    df = load_data()
    if not df.empty:
        companies = pd.unique(df[["supplier", "buyer"]].values.ravel("K"))
        company = st.selectbox("Select Company", companies)

        ledger_df = df[
            (df["supplier"] == company) |
            (df["buyer"] == company)
        ].copy()

        ledger_df["Role"] = ledger_df.apply(
            lambda x: "Supplier" if x["supplier"] == company else "Buyer",
            axis=1
        )

        st.dataframe(
            ledger_df[
                ["txn_date", "material", "Role",
                 "purchase_price", "delivery_price",
                 "pay_supplier", "pay_received"]
            ],
            use_container_width=True
        )
    else:
        st.info("No data found in database.")

# ---------------- OVERALL REPORT ---------------- #
elif menu == "📊 Overall Report":
    st.title("📊 Overall Trading Report")

    df = load_data()

    if not df.empty:
        total_profit = df["net_amount"].sum()
        st.metric("💰 Total Net Profit", f"₹ {total_profit}")

        st.dataframe(
            df[
                ["txn_date", "material",
                 "supplier", "purchase_price",
                 "transport_cost",
                 "buyer", "delivery_price",
                 "net_amount"]
            ],
            use_container_width=True
        )
    else:
        st.info("No data found in database.")
