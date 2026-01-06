import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
from datetime import date

st.set_page_config(page_title="Chemical Trading System", layout="wide")

# --- DATABASE CONNECTION ---
try:
    conn = SupabaseConnection(
        connection_name="supabase",
        url=st.secrets["connections"]["supabase"]["url"],
        key=st.secrets["connections"]["supabase"]["key"],
    )
except Exception as e:
    st.error("⚠️ Connection Error: Please verify your Streamlit Secrets configuration.")
    st.exception(e)
    st.stop()


def load_data():
    try:
        response = conn.table("transactions").select("*").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame(columns=[
            "txn_date", "material", "supplier",
            "quantity_kg",
            "purchase_price_per_kg", "total_purchase_price",
            "transport_cost",
            "buyer",
            "delivery_price_per_kg", "total_delivery_price",
            "pay_supplier", "pay_received",
            "net_amount"
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

    with st.form("transaction_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            txn_date = st.date_input("Date", value=date.today())
            material = st.text_input("Material Name")
            supplier = st.text_input("Purchased From (Supplier)")
            quantity_kg = st.number_input("Quantity (KG)", min_value=0.0)

        with col2:
            purchase_price_per_kg = st.number_input(
                "Purchase Price / KG", min_value=0.0, placeholder="₹ per KG"
            )
            delivery_price_per_kg = st.number_input(
                "Delivery Price / KG", min_value=0.0, placeholder="₹ per KG"
            )
            transport_cost = st.number_input("Transportation Cost", min_value=0.0)
            buyer = st.text_input("Delivered To (Buyer)")

        with col3:
            total_purchase_price = quantity_kg * purchase_price_per_kg
            total_delivery_price = quantity_kg * delivery_price_per_kg

            st.text_input(
                "Total Purchase Price",
                value=f"{total_purchase_price:,.2f}",
                disabled=True
            )
            st.text_input(
                "Total Delivery Price",
                value=f"{total_delivery_price:,.2f}",
                disabled=True
            )

            pay_supplier = st.selectbox("Payment To Supplier", ["Pending", "Paid"])
            pay_received = st.selectbox("Payment Received From Buyer", ["Pending", "Received"])

        submit = st.form_submit_button("Save Transaction")

    if submit:
        if not material or not supplier or not buyer:
            st.warning("⚠️ Please fill in all name fields (Material, Supplier, Buyer).")
        else:
            try:
                net_amount = total_delivery_price - (total_purchase_price + transport_cost)

                new_row = {
                    "txn_date": str(txn_date),
                    "material": material,
                    "supplier": supplier,
                    "quantity_kg": quantity_kg,
                    "purchase_price_per_kg": purchase_price_per_kg,
                    "total_purchase_price": total_purchase_price,
                    "transport_cost": transport_cost,
                    "buyer": buyer,
                    "delivery_price_per_kg": delivery_price_per_kg,
                    "total_delivery_price": total_delivery_price,
                    "pay_supplier": pay_supplier,
                    "pay_received": pay_received,
                    "net_amount": net_amount
                }

                conn.table("transactions").insert(new_row).execute()
                st.success(f"Transaction saved successfully ✅ Net Amount: ₹{net_amount:,.2f}")
                st.cache_data.clear()

            except Exception as e:
                st.error(f"❌ Failed to save transaction: {e}")


# ---------------- COMPANY LEDGER ---------------- #
elif menu == "📒 Company Ledger":
    st.title("📒 Company Ledger")

    df = load_data()
    if not df.empty and "supplier" in df.columns:
        all_entities = pd.unique(df[["supplier", "buyer"]].values.ravel("K"))
        company = st.selectbox("Select Company", sorted(all_entities))

        ledger_df = df[(df["supplier"] == company) | (df["buyer"] == company)].copy()

        ledger_df["Role"] = ledger_df.apply(
            lambda x: "Supplier" if x["supplier"] == company else "Buyer",
            axis=1
        )

        st.dataframe(
            ledger_df[
                [
                    "txn_date", "material", "Role",
                    "quantity_kg",
                    "purchase_price_per_kg",
                    "delivery_price_per_kg",
                    "total_purchase_price",
                    "total_delivery_price",
                    "pay_supplier", "pay_received"
                ]
            ],
            use_container_width=True
        )
    else:
        st.info("No data found in the database.")


# ---------------- OVERALL REPORT ---------------- #
elif menu == "📊 Overall Report":
    st.title("📊 Overall Trading Report")

    df = load_data()

    if not df.empty and "net_amount" in df.columns:
        total_profit = df["net_amount"].sum()
        st.metric("💰 Total Net Profit", f"₹ {total_profit:,.2f}")

        st.dataframe(
            df[
                [
                    "txn_date", "material",
                    "supplier",
                    "quantity_kg",
                    "purchase_price_per_kg",
                    "total_purchase_price",
                    "transport_cost",
                    "buyer",
                    "delivery_price_per_kg",
                    "total_delivery_price",
                    "net_amount"
                ]
            ],
            use_container_width=True
        )
    else:
        st.info("No data found in the database.")
