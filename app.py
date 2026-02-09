import streamlit as st
from datetime import datetime
import math
import re
import os
from io import BytesIO

import requests
from bs4 import BeautifulSoup

import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas as pdf_canvas


# ----------------------------
# Config
# ----------------------------
st.set_page_config(page_title="LBH - Proforma DA", layout="wide")

COLORS = {
    "primary_blue": "#003366",
    "secondary_blue": "#0066A1",
    "accent_blue": "#4A90A4",
    "light_blue": "#E6F2F5",
    "gold": "#DAA520",
    "white": "#FFFFFF",
    "light_gray": "#F5F5F5",
    "medium_gray": "#E0E0E0",
    "text_dark": "#1A1A1A",
    "header_bg": "#002B4D",
    "yellow_work": "#FFF9E6",
}

CURRENCY_DEFAULT = "USD"


# ----------------------------
# Opciones por puerto (igual a tu Tkinter)
# ----------------------------
PORT_OPTIONS = {
    "Valparaíso TPV": [
        "Light Dues",
        "Port Shelter Dues",
        "Authorities Expenses",
        "Port Pilotage",
        "Towage",
        "Launch Boat IC",
        "Launch Boat MU",
        "Dockage",
        "Transport For Authorities",
        "Pilot Transportation",
        "Pilot Insurance",
        "Agency Fee",
    ],
    "Valparaíso TPS": [
        "Light Dues",
        "Port Shelter Dues",
        "Authorities Expenses",
        "Port Pilotage",
        "Towage",
        "Launch Boat IC",
        "Launch Boat MU",
        "Dockage",
        "Transport For Authorities",
        "Pilot Transportation",
        "Pilot Insurance",
        "Agency Fee",
        "Vat Recovery Fee",
    ],
    "Valparaíso - Anchor": [
        "Light Dues",
        "Authorities Expenses",
        "Port Pilotage For Anchor",
        "Launch Boat IC",
        "Transport For Authorities",
        "Pilot Transportation",
        "Pilot Insurance",
        "Agency Fee",
        "Vat Recovery Fee",
    ],
    "Quintero - Enap": [
        "Light Dues",
        "Authorities Expenses",
        "Port Pilotage",
        "Port Pilotage For Anchor",
        "Towage",
        "Launch Boat MU",
        "Launch Boat IC",
        "Launch Boat AN",
        "Linesmen 1",
        "Security Fee",
        "Pier toll dues",
        "Pilot Insurance",
        "Pilot Transportation",
        "Transport For Authorities",
        "Agency Fee",
        "Vat Recovery Fee",
    ],
    "Ventanas": [
        "Light Dues",
        "Authorities Expenses",
        "Port Pilotage",
        "Port Pilotage For Anchor",
        "Towage",
        "Launch Boat MU",
        "Launch Boat AN",
        "Launch Boat IC",
        "Dockage Fixed",
        "Dockage Per Add Hr",
        "Linesmen 1",
        "Linesmen 2",
        "Shore tension system",
        "Loading Master",
        "Security fee Ventanas",
        "Pier toll dues",
        "Transport For Authorities",
        "Pilot Insurance",
        "Pilot Transportation",
        "Agency Fee",
        "Vat Recovery Fee",
    ],
    "Magellan Strait": [
        "Light Dues",
        "Channel Pilotage",
        "Pilot Waiting Time",
        "Pilot Insurance",
        "Pilot Transportation",
        "Launch Boat PUQ",
        "Launch Boat POS",
        "Agency Fee",
        "Vat Recovery Fee",
    ],
    "Magellan Strait Felix": [
        "Light Dues",
        "Channel Pilotage",
        "Channel Pilotage-Felix",
        "Pilot Waiting Time",
        "Pilot Insurance",
        "Pilot Transportation",
        "Launch Boat PUQ",
        "Launch Boat POS",
        "Launch Boat Felix",
        "Agency Fee",
        "Vat Recovery Fee",
    ],
    "Magellan Strait Full Pilotage": [
        "Light Dues",
        "Full Channel Pilotage",
        "Pilot Waiting Time",
        "Pilot Insurance",
        "Pilot Transportation",
        "Launch Boat ZUD",
        "Launch Boat LAI",
        "Launch Boat POS",
        "Agency Fee",
        "Vat Recovery Fee",
    ],
    "Mejillones - TGN 1": [
        "Light Dues",
        "Authorities Expenses",
        "Port Pilotage",
        "Port Pilotage For Anchor",
        "Port Pilotage For Shiftings",
        "Towage",
        "Launch Boat MU",
        "Launch Boat IC",
        "Dockage",
        "Linesmen 1",
        "Linesmen Shiftings",
        "Pilot Insurance",
        "Pilot Transportation",
        "Transport For Authorities",
        "Agency Fee",
        "Vat Recovery Fee",
    ],
    "Mejillones - TGN 2": [
        "Light Dues",
        "Authorities Expenses",
        "Port Pilotage",
        "Port Pilotage For Anchor",
        "Port Pilotage For Shiftings",
        "Towage",
        "Launch Boat MU",
        "Launch Boat IC",
        "Dockage",
        "Linesmen 1",
        "Pilot Insurance",
        "Pilot Transportation",
        "Transport For Authorities",
        "Agency Fee",
        "Vat Recovery Fee",
    ],
    "Mejillones - Pto Angamos": [
        "Light Dues",
        "Port Shelter Dues",
        "Authorities Expenses",
        "Port Pilotage",
        "Port Pilotage For Anchor",
        "Towage",
        "Launch Boat MU",
        "Launch Boat IC",
        "Dockage",
        "Linesmen 1",
        "Pilot Insurance",
        "Pilot Transportation",
        "Transport For Authorities",
        "Agency Fee",
        "Vat Recovery Fee",
    ],
    "San Vicente - Enap": [
        "Light Dues",
        "Authorities Expenses",
        "Pre Pilotage",
        "Port Pilotage",
        "Port Pilotage For Anchor",
        "Towage",
        "Towage Navigation",
        "Launch Boat MU",
        "Launch Boat IC",
        "Launch Boat AN",
        "Pilot Insurance",
        "Pilot Transportation",
        "Transport For Authorities",
        "Agency Fee",
        "Vat Recovery Fee",
    ],
}


