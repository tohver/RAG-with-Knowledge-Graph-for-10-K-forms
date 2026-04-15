import csv
from pathlib import Path
from typing import Any

from langchain_community.graphs import Neo4jGraph

from config import FORM13_FILE


def load_form13_rows(filepath: str = FORM13_FILE) -> list[dict[str, str]]:
    """Load Form 13 records from a CSV file."""
    path = Path(filepath)
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = [
            {key.strip(): value.strip() for key, value in row.items() if value is not None}
            for row in reader
            if row.get("cusip6")
        ]
    return rows


def ensure_company_constraints(kg: Neo4jGraph) -> None:
    kg.query(
        """
        CREATE CONSTRAINT unique_company IF NOT EXISTS
            FOR (c:Company) REQUIRE c.cusip6 IS UNIQUE
        """
    )


def ensure_manager_constraints(kg: Neo4jGraph) -> None:
    kg.query(
        """
        CREATE CONSTRAINT unique_manager IF NOT EXISTS
            FOR (m:Manager) REQUIRE m.managerCik IS UNIQUE
        """
    )


def ensure_company_nodes(kg: Neo4jGraph, rows: list[dict[str, str]]) -> None:
    query = """
    MERGE (com:Company {cusip6: $cusip6})
    ON CREATE SET
        com.companyName = $companyName,
        com.cusip = $cusip
    ON MATCH SET
        com.companyName = coalesce(com.companyName, $companyName)
    """

    for row in rows:
        kg.query(
            query,
            params={
                "cusip6": row["cusip6"],
                "companyName": row.get("companyName", ""),
                "cusip": row.get("cusip", ""),
            },
        )


def ensure_manager_nodes(kg: Neo4jGraph, rows: list[dict[str, str]]) -> None:
    query = """
    MERGE (mgr:Manager {managerCik: $managerCik})
    ON CREATE SET
        mgr.managerName = $managerName,
        mgr.managerAddress = $managerAddress
    ON MATCH SET
        mgr.managerName = coalesce(mgr.managerName, $managerName)
    """

    for row in rows:
        kg.query(
            query,
            params={
                "managerCik": row.get("managerCik", ""),
                "managerName": row.get("managerName", ""),
                "managerAddress": row.get("managerAddress", ""),
            },
        )


def ensure_owns_relationships(kg: Neo4jGraph, rows: list[dict[str, str]]) -> None:
    query = """
    MATCH (mgr:Manager {managerCik: $managerCik}),
          (com:Company {cusip6: $cusip6})
    MERGE (mgr)-[owns:OWNS_STOCK_IN {reportCalendarOrQuarter: $reportCalendarOrQuarter}]->(com)
    ON CREATE SET
        owns.value = toFloat($value),
        owns.shares = toInteger($shares)
    ON MATCH SET
        owns.value = toFloat($value),
        owns.shares = toInteger($shares)
    """

    for row in rows:
        kg.query(
            query,
            params={
                "managerCik": row.get("managerCik", ""),
                "cusip6": row.get("cusip6", ""),
                "reportCalendarOrQuarter": row.get("reportCalendarOrQuarter", ""),
                "value": row.get("value", "0"),
                "shares": row.get("shares", "0"),
            },
        )


def ensure_filed_relationships(kg: Neo4jGraph) -> None:
    kg.query(
        """
        MATCH (com:Company), (form:Form)
        WHERE com.cusip6 = form.cusip6
        MERGE (com)-[:FILED]->(form)
        """
    )


def enrich_graph_with_form13(kg: Neo4jGraph, rows: list[dict[str, str]]) -> None:
    ensure_company_constraints(kg)
    ensure_manager_constraints(kg)
    ensure_company_nodes(kg, rows)
    ensure_manager_nodes(kg, rows)
    ensure_owns_relationships(kg, rows)
    ensure_filed_relationships(kg)
    kg.refresh_schema()
