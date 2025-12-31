import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date

st.set_page_config(page_title="Chemical Trading System", layout="wide")

# --- DATABASE CONNECTION ---
try:
    # Initialize connection using Streamlit Secrets [connections.supabase]
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception as e:
    st.error("⚠️ Connection Error: Please verify your Streamlit Secrets configuration.")
    st.stop()

def load_data():
    try:
        # Fetch all rows from the 'transactions' table
        response = conn.table("transactions").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        # Return empty dataframe with correct columns if table/connection fails
        return pd.DataFrame(columns=[
            "txn_date", "material", "supplier", "purchase_price",
            "transport_cost", "buyer", "delivery_price",
            "pay_supplier", "pay_received", "net_amount"
        ])

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🧪 Chemical Trading System")
menu = st.sidebar.radio(
    "Navigation",
    ["➕ Add Transaction", "📒 Company Ledger", "📊 Overall Report"]
)

# ---------------- ADD TRANSACTION ---------------- #
if menu == "➕ Add Transaction":
    st.title("➕ Add New Transaction")

    # clear_on_submit resets the form after the button is clicked
    with st.form("transaction_form", clear_on_submit=True):
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
        # Simple validation
        if not material or not supplier or not buyer:
            st.warning("⚠️ Please fill in all name fields (Material, Supplier, Buyer) before saving.")
        else:
            try:
                net_amount = delivery_price - (purchase_price + transport_cost)

                # Map local variables to Supabase column names
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

                # Save directly to Supabase table 'transactions'
                conn.table("transactions").insert(new_row).execute()
                st.success(f"Transaction saved successfully ✅ Net Amount: ₹{net_amount:,.2f}")
            except Exception as e:
                st.error(f"❌ Failed to save transaction: {e}")

# ---------------- COMPANY LEDGER ---------------- #
elif menu == "📒 Company Ledger":
    st.title("📒 Company Ledger")

    df = load_data()
    if not df.empty:
        # Get unique names from both supplier and buyer columns
        all_entities = pd.unique(df[["supplier", "buyer"]].values.ravel("K"))
        company = st.selectbox("Select Company", sorted(all_entities))

        # Filter transactions related to the selected company
        ledger_df = df[
            (df["supplier"] == company) |
            (df["buyer"] == company)
        ].copy()

        # Define the role of the company for each row
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
        st.info("No data found in the database.")

# ---------------- OVERALL REPORT ---------------- #
elif menu == "📊 Overall Report":
    st.title("📊 Overall Trading Report")

    df = load_data()

    if not df.empty:
        total_profit = df["net_amount"].sum()
        st.metric("💰 Total Net Profit", f"₹ {total_profit:,.2f}")

        # Display full global ledger
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
        st.info("No data found in the database.")