# ----------------------------
# Reglas IVA (idéntico enfoque)
# ----------------------------
IVA_RULES = {
    "Valparaíso TPV": {
        "Light Dues": {"DISCHARGING_NIL": False, "LOADING": False},
        "Port Pilotage": {"DISCHARGING_NIL": False, "LOADING": False},
        "Towage": {"DISCHARGING_NIL": True, "LOADING": False},
        "Launch Boat MU": {"DISCHARGING_NIL": True, "LOADING": False},
        "Transport For Authorities": {"DISCHARGING_NIL": False, "LOADING": False},
        "Port Shelter Dues": {"DISCHARGING_NIL": True, "LOADING": True},
        "Authorities Expenses": {"DISCHARGING_NIL": False, "LOADING": False},
        "Dockage": {"DISCHARGING_NIL": True, "LOADING": False},
        "Launch Boat IC": {"DISCHARGING_NIL": True, "LOADING": False},
        "Pilot Transportation": {"DISCHARGING_NIL": False, "LOADING": False},
        "Pilot Insurance": {"DISCHARGING_NIL": True, "LOADING": True},
        "Agency Fee": {"DISCHARGING_NIL": True, "LOADING": True},
        "Vat Recovery Fee": {"DISCHARGING_NIL": False, "LOADING": False},
    },
    "Valparaíso TPS": {
        "Light Dues": {"DISCHARGING_NIL": False, "LOADING": False},
        "Port Pilotage": {"DISCHARGING_NIL": False, "LOADING": False},
        "Towage": {"DISCHARGING_NIL": True, "LOADING": False},
        "Launch Boat MU": {"DISCHARGING_NIL": True, "LOADING": False},
        "Transport For Authorities": {"DISCHARGING_NIL": False, "LOADING": False},
        "Port Shelter Dues": {"DISCHARGING_NIL": True, "LOADING": True},
        "Authorities Expenses": {"DISCHARGING_NIL": False, "LOADING": False},
        "Dockage": {"DISCHARGING_NIL": True, "LOADING": False},
        "Launch Boat IC": {"DISCHARGING_NIL": True, "LOADING": False},
        "Launch Boat AN": {"DISCHARGING_NIL": True, "LOADING": False},
        "Security Fee": {"DISCHARGING_NIL": True, "LOADING": True},
        "Pier toll dues": {"DISCHARGING_NIL": True, "LOADING": True},
        "Pilot Insurance": {"DISCHARGING_NIL": True, "LOADING": True},
        "Pilot Transportation": {"DISCHARGING_NIL": False, "LOADING": False},
        "Agency Fee": {"DISCHARGING_NIL": True, "LOADING": True},
        "Vat Recovery Fee": {"DISCHARGING_NIL": False, "LOADING": False},
    },
    "Ventanas": {
        "Light Dues": {"DISCHARGING_NIL": False, "LOADING": False},
        "Port Pilotage": {"DISCHARGING_NIL": False, "LOADING": False},
        "Towage": {"DISCHARGING_NIL": True, "LOADING": False},
        "Launch Boat MU": {"DISCHARGING_NIL": True, "LOADING": False},
        "Launch Boat AN": {"DISCHARGING_NIL": True, "LOADING": False},
        "Launch Boat IC": {"DISCHARGING_NIL": True, "LOADING": False},
        "Dockage Fixed": {"DISCHARGING_NIL": True, "LOADING": False},
        "Dockage Per Add Hr": {"DISCHARGING_NIL": True, "LOADING": False},
        "Linesmen 1": {"DISCHARGING_NIL": True, "LOADING": True},
        "Linesmen 2": {"DISCHARGING_NIL": True, "LOADING": True},
        "Shore tension system": {"DISCHARGING_NIL": True, "LOADING": False},
        "Loading Master": {"DISCHARGING_NIL": True, "LOADING": False},
        "Security fee Ventanas": {"DISCHARGING_NIL": True, "LOADING": False},
        "Pier toll dues": {"DISCHARGING_NIL": True, "LOADING": True},
        "Transport For Authorities": {"DISCHARGING_NIL": False, "LOADING": False},
        "Pilot Insurance": {"DISCHARGING_NIL": True, "LOADING": True},
        "Pilot Transportation": {"DISCHARGING_NIL": False, "LOADING": False},
        "Agency Fee": {"DISCHARGING_NIL": True, "LOADING": True},
        "Vat Recovery Fee": {"DISCHARGING_NIL": False, "LOADING": False},
        "Authorities Expenses": {"DISCHARGING_NIL": False, "LOADING": False},
        "Port Pilotage For Anchor": {"DISCHARGING_NIL": False, "LOADING": False},
    },
    "Quintero - Enap": {
        "Light Dues": {"DISCHARGING_NIL": False, "LOADING": False},
        "Authorities Expenses": {"DISCHARGING_NIL": False, "LOADING": False},
        "Port Pilotage": {"DISCHARGING_NIL": False, "LOADING": False},
        "Port Pilotage For Anchor": {"DISCHARGING_NIL": False, "LOADING": False},
        "Towage": {"DISCHARGING_NIL": True, "LOADING": False},
        "Launch Boat MU": {"DISCHARGING_NIL": True, "LOADING": False},
        "Launch Boat IC": {"DISCHARGING_NIL": True, "LOADING": False},
        "Launch Boat AN": {"DISCHARGING_NIL": True, "LOADING": False},
        "Linesmen 1": {"DISCHARGING_NIL": True, "LOADING": True},
        "Security Fee": {"DISCHARGING_NIL": True, "LOADING": True},
        "Pier toll dues": {"DISCHARGING_NIL": True, "LOADING": True},
        "Pilot Insurance": {"DISCHARGING_NIL": True, "LOADING": True},
        "Pilot Transportation": {"DISCHARGING_NIL": False, "LOADING": False},
        "Transport For Authorities": {"DISCHARGING_NIL": False, "LOADING": False},
        "Agency Fee": {"DISCHARGING_NIL": True, "LOADING": True},
        "Vat Recovery Fee": {"DISCHARGING_NIL": False, "LOADING": False},
    },
    "Valparaíso - Anchor": {
        "Light Dues": {"DISCHARGING_NIL": False, "LOADING": False},
        "Authorities Expenses": {"DISCHARGING_NIL": False, "LOADING": False},
        "Port Pilotage For Anchor": {"DISCHARGING_NIL": False, "LOADING": False},
        "Launch Boat IC": {"DISCHARGING_NIL": True, "LOADING": False},
        "Transport For Authorities": {"DISCHARGING_NIL": False, "LOADING": False},
        "Pilot Transportation": {"DISCHARGING_NIL": False, "LOADING": False},
        "Pilot Insurance": {"DISCHARGING_NIL": True, "LOADING": True},
        "Agency Fee": {"DISCHARGING_NIL": True, "LOADING": True},
        "Vat Recovery Fee": {"DISCHARGING_NIL": False, "LOADING": False},
    },
    "Magellan Strait": {
        "Light Dues": {"DISCHARGING_NIL": False, "LOADING": False},
        "Channel Pilotage": {"DISCHARGING_NIL": False, "LOADING": False},
        "Pilot Waiting Time": {"DISCHARGING_NIL": False, "LOADING": False},
        "Launch Boat PUQ": {"DISCHARGING_NIL": True, "LOADING": True},
        "Launch Boat POS": {"DISCHARGING_NIL": True, "LOADING": True},
        "Pilot Transportation": {"DISCHARGING_NIL": False, "LOADING": False},
        "Pilot Insurance": {"DISCHARGING_NIL": True, "LOADING": True},
        "Agency Fee": {"DISCHARGING_NIL": True, "LOADING": True},
        "Vat Recovery Fee": {"DISCHARGING_NIL": False, "LOADING": False},
    },
    # ... puedes pegar aquí el resto igual que en tu Tkinter si quieres 1:1
}


