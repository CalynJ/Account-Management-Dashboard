"""
Account Management Dashboard — Data Pipeline
==============================================
Simulates an end-to-end account management review pipeline for a B2B
factoring portfolio: fetching concentration reports from a factoring
platform API, transforming them into aging buckets and concentration
percentages, and exporting the results for downstream visualization
in Power BI.

This script uses a MOCKED API client (MockFactoringAPI) standing in for
a real factoring software vendor's API. No real credentials, endpoints,
or company data are used or required — this demonstrates the pipeline
architecture and transformation logic independent of any specific
vendor or employer system.

Workflow (see README for the full swim lane diagram):
  Start
    -> Fetch Client Concentration Data
    -> Transform Client Concentration Data
    -> Fetch Debtor Concentration Data
    -> Transform Debtor Concentration Data
    -> Load and Save Notes
    -> Save All Transformed Data to CSV
    -> End (feed into Power BI)
"""

import csv
import logging
import random
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


# ============================================================================
# Mock API Client
# ============================================================================
# Stands in for a real factoring platform's REST API. Same shape as a real
# client (auth, request wrapper, typed report methods) but returns
# generated sample data instead of calling a live vendor endpoint.

class MockFactoringAPI:
    def __init__(self):
        self.authenticated = False
        random.seed(42)  # reproducible sample data

    def authenticate(self):
        logger.info("Authenticating with mock factoring API...")
        self.authenticated = True
        logger.info("Authentication successful.")

    def _ensure_authenticated(self):
        if not self.authenticated:
            self.authenticate()

    def get_client_concentration(self, account_rep="all"):
        """
        Simulates GET /report/client-ar-detail (aggregated by client).
        Returns AR exposure per client with an aging breakdown.
        """
        self._ensure_authenticated()
        logger.info(f"Fetching client concentration data (account_rep={account_rep})...")
        clients = [
            "Apex Freight Solutions", "Bearclaw Logistics", "Coastal Grain Co",
            "Delta Textiles", "Evergreen Transport", "Frontline Steel",
            "Granite Hauling", "Horizon Produce", "Ironclad Trucking",
            "Juniper Fuel Distribution",
        ]
        data = []
        for client in clients:
            data.append({
                "client_name": client,
                "bucket_0_30": round(random.uniform(5000, 80000), 2),
                "bucket_31_45": round(random.uniform(1000, 20000), 2),
                "bucket_46_60": round(random.uniform(500, 10000), 2),
                "bucket_61_90": round(random.uniform(0, 5000), 2),
                "bucket_90_plus": round(random.uniform(0, 3000), 2),
            })
        return data

    def get_debtor_concentration(self, account_rep="all"):
        """
        Simulates GET /report/debtor-ar-detail (aggregated by debtor).
        Returns AR exposure per debtor with an aging breakdown.
        """
        self._ensure_authenticated()
        logger.info(f"Fetching debtor concentration data (account_rep={account_rep})...")
        debtors = [
            "Walmart", "Target", "Costco", "Kroger", "Albertsons",
            "Home Depot", "Lowe's", "CVS Health", "Walgreens", "Publix",
        ]
        data = []
        for debtor in debtors:
            data.append({
                "debtor_name": debtor,
                "bucket_0_30": round(random.uniform(20000, 150000), 2),
                "bucket_31_45": round(random.uniform(2000, 30000), 2),
                "bucket_46_60": round(random.uniform(1000, 15000), 2),
                "bucket_61_90": round(random.uniform(0, 8000), 2),
                "bucket_90_plus": round(random.uniform(0, 4000), 2),
            })
        return data

    def get_aging_report(self, client_id):
        """
        Simulates GET /report/aging?client_id={client_id}
        Returns invoice-level aging detail for ADTP calculation.
        """
        self._ensure_authenticated()
        logger.info(f"Fetching aging report for client_id={client_id}...")
        invoices = []
        base_date = datetime(2025, 1, 1)
        for i in range(20):
            invoice_date = base_date + timedelta(days=random.randint(0, 300))
            days_to_pay = random.randint(5, 95)
            receipt_date = invoice_date + timedelta(days=days_to_pay)
            invoices.append({
                "invoice_id": f"INV-{client_id}-{i+1:03d}",
                "invoice_date": invoice_date.strftime("%Y-%m-%d"),
                "receipt_date": receipt_date.strftime("%Y-%m-%d"),
                "days_to_pay": days_to_pay,
            })
        return invoices


