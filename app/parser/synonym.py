import re
from typing import List, Optional
from app.database.repository import CacheRepository
from app.models.category import Category
from app.parser.base import ParsedResult


class SynonymParser:
    """Matches text keywords against cached Google Sheets categories and accounts."""

    DEFAULT_CATEGORIES = [
        Category.from_raw_keywords("1", "Household", "Expense", "Belanja Dapur", "sayuran, sayur, sayur-sayuran, sayur2an, sayur-mayur, beras, minyak, bumbu, daging, telur, ayam, ikan, udang, cabai, cabe, bawang, tepung, tahu, tempe, buah, lauk, lauk pauk, belanja dapur, sembako, bahan dapur, bumbu dapur"),
        Category.from_raw_keywords("2", "Household", "Expense", "Tagihan", "listrik, air, wifi, pulsa, token, pdam, indihome, biznet, paket data"),
        Category.from_raw_keywords("3", "Household", "Expense", "Transport", "bensin, parkir, tol, ojol, grab, gojek, pertalite, pertamax, max, bbm, angkot, busway"),
        Category.from_raw_keywords("4", "Household", "Expense", "Jajan", "kopi, cemilan, es krim, boba, jajan, makan, makanan, minum, minuman, sarapan, makan siang, makan malam, warung, resto, restoran, cafe, bakery, kue"),
        Category.from_raw_keywords("5", "Household", "Expense", "Hiburan", "nonton, bioskop, game, netflix, spotify, youtube, steam, voucher"),
        Category.from_raw_keywords("6", "Household", "Expense", "Kesehatan", "obat, dokter, vitamin, apotek, puskesmas, rumah sakit, klinik"),
        Category.from_raw_keywords("7", "Household", "Expense", "Pendidikan", "buku, kursus, spp, sekolah, les, kuliah"),
        Category.from_raw_keywords("8", "Household", "Expense", "Rumah Tangga", "sabun, detergen, perkakas, perlengkapan, tisue, tisu, galon, kebersihan, pembersih"),
        Category.from_raw_keywords("9", "Household", "Expense", "Lainnya", "misc, pengeluaran lain"),
        Category.from_raw_keywords("10", "Household", "Income", "Gaji", "gaji, payroll, salary, insentif, thrum, bonus"),
        Category.from_raw_keywords("11", "Catering", "Income", "Penjualan", "pesanan, katering, nasi box, catering, order, menerima, pembayaran, pelunasan, tagihan, dp, lunas, bayaran, omset, penjualan, transferan, masuk"),
        Category.from_raw_keywords("12", "Catering", "Expense", "Bahan Baku", "sayuran, sayur, sayur-sayuran, sayur2an, sayur-mayur, ayam, daging, bumbu, beras, telur, ikan, udang, cabai, cabe, bawang, minyak, tepung, tahu, tempe, buah, bahan, lauk, lauk pauk, belanja, sembako, bahan baku, bumbu katering"),
        Category.from_raw_keywords("13", "Catering", "Expense", "Kemasan", "box, mika, plastik, sendok, sterofoam, dus, kemasan, kantong, thinwall, paperbowl"),
        Category.from_raw_keywords("14", "Catering", "Expense", "Gas", "elpiji, gas 3kg, gas 12kg, gas, lpg"),
    ]

    @classmethod
    def match_category(cls, text: str, business: str, tx_type: str) -> Optional[str]:
        """Match text against cached categories and their keywords."""
        categories: List[Category] = CacheRepository.get_cached_categories()
        if not categories:
            categories = cls.DEFAULT_CATEGORIES

        lower_text = text.lower()

        # 1. Filter categories by business and type first
        filtered = [c for c in categories if c.business.lower() == business.lower() and c.type.lower() == tx_type.lower()]
        if not filtered:
            filtered = categories

        # 2. Check exact category name match
        for cat in filtered:
            if cat.category_name.lower() in lower_text:
                return cat.category_name

        # 3. Check keyword matches
        for cat in filtered:
            for kw in cat.keywords:
                if kw and re.search(r"\b" + re.escape(kw.lower()) + r"\b", lower_text):
                    return cat.category_name

        return None

    @classmethod
    def enrich(cls, result: ParsedResult) -> ParsedResult:
        """Enrich a ParsedResult with matched category and boost confidence score."""
        if not result.success:
            return result

        matched_cat = cls.match_category(result.raw_text, result.business, result.type)
        if matched_cat:
            result.category = matched_cat
            result.confidence = min(100, result.confidence + 25)  # Boost confidence when category is matched
        else:
            result.confidence = max(50, result.confidence - 10)

        return result