LIGHT_DUES_CHOICES = [
    "4.07 (Anual)",
    "1.6 (Per Boyage)",
    "0.93 (Bulk)",
    "0.16 (Bunker)",
    "0.29 (Magellan Strait)",
    "1.31 (Cabotage)",
]

DOCKAGE_FIXED_CHOICES = [
    "63657 (Sitio 2 y 3)",
    "68660 (sitio 5)",
]


# ----------------------------
# Helpers
# ----------------------------
def purpose_group(purpose: str) -> str:
    p = (purpose or "").strip()
    return "LOADING" if p == "Loading" else "DISCHARGING_NIL"


def tiene_iva(port: str, desc: str, purpose: str) -> bool:
    g = purpose_group(purpose)
    return bool(IVA_RULES.get(port, {}).get(desc, {}).get(g, False))


def clean_imo(imo_raw: str) -> str:
    return re.sub(r"[^\d]", "", imo_raw or "")


def buscar_vesselfinder_imo(imo: str):
    try:
        url = f"https://www.vesselfinder.com/es/vessels/details/{imo}"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        }
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.content, "html.parser")
        datos = {"imo": imo}

        title = soup.find("h1")
        if title:
            vessel_name = title.get_text(strip=True)
            vessel_name = re.sub(r"\s*IMO\s*\d+", "", vessel_name, flags=re.IGNORECASE)
            datos["vessel_name"] = vessel_name.strip()

        tables = soup.find_all("table")
        for table in tables:
            for row in table.find_all("tr"):
                cells = row.find_all(["td", "th"])
                if len(cells) < 2:
                    continue
                label = cells[0].get_text(strip=True).lower()
                value = cells[1].get_text(strip=True)

                if any(x in label for x in ["tonelaje bruto", "gross tonnage", "gt", "arqueo bruto"]):
                    m = re.search(r"[\d,\.]+", value)
                    if m:
                        gt_str = m.group().replace(",", "").replace(".", "")
                        try:
                            datos["gt"] = int(gt_str)
                        except:
                            pass

                if any(x in label for x in ["eslora", "length overall", "loa", "longitud"]):
                    loa_match = re.search(r"(\d+)\s*[/]", value)
                    if loa_match:
                        datos["loa"] = int(loa_match.group(1))
                    else:
                        loa_match = re.search(r"([\d.]+)", value)
                        if loa_match:
                            try:
                                datos["loa"] = float(loa_match.group(1))
                            except:
                                pass

                if "mmsi" in label:
                    mm = re.search(r"\d+", value)
                    if mm:
                        datos["mmsi"] = mm.group()

                if any(x in label for x in ["tipo ais", "ais type", "ship type", "type"]):
                    datos["ais_type"] = value.strip()

        if datos.get("gt") or datos.get("loa"):
            return datos
        return None
    except Exception:
        return None


def buscar_myshiptracking_imo(imo: str):
    try:
        url = "https://www.myshiptracking.com/requests/vesselinfo.php"
        params = {"imo": imo}
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.myshiptracking.com/", "Accept": "application/json"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        if not data or not isinstance(data, list):
            return None
        vessel = data[0]
        gt = vessel.get("GT") or vessel.get("gt")
        loa = vessel.get("LENGTH") or vessel.get("length") or vessel.get("LOA")
        try:
            gt = int(str(gt).replace(",", "").replace(".", "")) if gt else None
        except:
            gt = None
        try:
            loa = float(str(loa).replace(",", "")) if loa else None
        except:
            loa = None

        return {
            "vessel_name": vessel.get("NAME") or vessel.get("name"),
            "gt": gt,
            "loa": loa,
            "imo": imo,
            "mmsi": vessel.get("MMSI") or vessel.get("mmsi"),
            "ais_type": vessel.get("TYPE") or vessel.get("type"),
        }
    except Exception:
        return None


def buscar_marinetraffic_imo(imo: str):
    try:
        url = f"https://www.marinetraffic.com/en/ais/details/ships/imo:{imo}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.content, "html.parser")
        datos = {"imo": imo}
        all_text = soup.get_text(" ")

        title = soup.find("h1")
        if title:
            datos["vessel_name"] = title.get_text(strip=True)

        for pattern in [r"Gross Tonnage[:\s]+([,\d]+)", r"GT[:\s]+([,\d]+)"]:
            m = re.search(pattern, all_text, re.IGNORECASE)
            if m:
                try:
                    datos["gt"] = int(m.group(1).replace(",", ""))
                    break
                except:
                    pass

        for pattern in [r"Length Overall[:\s]+([\d.]+)", r"LOA[:\s]+([\d.]+)", r"Length[:\s]+([\d.]+)\s*m"]:
            m = re.search(pattern, all_text, re.IGNORECASE)
            if m:
                try:
                    datos["loa"] = float(m.group(1))
                    break
                except:
                    pass

        if datos.get("gt") or datos.get("loa"):
            return datos
        return None
    except Exception:
        return None