# ============================================================================
# Transformation Functions
# ============================================================================

def transform_concentration_data(raw_data, name_field):
    """
    Adds total exposure, concentration %, and aging bucket % columns
    to raw concentration data — mirrors the manual Excel process
    (sort by concentration, add percentage columns per bucket).
    """
    for row in raw_data:
        buckets = ["bucket_0_30", "bucket_31_45", "bucket_46_60", "bucket_61_90", "bucket_90_plus"]
        row["total"] = round(sum(row[b] for b in buckets), 2)

    grand_total = sum(row["total"] for row in raw_data)

    for row in raw_data:
        row["concentration_pct"] = round((row["total"] / grand_total) * 100, 2) if grand_total else 0
        for b in ["bucket_0_30", "bucket_31_45", "bucket_46_60", "bucket_61_90", "bucket_90_plus"]:
            row[f"{b}_pct"] = round((row[b] / row["total"]) * 100, 2) if row["total"] else 0

    raw_data.sort(key=lambda r: r["concentration_pct"], reverse=True)
    logger.info(f"Transformed {len(raw_data)} {name_field} records. Grand total exposure: ${grand_total:,.2f}")
    return raw_data


def calculate_adtp(invoice_data):
    """
    Calculates Average Days to Pay (ADTP) from invoice-level data.
    ADTP has no dedicated API endpoint in most factoring platforms —
    it's derived here from invoice_date vs receipt_date, matching how
    it would need to be calculated from raw invoice/receipt data if a
    platform doesn't expose it directly.
    """
    total_days = sum(inv["days_to_pay"] for inv in invoice_data)
    adtp = round(total_days / len(invoice_data), 1) if invoice_data else 0
    logger.info(f"Calculated ADTP from {len(invoice_data)} invoices: {adtp} days")
    return adtp


def load_and_save_notes(client_name, notes_dict):
    """
    Captures the manual/qualitative fields from the account review
    process (billing procedures, action items, wins, etc.) alongside
    the quantitative data, so both live in the same output.
    """
    logger.info(f"Saving account notes for {client_name}...")
    return {"client_name": client_name, **notes_dict}


# ============================================================================
# Export
# ============================================================================

def export_to_csv(data, filepath, fieldnames):
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    logger.info(f"Exported {len(data)} rows to {filepath}")


# ============================================================================
# Pipeline
# ============================================================================

def run_pipeline():
    logger.info("=== Account Management Dashboard Pipeline: START ===")
    api = MockFactoringAPI()

    # Step 1-2: Client concentration
    client_data = api.get_client_concentration()
    client_data = transform_concentration_data(client_data, "client")

    # Step 3-4: Debtor concentration
    debtor_data = api.get_debtor_concentration()
    debtor_data = transform_concentration_data(debtor_data, "debtor")

    # ADTP example for the top client
    top_client_invoices = api.get_aging_report(client_id="1001")
    adtp = calculate_adtp(top_client_invoices)

    # Step 5: Notes
    notes = load_and_save_notes(client_data[0]["client_name"], {
        "last_contact": "2025-06-15",
        "loan_balance": 125000.00,
        "reserves_balance": 8400.00,
        "last_rebate": 2100.00,
        "adtp": adtp,
        "highest_debtor_concentration": debtor_data[0]["debtor_name"],
    })

    # Step 6: Export
    bucket_pct_fields = ["bucket_0_30_pct", "bucket_31_45_pct", "bucket_46_60_pct",
                         "bucket_61_90_pct", "bucket_90_plus_pct"]
    client_fields = (["client_name", "bucket_0_30", "bucket_31_45", "bucket_46_60",
                      "bucket_61_90", "bucket_90_plus", "total", "concentration_pct"]
                     + bucket_pct_fields)
    debtor_fields = (["debtor_name", "bucket_0_30", "bucket_31_45", "bucket_46_60",
                      "bucket_61_90", "bucket_90_plus", "total", "concentration_pct"]
                     + bucket_pct_fields)

    export_to_csv(client_data, "client_concentration.csv", client_fields)
    export_to_csv(debtor_data, "debtor_concentration.csv", debtor_fields)
    export_to_csv([notes], "account_notes.csv", list(notes.keys()))

    logger.info("=== Account Management Dashboard Pipeline: END ===")
    logger.info("Output CSVs ready to load into Power BI for visualization.")


if __name__ == "__main__":
    run_pipeline()
