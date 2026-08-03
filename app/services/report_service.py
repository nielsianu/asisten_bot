import os
import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless server environment
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

from app.models.transaction import Transaction
from app.database.repository import CacheRepository, TransactionRepository
from app.services.dashboard_service import MONTH_NAMES_ID, MONTH_MAP, parse_target_month

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating transaction text reports, monthly bar charts, and annual PDF reports."""

    @staticmethod
    def get_all_transactions() -> List[Transaction]:
        """Fetch transactions from Google Sheets with fallback to SQLite."""
        try:
            from app.sheets.client import SheetsClient
            client = SheetsClient()
            txs = client.fetch_all_transactions()
            if txs:
                TransactionRepository.sync_transactions_from_sheet(txs)
                return txs
        except Exception as e:
            logger.warning(f"Google Sheets fetch error in ReportService: {e}. Fallback to SQLite.")

        return TransactionRepository.get_recent_transactions(limit=5000)

    @classmethod
    def generate_transaction_report(cls, target_month: Optional[str] = None) -> List[str]:
        """Generate formatted transaction table text for Telegram for a specific month (YYYY-MM)."""
        if not target_month:
            target_month = datetime.now().strftime("%Y-%m")

        all_txs = cls.get_all_transactions()
        month_txs = [t for t in all_txs if t.date.startswith(target_month)]

        # Sort chronologically by date and time
        month_txs.sort(key=lambda t: (t.date, t.time))

        year_str, month_num = target_month.split("-")
        month_name = MONTH_NAMES_ID.get(month_num, month_num)
        header_title = f"📑 *LAPORAN TRANSAKSI ({month_name.upper()} {year_str})*"

        if not month_txs:
            return [f"{header_title}\n\n_Belum ada transaksi recorded untuk periode ini._"]

        # Build table header & rows
        lines = [header_title, ""]
        lines.append("```")
        lines.append(f"{'Date':<10} | {'Type':<7} | {'Description':<18} | {'Amount (Rp)':>12}")
        lines.append("-" * 57)

        total_income = 0.0
        total_expense = 0.0

        for t in month_txs:
            if t.type == "Income":
                total_income += t.amount
            elif t.type == "Expense":
                total_expense += t.amount

            # Truncate description to fit nicely in 18 characters
            desc = (t.description[:15] + "...") if len(t.description) > 18 else t.description
            amt_str = f"{t.amount:,.0f}".replace(",", ".")
            tx_type = "In" if t.type == "Income" else ("Out" if t.type == "Expense" else "Trf")

            lines.append(f"{t.date:<10} | {tx_type:<7} | {desc:<18} | {amt_str:>12}")

        lines.append("-" * 57)
        lines.append("```")
        lines.append(f"💵 *Total Pemasukan:* Rp {total_income:,.0f}")
        lines.append(f"💸 *Total Pengeluaran:* Rp {total_expense:,.0f}")
        lines.append(f"⚖️ *Net Cash Flow:* Rp {(total_income - total_expense):,.0f}")

        full_text = "\n".join(lines)

        # Handle Telegram 4096 character limit safely
        if len(full_text) <= 3900:
            return [full_text]

        # Chunk into multi-part messages if too long
        chunks = []
        chunk_header = f"{header_title}\n\n```\n{'Date':<10} | {'Type':<7} | {'Description':<18} | {'Amount (Rp)':>12}\n" + "-" * 57 + "\n"
        current_chunk = chunk_header

        for line in lines[4:-5]:  # rows only
            if len(current_chunk) + len(line) + 50 > 3800:
                current_chunk += "```"
                chunks.append(current_chunk)
                current_chunk = chunk_header + line + "\n"
            else:
                current_chunk += line + "\n"

        current_chunk += "-" * 57 + "\n```\n"
        current_chunk += f"💵 *Total Pemasukan:* Rp {total_income:,.0f}\n"
        current_chunk += f"💸 *Total Pengeluaran:* Rp {total_expense:,.0f}\n"
        current_chunk += f"⚖️ *Net Cash Flow:* Rp {(total_income - total_expense):,.0f}"
        chunks.append(current_chunk)

        return chunks

    @classmethod
    def generate_monthly_chart(cls, output_path: str = "data/chart_monthly.png") -> str:
        """Generate bar chart of Expense (Red) vs Income (Green) per month across all recorded data."""
        all_txs = cls.get_all_transactions()

        # Group income & expense by month YYYY-MM
        monthly_income: Dict[str, float] = defaultdict(float)
        monthly_expense: Dict[str, float] = defaultdict(float)

        for t in all_txs:
            if not t.date or len(t.date) < 7:
                continue
            month_key = t.date[:7]  # YYYY-MM
            if t.type == "Income":
                monthly_income[month_key] += t.amount
            elif t.type == "Expense":
                monthly_expense[month_key] += t.amount

        months = sorted(set(list(monthly_income.keys()) + list(monthly_expense.keys())))

        if not months:
            # Fallback current month if empty
            months = [datetime.now().strftime("%Y-%m")]

        # Format month labels (e.g. "06/26" or "Jun 2026")
        formatted_labels = []
        for m in months:
            try:
                y, m_num = m.split("-")
                m_short = MONTH_NAMES_ID.get(m_num, m_num)[:3]
                formatted_labels.append(f"{m_short} {y[2:]}")
            except Exception:
                formatted_labels.append(m)

        incomes = [monthly_income[m] for m in months]
        expenses = [monthly_expense[m] for m in months]

        # Setup plot style
        fig, ax = plt.subplots(figsize=(10, 6), dpi=150)

        import numpy as np
        x = np.arange(len(months))
        width = 0.35

        rects1 = ax.bar(x - width/2, expenses, width, label='Pengeluaran (Expense)', color='#E53935', alpha=0.9)
        rects2 = ax.bar(x + width/2, incomes, width, label='Pemasukan (Income)', color='#4CAF50', alpha=0.9)

        ax.set_ylabel('Nominal (Rupiah)', fontsize=11, fontweight='bold')
        ax.set_title('Grafik Bulanan Pemasukan vs Pengeluaran', fontsize=14, fontweight='bold', pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(formatted_labels, fontsize=10, fontweight='bold')
        ax.legend(fontsize=10, loc='upper left')

        # Format Y axis currency
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda val, p: f"Rp {val*1e-3:,.0f}k" if val < 1e6 else f"Rp {val*1e-6:,.1f}M"))

        # Add grid lines
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        ax.set_axisbelow(True)

        # Add value labels on top of bars
        def autolabel(rects):
            for rect in rects:
                height = rect.get_height()
                if height > 0:
                    lbl = f"{height*1e-3:,.0f}k" if height < 1e6 else f"{height*1e-6:,.1f}M"
                    ax.annotate(lbl,
                                xy=(rect.get_x() + rect.get_width() / 2, height),
                                xytext=(0, 3),  # 3 points vertical offset
                                textcoords="offset points",
                                ha='center', va='bottom', fontsize=8, fontweight='bold')

        autolabel(rects1)
        autolabel(rects2)

        plt.tight_layout()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, format='png', bbox_inches='tight')
        plt.close(fig)

        logger.info(f"Monthly chart generated successfully at {output_path}")
        return output_path

    @classmethod
    def generate_annual_pdf_report(cls, target_year: Optional[str] = None, output_path: Optional[str] = None) -> str:
        """Generate a professional annual financial PDF report using ReportLab."""
        if not target_year:
            target_year = str(datetime.now().year)

        if not output_path:
            output_path = f"data/Laporan_Keuangan_{target_year}.pdf"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        all_txs = cls.get_all_transactions()
        year_txs = [t for t in all_txs if t.date.startswith(target_year)]

        # Calculate Executive Totals
        total_income = sum(t.amount for t in year_txs if t.type == "Income")
        total_expense = sum(t.amount for t in year_txs if t.type == "Expense")
        net_cash_flow = total_income - total_expense

        catering_income = sum(t.amount for t in year_txs if t.business == "Catering" and t.type == "Income")
        catering_expense = sum(t.amount for t in year_txs if t.business == "Catering" and t.type == "Expense")
        catering_profit = catering_income - catering_expense

        # Categories Breakdown
        household_expenses: Dict[str, float] = defaultdict(float)
        catering_expenses: Dict[str, float] = defaultdict(float)
        income_categories: Dict[str, float] = defaultdict(float)

        for t in year_txs:
            if t.type == "Income":
                income_categories[t.category] += t.amount
            elif t.type == "Expense":
                if t.business == "Catering":
                    catering_expenses[t.category] += t.amount
                else:
                    household_expenses[t.category] += t.amount

        # Monthly breakdown
        monthly_data = {m: {"inc": 0.0, "exp": 0.0} for m in [f"{target_year}-{m:02d}" for m in range(1, 13)]}
        for t in year_txs:
            m_key = t.date[:7]
            if m_key in monthly_data:
                if t.type == "Income":
                    monthly_data[m_key]["inc"] += t.amount
                elif t.type == "Expense":
                    monthly_data[m_key]["exp"] += t.amount

        # Build PDF Document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm
        )

        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#1A365D"),
            alignment=0,
            spaceAfter=4
        )

        subtitle_style = ParagraphStyle(
            'DocSubTitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#4A5568"),
            spaceAfter=15
        )

        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#2B6CB0"),
            spaceBefore=12,
            spaceAfter=8
        )

        normal_style = ParagraphStyle(
            'BodyNormal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#2D3748")
        )

        table_header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.white
        )

        story = []

        # Document Header
        story.append(Paragraph(f"LAPORAN KEUANGAN TAHUNAN ({target_year})", title_style))
        story.append(Paragraph(f"Asisten Keuangan Bot • Dicetak pada: {datetime.now().strftime('%d %B %Y %H:%M')}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#3182CE"), spaceAfter=15))

        # 1. Executive Summary Table
        story.append(Paragraph("1. Ringkasan Eksekutif Keuangan", section_heading))

        exec_data = [
            [Paragraph("Indikator Keuangan", table_header_style), Paragraph("Jumlah Nominal (Rp)", table_header_style)],
            [Paragraph("Total Pemasukan (All)", normal_style), f"Rp {total_income:,.0f}".replace(",", ".")],
            [Paragraph("Total Pengeluaran (All)", normal_style), f"Rp {total_expense:,.0f}".replace(",", ".")],
            [Paragraph("<b>Net Cash Flow Total</b>", normal_style), f"<b>Rp {net_cash_flow:,.0f}</b>".replace(",", ".")],
            [Paragraph("Omset Usaha Katering", normal_style), f"Rp {catering_income:,.0f}".replace(",", ".")],
            [Paragraph("Pengeluaran Usaha Katering", normal_style), f"Rp {catering_expense:,.0f}".replace(",", ".")],
            [Paragraph("<b>Laba Bersih Usaha Katering</b>", normal_style), f"<b>Rp {catering_profit:,.0f}</b>".replace(",", ".")]
        ]

        t_exec = Table(exec_data, colWidths=[10 * cm, 7.5 * cm])
        t_exec.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor("#2B6CB0")),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#F7FAFC"), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(t_exec)
        story.append(Spacer(1, 15))

        # 2. Subtotal Breakdown by Categories Table
        story.append(Paragraph("2. Subtotal Pengeluaran per Kategori", section_heading))

        cat_data = [
            [Paragraph("Kategori Pengeluaran", table_header_style), Paragraph("Sektor", table_header_style), Paragraph("Total Nominal (Rp)", table_header_style)]
        ]

        for cat_name, amt in sorted(household_expenses.items(), key=lambda x: x[1], reverse=True):
            cat_data.append([Paragraph(cat_name, normal_style), Paragraph("Household", normal_style), f"Rp {amt:,.0f}".replace(",", ".")])

        for cat_name, amt in sorted(catering_expenses.items(), key=lambda x: x[1], reverse=True):
            cat_data.append([Paragraph(cat_name, normal_style), Paragraph("Catering", normal_style), f"Rp {amt:,.0f}".replace(",", ".")])

        if len(cat_data) == 1:
            cat_data.append([Paragraph("Belum ada pengeluaran", normal_style), "-", "Rp 0"])

        t_cat = Table(cat_data, colWidths=[7.5 * cm, 4 * cm, 6 * cm])
        t_cat.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2C5282")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#EDF2F7"), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ]))
        story.append(t_cat)
        story.append(Spacer(1, 15))

        # 3. Monthly Financial Breakdown (12 Months)
        story.append(Paragraph("3. Rincian Keuangan Per Bulan", section_heading))

        month_rows = [
            [Paragraph("Bulan", table_header_style), Paragraph("Pemasukan (Rp)", table_header_style), Paragraph("Pengeluaran (Rp)", table_header_style), Paragraph("Net Cash Flow (Rp)", table_header_style)]
        ]

        for m_key in sorted(monthly_data.keys()):
            y, m_num = m_key.split("-")
            m_name = MONTH_NAMES_ID.get(m_num, m_num)
            inc = monthly_data[m_key]["inc"]
            exp = monthly_data[m_key]["exp"]
            net = inc - exp

            month_rows.append([
                Paragraph(f"{m_name} {y}", normal_style),
                f"Rp {inc:,.0f}".replace(",", "."),
                f"Rp {exp:,.0f}".replace(",", "."),
                f"Rp {net:,.0f}".replace(",", ".")
            ])

        t_month = Table(month_rows, colWidths=[5 * cm, 4.2 * cm, 4.2 * cm, 4.1 * cm])
        t_month.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A365D")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#F7FAFC"), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(t_month)

        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#A0AEC0"), spaceAfter=10))
        story.append(Paragraph("<i>Laporan keuangan ini dibuat secara otomatis oleh Bot Telegram Asisten Keuangan.</i>", ParagraphStyle('FooterNote', parent=styles['Italic'], fontSize=8, textColor=colors.HexColor("#718096"))))

        doc.build(story)
        logger.info(f"Annual PDF report generated successfully at {output_path}")
        return output_path

    @classmethod
    def generate_budget_report(cls, target_month: Optional[str] = None) -> str:
        """Generate remaining budget summary for specified month (YYYY-MM)."""
        if not target_month:
            target_month = datetime.now().strftime("%Y-%m")

        year_str, month_num = target_month.split("-")
        month_name = MONTH_NAMES_ID.get(month_num, month_num)

        # 1. Fetch budget reference limits from Google Sheets
        sheets_budgets = {}
        categories = []
        try:
            from app.sheets.client import SheetsClient
            client = SheetsClient()
            sheets_budgets = client.fetch_budgets()
            categories = client.fetch_categories()
        except Exception as e:
            logger.warning(f"Error fetching budget/category data from Sheets: {e}")
            categories = CacheRepository.get_cached_categories()

        # Default budget targets if sheet is empty or not configured
        default_budgets = {
            "Belanja Dapur": 2000000.0,
            "Tagihan": 1500000.0,
            "Transport": 500000.0,
            "Jajan": 500000.0
        }

        budget_limits = {**default_budgets, **sheets_budgets}

        # 2. Build Category -> Budget Category mapping
        cat_to_budget = {}
        for c in categories:
            if c.budget_category:
                cat_to_budget[c.category_name.lower()] = c.budget_category
            else:
                cat_to_budget[c.category_name.lower()] = c.category_name

        # 3. Fetch expenses for target month
        all_txs = cls.get_all_transactions()
        month_expenses = [t for t in all_txs if t.date.startswith(target_month) and t.type == "Expense"]

        spent_per_budget: Dict[str, float] = defaultdict(float)

        for t in month_expenses:
            cat_lower = t.category.lower()
            mapped_budget = cat_to_budget.get(cat_lower, t.category)

            # Match against known budget categories (case-insensitive)
            matched = None
            for b_name in budget_limits.keys():
                if b_name.lower() == mapped_budget.lower() or b_name.lower() in cat_lower or mapped_budget.lower() in b_name.lower():
                    matched = b_name
                    break

            if matched:
                spent_per_budget[matched] += t.amount

        # Build output message
        lines = [
            f"🎯 *RINGKASAN ANGGARAN BULANAN ({month_name.upper()} {year_str})*",
            ""
        ]

        total_budget = 0.0
        total_spent = 0.0

        for b_name, limit in budget_limits.items():
            spent = spent_per_budget.get(b_name, 0.0)
            remaining = limit - spent
            pct = (spent / limit * 100.0) if limit > 0 else 0.0

            total_budget += limit
            total_spent += spent

            status_icon = "⚠️ *Over Budget!*" if remaining < 0 else ""
            rem_sign = "-" if remaining < 0 else ""
            rem_abs = abs(remaining)

            lines.append(f"• *{b_name}*")
            lines.append(f"  - Budget: Rp {limit:,.0f}".replace(",", "."))
            lines.append(f"  - Terpakai: Rp {spent:,.0f} ({pct:.1f}%) {status_icon}".replace(",", "."))
            lines.append(f"  - 💵 Sisa: *{rem_sign}Rp {rem_abs:,.0f}*".replace(",", "."))
            lines.append("")

        lines.append("-" * 35)
        total_remaining = total_budget - total_spent
        total_pct = (total_spent / total_budget * 100.0) if total_budget > 0 else 0.0
        tot_rem_sign = "-" if total_remaining < 0 else ""
        tot_rem_abs = abs(total_remaining)

        lines.append(f"📊 *Total Budget:* Rp {total_budget:,.0f}".replace(",", "."))
        lines.append(f"💸 *Total Terpakai:* Rp {total_spent:,.0f} ({total_pct:.1f}%)".replace(",", "."))
        lines.append(f"💰 *Total Sisa Budget:* *{tot_rem_sign}Rp {tot_rem_abs:,.0f}*".replace(",", "."))

        return "\n".join(lines)