def buscar_por_imo(imo: str):
    for fn in (buscar_vesselfinder_imo, buscar_myshiptracking_imo, buscar_marinetraffic_imo):
        datos = fn(imo)
        if datos and (datos.get("gt") or datos.get("loa")):
            return datos
    return None


def calcular_port_stay(cargo_mt: float, rate: float, purpose: str) -> int:
    if (purpose or "").strip() == "NIL":
        return 0
    if rate <= 0 or cargo_mt <= 0:
        return 0
    port_stay = (cargo_mt / rate) * 24
    base = math.floor(port_stay)
    return base if (port_stay - base) < 0.5 else math.ceil(port_stay)


def ensure_rows(n=20) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Description": "",
                "Remarks": "",
                "Currency": CURRENCY_DEFAULT,
                "Tarifa": "",
                "Cantidad": "",
                "Selector": "",   # para combos especiales (Light Dues / Dockage Fixed)
                "Amount": 0.00,
            }
            for _ in range(n)
        ]
    )


def apply_port_defaults(df: pd.DataFrame, port: str) -> pd.DataFrame:
    df = df.copy()
    options = PORT_OPTIONS.get(port, [])
    for i in range(len(df)):
        if i < len(options):
            df.at[i, "Description"] = options[i]
        else:
            df.at[i, "Description"] = ""
            df.at[i, "Remarks"] = ""
            df.at[i, "Tarifa"] = ""
            df.at[i, "Cantidad"] = ""
            df.at[i, "Selector"] = ""
            df.at[i, "Amount"] = 0.00
    return df


def to_float(x, default=0.0):
    try:
        if x is None:
            return default
        s = str(x).strip()
        if s == "":
            return default
        return float(s.replace(",", ""))
    except:
        return default


