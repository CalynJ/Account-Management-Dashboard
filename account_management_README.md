# Account Management Dashboard — Data Pipeline

A Python pipeline that automates the account management review process for a B2B factoring portfolio: fetching client and debtor concentration data from a factoring platform API, transforming it into aging buckets and concentration percentages, and exporting results for visualization in Power BI.

## Background

This project replaces a manual review process that previously required pulling multiple reports by hand, sorting by concentration, and building aging percentage tables in Excel for every client and debtor on a rolling basis. This pipeline automates that transformation end-to-end.

## Important note on data source

This script uses a **mocked API client** (`MockFactoringAPI`) that generates realistic sample data in the same shape as a real factoring platform's reporting API. It does not connect to, reference, or require credentials for any specific vendor or employer system. The goal is to demonstrate the pipeline architecture and transformation logic independent of any particular company's live data or infrastructure.

## Workflow

```
Start
  -> Fetch Client Concentration Data
  -> Transform Client Concentration Data
  -> Fetch Debtor Concentration Data
  -> Transform Debtor Concentration Data
  -> Load and Save Notes
  -> Save All Transformed Data to CSV
  -> End (feed into Power BI)
```

## What it does

- **Concentration analysis**: calculates each client's/debtor's share of total portfolio exposure, sorted highest to lowest, to flag concentration risk
- **Aging bucket breakdown**: splits exposure into 0-30, 31-45, 46-60, 61-90, and 90+ day buckets, both in dollar amount and as a percentage of that account's total
- **ADTP (Average Days to Pay)**: calculated from invoice-level date vs. receipt date, since this metric typically isn't exposed directly by factoring platform APIs and has to be derived from raw invoice/receipt data
- **Account notes**: captures qualitative account review fields (last contact, loan balance, reserves, rebate, highest debtor concentration) alongside the quantitative output
- **CSV export**: outputs three files (`client_concentration.csv`, `debtor_concentration.csv`, `account_notes.csv`) structured for direct import into Power BI

## Running it

```
python account_management_pipeline.py
```

No setup or credentials required — it runs entirely on generated sample data.

## Notes

This was adapted from a real account management review process I built and used in a B2B factoring context, restructured here to run independently of any employer-specific system or credentials.