def compute_expenses(df: pd.DataFrame, gt: float, loa: float, port_stay: float, port: str, purpose: str, ais_type: str, vat_recovery_enabled: bool):
    df = df.copy()
    ais = (ais_type or "").upper()

    # Dockage Ventanas helper (depende de selector en Dockage Fixed)
    dockage_fixed_sel = ""
    for i in range(len(df)):
        if df.at[i, "Description"] == "Dockage Fixed":
            dockage_fixed_sel = str(df.at[i, "Selector"] or "")
            break

    # 1) calcular items (sin Vat Recovery Fee)
    for i in range(len(df)):
        desc = (df.at[i, "Description"] or "").strip()
        if not desc:
            df.at[i, "Amount"] = 0.0
            df.at[i, "Remarks"] = ""
            continue

        amount = 0.0
        remark = ""

        if desc == "Light Dues":
            sel = str(df.at[i, "Selector"] or "").strip()
            if sel:
                mult = to_float(sel.split(" ")[0], 0.0)
                amount = mult * gt
                remark = f"${mult} USD per GT"

        elif desc == "Dockage Fixed":
            sel = str(df.at[i, "Selector"] or "").strip()
            if sel:
                base = to_float(sel.split(" ")[0], 0.0)
                amount = base
                amount_formatted = f"{amount:,.0f}".replace(",", ".")
                remark = f"USD ${amount_formatted} First 12 Hours"

        elif desc == "Port Shelter Dues":
            if port in ("Valparaíso TPV", "Valparaíso TPS"):
                amount = 0.5 * gt
                remark = "$0.50 USD per GT"
            elif port == "Mejillones - Pto Angamos":
                amount = 0.20 * gt
                remark = "$0.20 USD per GT"

        elif desc == "Authorities Expenses":
            amount = to_float(df.at[i, "Tarifa"], 600.0)  # uso Tarifa como amount manual
            if amount == 0:
                amount = 600.0
            remark = "Maritime, health, SAG and immigration authorities"

        elif desc in ["Agency Fee", "Transport For Authorities", "Pilot Transportation", "Pilot Insurance",
                      "Launch Boat PUQ", "Launch Boat ZUD", "Launch Boat LAI", "Launch Boat POS", "Launch Boat Felix"]:
            amount = to_float(df.at[i, "Tarifa"], 0.0)  # uso Tarifa como amount manual
            # remarks similares a tu Tkinter (puedes ajustar)
            if desc == "Agency Fee":
                remark = "Per call"
            elif desc == "Pilot Insurance":
                remark = "Per Pilot"
            elif desc == "Launch Boat PUQ":
                remark = "Pilot Embark / Disembark Punta Arenas"
                if amount == 0: amount = 1950
            elif desc == "Launch Boat ZUD":
                remark = "Pilot Embark / Disembark Ancud"
                if amount == 0: amount = 2250
            elif desc == "Launch Boat LAI":
                remark = "Pilot Embark / Disembark Punta Laitec"
                if amount == 0: amount = 4250
            elif desc == "Launch Boat POS":
                remark = "Pilot Embark / Disembark Posesion"
                if amount == 0: amount = 3900
            elif desc == "Launch Boat Felix":
                remark = "Pilot Embark / Disembark Felix"
                if amount == 0: amount = 28000

        elif desc in ["Towage", "Towage Navigation", "Launch Boat IC", "Launch Boat MU", "Launch Boat AN",
                      "Linesmen 1", "Linesmen 2", "Linesmen Shiftings", "Pier toll dues"]:
            tarifa = to_float(df.at[i, "Tarifa"], 0.0)
            cantidad = to_float(df.at[i, "Cantidad"], 0.0)

            if desc == "Towage":
                es_tanker = "TANKER" in ais
                # si no hay tarifa manual, tabla por GT como tu lógica
                if tarifa <= 0:
                    if 1 <= gt <= 10000:
                        tarifa = 2166
                    elif 10001 <= gt <= 12500:
                        tarifa = 2353
                    elif 12501 <= gt <= 15000:
                        tarifa = 2666
                    elif 15001 <= gt <= 17500:
                        tarifa = 2871
                    elif 17501 <= gt <= 20000:
                        tarifa = 3093
                    elif 20001 <= gt <= 25000:
                        tarifa = 3321
                    elif 25001 <= gt <= 30000:
                        tarifa = 3593
                    elif 30001 <= gt <= 35000:
                        tarifa = 3937
                    elif 35001 <= gt <= 40000:
                        tarifa = 4316
                    elif 40001 <= gt <= 45000:
                        tarifa = 4733
                    elif 45001 <= gt <= 50000:
                        tarifa = 5191
                    else:
                        c2 = (gt - 50000) / 10000 if gt > 50000 else 0
                        tarifa = 5191 + (5191 * 0.1 * c2)

                if es_tanker:
                    tarifa *= 0.85

                amount = tarifa * max(cantidad, 0.0)
                remark = f"USD {tarifa:,.2f} per tug (estimated 2 in (1.5 hrs) 2 out (1 hr))"

            elif desc == "Towage Navigation":
                if tarifa <= 0:
                    tarifa = 735
                amount = tarifa * max(cantidad, 0.0)
                remark = f"USD {tarifa:,.2f} per tug (navigation)"

            elif desc == "Launch Boat IC":
                amount = tarifa * cantidad
                if tarifa or cantidad:
                    remark = "Inward Clearance"
            elif desc == "Launch Boat MU":
                amount = tarifa * cantidad
                if tarifa or cantidad:
                    remark = "Mooring / Unmooring"
            elif desc == "Launch Boat AN":
                amount = tarifa * cantidad
                if tarifa or cantidad:
                    remark = "Anchorage"
            elif desc == "Linesmen 1":
                # defaults como tu Tkinter (puedes ajustar si quieres 1:1 total)
                if tarifa <= 0:
                    if port == "Ventanas": tarifa = 1957.32
                    elif port == "Quintero - Enap": tarifa = 500
                    elif port == "Mejillones - TGN 1": tarifa = 3070.35
                    elif port == "Mejillones - TGN 2": tarifa = 3333.27
                    elif port == "Mejillones - Pto Angamos": tarifa = 856.41
                amount = tarifa * cantidad
                remark = "Mooring / Unmooring"
            elif desc == "Linesmen 2":
                if tarifa <= 0 and port == "Ventanas":
                    tarifa = 1100
                amount = tarifa * cantidad
                remark = "On launch Service"
            elif desc == "Linesmen Shiftings":
                if tarifa <= 0 and port == "Mejillones - TGN 1":
                    tarifa = 262.92
                amount = tarifa * cantidad
                remark = ""
            elif desc == "Pier toll dues":
                amount = tarifa * cantidad
                if tarifa or cantidad:
                    remark = "Considers Pier Asimar Per Shift"

        elif desc == "Security Fee":
            tarifa = to_float(df.at[i, "Tarifa"], 990.0)
            cantidad = to_float(df.at[i, "Cantidad"], 1.0)
            amount = tarifa * cantidad
            remark = "Considers Pier Asimar"

        elif desc == "Security fee Ventanas":
            amount = 3730.65
            remark = "Per call"

        elif desc == "Dockage":
            if port == "Valparaíso TPV":
                amount = 1.18 * loa * port_stay
                remark = "USD 1.18 *LOA*Hrs"
            elif port == "Valparaíso TPS":
                amount = 2.27 * loa * port_stay
                remark = "USD 2.27 *LOA*Hrs"
            elif port == "Mejillones - TGN 1":
                amount = 3.16 * loa * port_stay
                remark = "USD 3.16 *LOA*Hrs"
            elif port == "Mejillones - TGN 2":
                amount = 3.16 * loa * port_stay
                remark = "USD 3.16 *LOA*Hrs"
            elif port == "Mejillones - Pto Angamos":
                amount = 2.92 * loa * port_stay
                remark = "USD 2.92 *LOA*Hrs"

        elif desc == "Dockage Per Add Hr":
            # Ventanas: extra hours si > 12, tarifa depende de Dockage Fixed selector
            if port == "Ventanas" and port_stay and float(port_stay) > 12:
                extra_hours = float(port_stay) - 12
                tarifa_hr = 0
                if "63657" in dockage_fixed_sel:
                    tarifa_hr = 972
                elif "68660" in dockage_fixed_sel:
                    tarifa_hr = 1056
                if tarifa_hr > 0:
                    amount = extra_hours * tarifa_hr
                    tarifa_formatted = f"{tarifa_hr:,.0f}".replace(",", ".")
                    remark = f"USD ${tarifa_formatted}/Hr Each Additional Hr"

        elif desc == "Port Pilotage":
            cantidad = max(to_float(df.at[i, "Cantidad"], 0.0), 0.0)
            if cantidad <= 0:
                cantidad = 1.0
            if 50 <= gt <= 6000:
                amount = ((169.92 + (0.0267 * gt)) * 1) * cantidad
            elif 6001 <= gt <= 16000:
                amount = ((207.68 + (0.0306 * gt)) * 1) * cantidad
            elif 16001 <= gt <= 40000:
                amount = ((245.46 + (0.0315 * gt)) * 1) * cantidad
            elif 40001 <= gt <= 60000:
                amount = ((377.66 + (0.0336 * gt)) * 1) * cantidad
            elif gt >= 60001:
                amount = ((576.36 + (0.0343 * gt)) * 1) * cantidad
            remark = f"USD {amount:,.2f} Mooring / Unmooring (estimated {int(cantidad)})"

        elif desc == "Port Pilotage For Anchor":
            cantidad = max(to_float(df.at[i, "Cantidad"], 0.0), 0.0)
            if cantidad <= 0:
                cantidad = 1.0
            if 50 <= gt <= 6000:
                amount = ((169.92 + (0.0267 * gt)) * 0.5) * cantidad
            elif 6001 <= gt <= 16000:
                amount = ((207.68 + (0.0306 * gt)) * 0.5) * cantidad
            elif 16001 <= gt <= 40000:
                amount = ((245.46 + (0.0315 * gt)) * 0.5) * cantidad
            elif 40001 <= gt <= 60000:
                amount = ((377.66 + (0.0336 * gt)) * 0.5) * cantidad
            elif gt >= 60001:
                amount = ((576.36 + (0.0343 * gt)) * 0.5) * cantidad
            remark = f"USD {amount:,.2f} Per Maneuver (estimated {int(cantidad)})"

        elif desc == "Port Pilotage For Shiftings":
            cantidad = max(to_float(df.at[i, "Cantidad"], 0.0), 0.0)
            if cantidad <= 0:
                cantidad = 1.0
            if 50 <= gt <= 6000:
                amount = ((169.92 + (0.0267 * gt)) * 0.2) * cantidad
            elif 6001 <= gt <= 16000:
                amount = ((207.68 + (0.0306 * gt)) * 0.2) * cantidad
            elif 16001 <= gt <= 40000:
                amount = ((245.46 + (0.0315 * gt)) * 0.2) * cantidad
            elif 40001 <= gt <= 60000:
                amount = ((377.66 + (0.0336 * gt)) * 0.2) * cantidad
            elif gt >= 60001:
                amount = ((576.36 + (0.0343 * gt)) * 0.2) * cantidad
            remark = f"USD {amount:,.2f} Per Shiftings (estimated {int(cantidad)})"

        elif desc == "Pilot Waiting Time":
            cantidad = max(to_float(df.at[i, "Cantidad"], 0.0), 0.0)
            tarifapw = 63.93
            amount = tarifapw * cantidad
            if cantidad > 0:
                remark = "USD 63,93 Charge per hour"

        elif desc == "Shore tension system":
            if port_stay > 0:
                tarifashore = 1677
                turnosh = port_stay / 8
                turnoshh = math.floor(turnosh + 0.5)
                amount = (tarifashore * turnoshh) + 1400
                remark = f"Installation USD 700*2 + USD 1677 per shift estimated ({turnoshh})"

        elif desc == "Loading Master":
            if port_stay > 0:
                tarifal = 2866.50
                turno = port_stay / 8
                turnos = math.floor(turno + 0.5)
                amount = tarifal * turnos
                remark = f"USD {tarifal:,.2f} per shift estimated ({turnos})"

        elif desc == "Pre Pilotage":
            amount = (gt / 1000) * 30.49
            remark = ""

        elif desc in ["Channel Pilotage", "Channel Pilotage-Felix", "Full Channel Pilotage"]:
            # Aquí puedes pegar 1:1 tu tabla completa (como en Tkinter).
            # Por ahora lo dejo como placeholder 0 si no se usa.
            amount = 0.0
            remark = ""

        elif desc == "Vat Recovery Fee":
            # Se calcula después
            amount = 0.0
            remark = ""

        df.at[i, "Amount"] = float(amount or 0.0)
        df.at[i, "Remarks"] = remark or ""

    # 2) Subtotal sin Vat Recovery Fee
    subtotal = float(df.loc[df["Description"] != "Vat Recovery Fee", "Amount"].sum())

    # 3) VAT según reglas
    iva_base = 0.0
    for i in range(len(df)):
        desc = (df.at[i, "Description"] or "").strip()
        if not desc or desc == "Vat Recovery Fee":
            continue
        if tiene_iva(port, desc, purpose):
            iva_base += float(df.at[i, "Amount"] or 0.0)

    vat = iva_base * 0.19

    # 4) VAT Recovery Fee
    vat_recovery_fee = 0.0
    for i in range(len(df)):
        if (df.at[i, "Description"] or "").strip() == "Vat Recovery Fee":
            if vat_recovery_enabled:
                vat_recovery_fee = vat * 0.08
                df.at[i, "Amount"] = float(vat_recovery_fee)
                df.at[i, "Remarks"] = f"Basis 8% of VAT (USD {vat:,.2f})"
            else:
                df.at[i, "Amount"] = 0.0
                df.at[i, "Remarks"] = ""
            break

    total = subtotal + vat + vat_recovery_fee
    return df, subtotal, vat, total


def generar_pdf_bytes(vessel_name: str, port_call: str, to_value: str, gt: str, loa: str, purpose: str, port_stay: str, cargo_text: str, rate_text: str,
                      df: pd.DataFrame, subtotal: float, vat: float, total: float):
    buf = BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # Logo (si existe)
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo_lbh.png")
    logo_y = height - 2.3 * inch
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, 0.1*inch, logo_y, width=2.1*inch, height=2.1*inch, preserveAspectRatio=True, mask='auto')
        except:
            pass

    # Header derecho
    y_pos = height - 1.0*inch
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 0.5*inch, y_pos, "LBH Chile SPA.")
    y_pos -= 0.15*inch
    c.setFont("Helvetica", 9)
    c.drawRightString(width - 0.5*inch, y_pos, "Cocharne 639, Of 111")
    y_pos -= 0.15*inch
    c.drawRightString(width - 0.5*inch, y_pos, "Floor 11")
    y_pos -= 0.15*inch
    c.drawRightString(width - 0.5*inch, y_pos, "Valparaíso,")
    y_pos -= 0.15*inch
    c.drawRightString(width - 0.5*inch, y_pos, "Chile")

    # Título
    y_pos = height - 1.7*inch
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width/2, y_pos, "Proforma Disbursement Account")

    # Links
    y_pos -= 0.2*inch
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.blue)
    c.drawCentredString(width/2, y_pos, "Agency@lbhchile.com")
    y_pos -= 0.18*inch
    c.drawCentredString(width/2, y_pos, "www.LBH-Group.com")
    c.setFillColor(colors.black)

    # Date
    y_pos -= 0.5*inch
    c.setFont("Helvetica", 9)
    fecha_actual = datetime.now().strftime("%B %d, %Y")
    c.drawRightString(width - 2.4*inch, y_pos, "Date")
    c.drawRightString(width - 0.5*inch, y_pos, fecha_actual)

    # Linea
    y_pos -= 0.15*inch
    c.setStrokeColor(colors.HexColor("#CCCCCC"))
    c.setLineWidth(1)
    c.line(0.5*inch, y_pos, width - 0.5*inch, y_pos)

    # To
    y_pos -= 0.25*inch
    c.drawString(0.5*inch, y_pos, "To")
    c.drawString(1.8*inch, y_pos, to_value or "")

    # Vessel block
    y_pos -= 0.2*inch
    c.setFont("Helvetica", 9)
    c.drawString(0.5*inch, y_pos, "Vessel name")
    c.drawString(1.8*inch, y_pos, vessel_name or "")
    c.drawString(4.5*inch, y_pos, "GT")
    c.drawString(5.8*inch, y_pos, gt or "")

    y_pos -= 0.18*inch
    c.drawString(0.5*inch, y_pos, "Port of call")
    c.drawString(1.8*inch, y_pos, port_call or "")
    c.drawString(4.5*inch, y_pos, "LOA")
    c.drawString(5.8*inch, y_pos, loa or "")

    y_pos -= 0.18*inch
    c.drawString(0.5*inch, y_pos, "Purpose of call")
    c.drawString(1.8*inch, y_pos, purpose or "")
    c.drawString(4.5*inch, y_pos, "Port Stay (hrs)")
    c.drawString(5.8*inch, y_pos, port_stay or "0")

    y_pos -= 0.18*inch
    c.drawString(0.5*inch, y_pos, "Cargo")
    c.drawString(1.8*inch, y_pos, cargo_text or "")
    c.drawString(4.5*inch, y_pos, "Rate")
    c.drawString(5.8*inch, y_pos, rate_text or "")

    # Linea
    y_pos -= 0.15*inch
    c.setStrokeColor(colors.HexColor("#CCCCCC"))
    c.line(0.5*inch, y_pos, width - 0.5*inch, y_pos)

    # Title table
    y_pos -= 0.25*inch
    c.setFont("Helvetica-Bold", 11)
    c.drawString(0.5*inch, y_pos, "Vessel Port Expenses")

    # Header table
    col_num = 0.4 * inch
    col_desc = 0.7 * inch
    col_remarks = 3.3 * inch
    col_currency = 6.6 * inch
    col_amount = 7.7 * inch

    y_pos -= 0.25*inch
    c.setFillColor(colors.HexColor("#003D5C"))
    c.rect(0.5*inch, y_pos, width - 1*inch, 0.2*inch, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(col_desc, y_pos + 0.05*inch, "Description")
    c.drawCentredString(col_remarks, y_pos + 0.05*inch, "Remarks")
    c.drawCentredString(col_currency, y_pos + 0.05*inch, "Currency")
    c.drawRightString(col_amount, y_pos + 0.05*inch, "Amount")
    c.setFillColor(colors.black)

    # Rows
    y_pos -= 0.2*inch
    c.setFont("Helvetica", 9)
    row_num = 1

    # mostrar solo filas con descripción, máximo 20
    show = df.copy()
    show = show[show["Description"].astype(str).str.strip() != ""].head(20)

    for _, r in show.iterrows():
        desc = str(r["Description"])
        remark = str(r["Remarks"] or "")
        curr = str(r["Currency"] or "USD")
        amount = float(r["Amount"] or 0.0)

        c.drawString(col_num, y_pos, str(row_num))
        c.drawString(col_desc, y_pos, desc)
        remarks_width = 1.5 * inch
        remarks_x = col_remarks - (remarks_width / 2) + 0.05 * inch
        c.drawString(remarks_x, y_pos, remark[:75])
        c.drawCentredString(col_currency, y_pos, curr)
        c.drawRightString(col_amount, y_pos, f"{amount:,.2f}")

        y_pos -= 0.15*inch
        row_num += 1
        if y_pos < 2.5*inch:
            break

    # completar hasta 20
    while row_num <= 20 and y_pos > 2.5*inch:
        c.drawString(col_num, y_pos, str(row_num))
        c.drawString(col_desc, y_pos, "-")
        c.drawCentredString(col_remarks, y_pos, "-")
        c.drawCentredString(col_currency, y_pos, "USD")
        c.drawRightString(col_amount, y_pos, "-")
        y_pos -= 0.15*inch
        row_num += 1

    # line
    y_pos -= 0.1*inch
    c.setStrokeColor(colors.HexColor("#CCCCCC"))
    c.setLineWidth(1)
    c.line(0.5*inch, y_pos, width - 0.5*inch, y_pos)

    # totals
    y_pos -= 0.25*inch
    c.setFont("Helvetica-Bold", 9)
    col_label = width - 2.3 * inch
    col_curr = width - 1.7 * inch
    col_amt = width - 0.5 * inch

    c.drawRightString(col_label, y_pos, "Sub total")
    c.drawCentredString(col_curr, y_pos, "USD")
    c.drawRightString(col_amt, y_pos, f"{subtotal:,.2f}")

    y_pos -= 0.2*inch
    c.setFillColor(colors.red)
    c.drawRightString(col_label, y_pos, "VAT (19%)")
    c.drawCentredString(col_curr, y_pos, "USD")
    c.drawRightString(col_amt, y_pos, f"{vat:,.2f}")
    c.setFillColor(colors.black)

    y_pos -= 0.25*inch
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(col_label, y_pos, "Total")
    c.drawCentredString(col_curr, y_pos, "USD")
    c.drawRightString(col_amt, y_pos, f"{total:,.2f}")

    c.save()
    buf.seek(0)
    return buf


# ----------------------------
# Session state init
# ----------------------------
if "df" not in st.session_state:
    st.session_state.df = ensure_rows(20)

if "ais_type" not in st.session_state:
    st.session_state.ais_type = ""

if "port" not in st.session_state:
    st.session_state.port = "Valparaíso TPV"

if "vat_recovery_enabled" not in st.session_state:
    st.session_state.vat_recovery_enabled = True

if "last_defaults_port" not in st.session_state:
    st.session_state.last_defaults_port = None


# ----------------------------
# Header UI
# ----------------------------
st.markdown(
    f"""
    <div style="background:{COLORS['primary_blue']};padding:14px;border-radius:10px;">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div style="color:{COLORS['gold']};font-size:24px;font-weight:800;">LBH GROUP</div>
        <div style="color:white;font-size:14px;font-weight:600;">Date: {datetime.now().strftime("%B %d, %Y")}</div>
      </div>
      <div style="color:white;font-size:12px;margin-top:4px;">CHILE - Maritime Agency Services</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div style="background:{COLORS['secondary_blue']};padding:10px;border-radius:10px;margin-top:10px;">
      <div style="color:white;font-size:18px;font-weight:800;text-align:center;">PROFORMA DISBURSEMENT ACCOUNT</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")


# ----------------------------
# Vessel info
# ----------------------------
c1, c2, c3, c4 = st.columns([2.2, 1.2, 1.2, 1.4])

with c1:
    to_value = st.text_input("To", key="to_value")
with c2:
    imo_raw = st.text_input("IMO", key="imo_raw")
    if st.button("🔍 Buscar IMO"):
        imo = clean_imo(imo_raw)
        if len(imo) < 7:
            st.warning("El IMO debe tener al menos 7 dígitos.")
        else:
            with st.spinner("Buscando datos por IMO..."):
                datos = buscar_por_imo(imo)
            if datos and (datos.get("gt") or datos.get("loa") or datos.get("vessel_name")):
                st.session_state.vessel_name = datos.get("vessel_name") or st.session_state.get("vessel_name", "")
                st.session_state.gt = str(int(datos["gt"])) if datos.get("gt") else st.session_state.get("gt", "")
                st.session_state.loa = str(int(datos["loa"])) if datos.get("loa") else st.session_state.get("loa", "")
                st.session_state.ais_type = datos.get("ais_type") or ""
                st.success("✓ Encontrado")
            else:
                st.error("✗ No encontrado")

with c3:
    vessel_name = st.text_input("Vessel name", key="vessel_name")
    gt = st.text_input("GT", key="gt")
with c4:
    port = st.selectbox(
        "Port of call",
        list(PORT_OPTIONS.keys()),
        index=list(PORT_OPTIONS.keys()).index(st.session_state.port) if st.session_state.port in PORT_OPTIONS else 0,
        key="port",
    )
    loa = st.text_input("LOA", key="loa")

purpose = st.selectbox("Purpose of call", ["Discharging", "Loading", "NIL"], key="purpose")
ais_type_show = st.session_state.ais_type or "-"
st.caption(f"**AIS Type:** {ais_type_show}")

# Cargo / Rate / Gang
cc1, cc2, cc3, cc4 = st.columns([1.8, 1.2, 1.2, 1.2])
with cc1:
    cargo = st.text_input("Cargo", key="cargo")
with cc2:
    cargo_mt = st.number_input("Total cargo", min_value=0.0, step=1.0, value=float(st.session_state.get("cargo_mt", 0.0)), key="cargo_mt")
with cc3:
    cargo_unit = st.selectbox("Unit", ["MT", "PCS"], key="cargo_unit")
with cc4:
    rate = st.number_input("Rate (Mt per day)", min_value=0.0, step=1.0, value=float(st.session_state.get("rate", 0.0)), key="rate")
gang = st.text_input("Gang", value=st.session_state.get("gang", "2 gang"), key="gang")

# Port stay
port_stay_calc = calcular_port_stay(float(cargo_mt or 0), float(rate or 0), purpose)
st.info(f"**Port Stay (hrs):** {port_stay_calc}")

# VAT Recovery toggle (global)
st.session_state.vat_recovery_enabled = st.checkbox("Incluir VAT Recovery Fee (8% de VAT)", value=st.session_state.vat_recovery_enabled)

st.divider()


# ----------------------------
# Defaults por puerto (auto)
# ----------------------------
if st.session_state.last_defaults_port != port:
    st.session_state.df = apply_port_defaults(st.session_state.df, port)
    st.session_state.last_defaults_port = port


# ----------------------------
# Editor de tabla
# ----------------------------
st.subheader("VESSEL PORT EXPENSES")

# Preparar opciones de Description (solo del puerto seleccionado)
desc_choices = [""] + PORT_OPTIONS.get(port, [])

df = st.session_state.df.copy()

# Ayuda para combos especiales: Light Dues / Dockage Fixed
# Usamos columna Selector y el usuario selecciona opción.
st.caption("Usa **Selector** para Light Dues y Dockage Fixed. Usa **Tarifa/Cantidad** para los ítems manuales.")

edited = st.data_editor(
    df,
    use_container_width=True,
    num_rows="fixed",
    column_config={
        "Description": st.column_config.SelectboxColumn("Description", options=desc_choices),
        "Currency": st.column_config.SelectboxColumn("Currency", options=[CURRENCY_DEFAULT]),
        "Selector": st.column_config.SelectboxColumn("Selector", options=[""] + LIGHT_DUES_CHOICES + DOCKAGE_FIXED_CHOICES),
        "Tarifa": st.column_config.TextColumn("Tarifa / Amount manual"),
        "Cantidad": st.column_config.TextColumn("Cantidad"),
        "Amount": st.column_config.NumberColumn("Amount (USD)", disabled=True, format="%.2f"),
        "Remarks": st.column_config.TextColumn("Remarks"),
    },
    key="data_editor",
)

# ----------------------------
# Calcular
# ----------------------------
gt_f = to_float(gt, 0.0)
loa_f = to_float(loa, 0.0)
df_calc, subtotal, vat, total = compute_expenses(
    edited,
    gt=gt_f,
    loa=loa_f,
    port_stay=float(port_stay_calc),
    port=port,
    purpose=purpose,
    ais_type=st.session_state.ais_type,
    vat_recovery_enabled=st.session_state.vat_recovery_enabled,
)

st.session_state.df = df_calc

t1, t2, t3 = st.columns(3)
t1.metric("Sub total (USD)", f"{subtotal:,.2f}")
t2.metric("VAT 19% (USD)", f"{vat:,.2f}")
t3.metric("TOTAL (USD)", f"{total:,.2f}")

st.divider()


# ----------------------------
# PDF
# ----------------------------
st.subheader("PDF")

cargo_text = f"{cargo} {cargo_unit} {cargo_mt}"
rate_text = f"{rate} Mt per day {gang}"

colpdf1, colpdf2 = st.columns([1, 2])
with colpdf1:
    if st.button("📄 Generar PDF"):
        if not (vessel_name or "").strip():
            st.warning("Ingresa Vessel name antes de generar el PDF.")
        else:
            buf = generar_pdf_bytes(
                vessel_name=vessel_name,
                port_call=port,
                to_value=to_value,
                gt=str(gt or ""),
                loa=str(loa or ""),
                purpose=purpose,
                port_stay=str(port_stay_calc),
                cargo_text=cargo_text,
                rate_text=rate_text,
                df=st.session_state.df,
                subtotal=subtotal,
                vat=vat,
                total=total,
            )
            st.session_state.pdf_bytes = buf.getvalue()
            st.success("PDF listo para descargar ✅")

with colpdf2:
    if "pdf_bytes" in st.session_state and st.session_state.pdf_bytes:
        fecha = datetime.now().strftime("%d-%m-%y")
        port_name = (port or "Port").strip().replace(" ", "-")
        filename = f"PDA-{(vessel_name or 'Vessel').strip()}-{port_name}-{fecha}.pdf"
        st.download_button(
            "⬇️ Descargar PDF",
            data=st.session_state.pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
        )
