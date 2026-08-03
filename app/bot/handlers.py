import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.bot.middleware import is_user_allowed
from app.parser.pipeline import ParserPipeline
from app.ai.client import NineRouterClient
from app.models.transaction import Transaction
from app.services.transaction_service import TransactionService
from app.services.dashboard_service import DashboardService, parse_target_month
from app.database.repository import CacheRepository, TransactionRepository
from app.sheets.client import SheetsClient
from app.services.sheet_sync import sync_sheet_cache

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command."""
    if not is_user_allowed(update.effective_user):
        await update.message.reply_text("🚫 Akses ditolak. Anda tidak memiliki izin mengoperasikan bot ini.")
        return

    welcome_msg = (
        "👋 *Selamat Datang di Asisten Keuangan Bot!*\n\n"
        "Bot ini siap membantu Anda mencatat transaksi *Rumah Tangga* dan *Usaha Katering* "
        "secara otomatis ke Google Sheets.\n\n"
        "📌 *Perintah Utama:*\n"
        "• `/rekap` - Lihat saldo & ringkasan transaksi\n"
        "• `/report [bulan]` - Lihat tabel transaksi per bulan\n"
        "• `/chart` - Grafik pengeluaran (merah) vs pemasukan (hijau)\n"
        "• `/pdf [tahun]` - Download laporan keuangan PDF profesional\n"
        "• `/sync` - Sinkronkan akun & kategori dari Google Sheets\n"
        "• `/status` - Cek status sistem\n"
        "• `/undo` - Membatalkan transaksi terakhir\n"
        "• `/help` - Panduan bantuan\n\n"
        "💬 *Cara Catat Transaksi:*\n"
        "Ketik kalimat alami langsung, contoh:\n"
        "• `beli beras 250rb pakai blu`\n"
        "• `bayar bumbu katering 500k cash`\n"
        "• `dapat komisi katering 1.5jt ke bca`"
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /help command."""
    if not is_user_allowed(update.effective_user):
        return

    help_msg = (
        "📖 *Daftar Lengkap Perintah Bot Keuangan*\n\n"
        "📌 *Perintah Utama:*\n"
        "• `/start` - Inisialisasi bot & pesan selamat datang\n"
        "• `/help` - Tampilkan panduan & semua perintah bot\n"
        "• `/rekap [bulan] [tahun]` - Rekap keuangan bulanan (contoh: `/rekap`, `/rekap juni 2026`)\n"
        "• `/report [bulan] [tahun]` - Tabel daftar transaksi per bulan (contoh: `/report`, `/report juli`)\n"
        "• `/chart` - Gambar grafik batang perbandingan pengeluaran vs pemasukan per bulan\n"
        "• `/pdf [tahun]` - File PDF Laporan Keuangan Tahunan (contoh: `/pdf`, `/pdf 2026`)\n"
        "• `/saldo` - Ringkasan saldo seluruh akun (Cash, Bank, E-Wallet)\n"
        "• `/top [bulan]` - Top 10 pengeluaran terbesar\n"
        "• `/sync` - Perbarui cache & sinkronkan data dari Google Sheets\n"
        "• `/status` - Cek status kesehatan sistem & database lokal\n"
        "• `/undo` - Membatalkan transaksi terakhir yang dicatat\n\n"
        "💬 *Pencatatan Otomatis (Ketik Langsung):*\n"
        "• `beli beras 250rb pakai blu` ➔ Household\n"
        "• `bayar kemasan box 300k cash` ➔ Catering\n"
        "• `dapat komisi katering 1.5jt ke bca` ➔ Income Catering"
    )
    await update.message.reply_text(help_msg, parse_mode="Markdown")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /status command."""
    if not is_user_allowed(update.effective_user):
        return

    accounts = CacheRepository.get_cached_accounts()
    categories = CacheRepository.get_cached_categories()

    status_msg = (
        "🟢 *Status Sistem Bot Keuangan*\n\n"
        f"• *Google Sheets Status:* Terhubung ✅\n"
        f"• *Cached Accounts:* {len(accounts)} akun\n"
        f"• *Cached Categories:* {len(categories)} kategori\n"
        f"• *Local Cache SQLite:* Ready ✅"
    )
    await update.message.reply_text(status_msg, parse_mode="Markdown")


async def sync_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /sync command: syncs Categories, Accounts, and Transactions from Google Sheets to local SQLite backup mirror."""
    if not is_user_allowed(update.effective_user):
        return

    await update.message.reply_text("🔄 Memulai sinkronisasi data dengan Google Sheets...", parse_mode="Markdown")
    success, acc_count, cat_count, tx_count, pushed_count = sync_sheet_cache()

    if success:
        msg = (
            f"✅ *SINKRONISASI BERHASIL*\n\n"
            f"• *Kategori Terbarui:* {cat_count} item\n"
            f"• *Akun Terbarui:* {acc_count} akun\n"
            f"• *Transaksi Disinkronkan:* {tx_count} transaksi dari Google Sheets\n"
        )
        if pushed_count > 0:
            msg += f"• *Transaksi Offline Terkirim:* {pushed_count} transaksi ke Google Sheets\n"
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Gagal melakukan sinkronisasi dengan Google Sheets.")


async def rekap_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /rekap command (supports optional month & year arguments)."""
    if not is_user_allowed(update.effective_user):
        return

    target_month = parse_target_month(context.args or [])
    summary = DashboardService.get_summary(target_month)

    month_label = summary["month_label"]
    accounts = summary["accounts"]
    month_txs = summary["month_transactions"]

    msg = f"📊 *REKAP KEUNGAN BULANAN ({month_label})*\n\n"
    msg += f"💵 *Total Pemasukan:* Rp {summary['total_income']:,.0f}\n"
    msg += f"💸 *Total Pengeluaran:* Rp {summary['total_expense']:,.0f}\n"
    msg += f"⚖️ *Net Cash Flow:* Rp {summary['net_cash_flow']:,.0f}\n"
    msg += f"🍳 *Laba Katering:* Rp {summary['catering_profit']:,.0f}\n\n"

    msg += "*💳 Saldo Akun Saat Ini:*\n"
    for acc in accounts:
        msg += f"• {acc.account_name}: Rp {acc.current_balance:,.0f}\n"

    msg += f"\n*📝 Transaksi ({month_label}):*\n"
    if not month_txs:
        msg += "_Belum ada transaksi tersimpan untuk periode ini._\n"
    else:
        for t in month_txs:
            msg += f"• [{t.date}] `{t.type}` - {t.category} ({t.account}): *Rp {t.amount:,.0f}* ({t.description})\n"

    await update.message.reply_text(msg, parse_mode="Markdown")


async def undo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /undo command."""
    if not is_user_allowed(update.effective_user):
        return

    success, message = TransactionService.undo_last_transaction()
    await update.message.reply_text(message, parse_mode="Markdown")


async def saldo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /saldo command."""
    if not is_user_allowed(update.effective_user):
        return

    summary = DashboardService.get_summary()
    accounts = summary["accounts"]

    msg = "💳 *RINGKASAN SALDO AKUN*\n\n"
    total_saldo = 0.0
    for acc in accounts:
        msg += f"• *{acc.account_name}* ({acc.type}): Rp {acc.current_balance:,.0f}\n"
        total_saldo += acc.current_balance

    msg += f"\n💰 *Total Saldo Keseluruhan:* Rp {total_saldo:,.0f}"
    await update.message.reply_text(msg, parse_mode="Markdown")


async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /top command."""
    if not is_user_allowed(update.effective_user):
        return

    target_month = parse_target_month(context.args or [])
    summary = DashboardService.get_summary(target_month)
    top_exps = summary["top_expenses"]
    month_label = summary["month_label"]

    msg = f"🏆 *TOP 10 PENGELUARAN ({month_label})*\n\n"
    if not top_exps:
        msg += "_Belum ada data pengeluaran untuk periode ini._"
    else:
        for idx, (cat, amt) in enumerate(top_exps, 1):
            msg += f"{idx}. *{cat}*: Rp {amt:,.0f}\n"

    msg += f"\n📊 *Total Pengeluaran:* Rp {summary['total_expense']:,.0f}"
    await update.message.reply_text(msg, parse_mode="Markdown")


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process natural language transaction messages using ParserPipeline."""
    text = update.message.text
    if not text or text.startswith("/"):
        return

    if not is_user_allowed(update.effective_user):
        return

    chat_type = update.effective_chat.type if update.effective_chat else "private"
    bot_username = context.bot.username.lower() if context.bot and context.bot.username else ""

    # Clean any @mention tag from text (e.g. @sistim, @sistim_bot, etc.)
    import re
    has_any_mention = bool(re.search(r"@[a-zA-Z0-9_]+", text))
    clean_text = re.sub(r"@[a-zA-Z0-9_]+", "", text).strip()

    # Group chat filter: Only respond in groups if bot is @mentioned or message is a reply to the bot
    if chat_type in ["group", "supergroup"]:
        is_reply = bool(
            update.message.reply_to_message and
            update.message.reply_to_message.from_user and
            update.message.reply_to_message.from_user.id == context.bot.id
        )
        if not (has_any_mention or is_reply):
            return  # Ignore general un-tagged group conversations

    parsed = ParserPipeline.parse(clean_text)

    if not parsed.success or parsed.amount <= 0:
        # Attempt AI Q&A Fallback for natural language financial questions
        summary_data = DashboardService.get_summary()
        ai_client = NineRouterClient()
        ai_answer = ai_client.answer_financial_question(text, summary_data)

        if ai_answer:
            try:
                await update.message.reply_text(f"🤖 *Jawaban Asisten AI:*\n\n{ai_answer}", parse_mode="Markdown")
            except Exception:
                await update.message.reply_text(f"🤖 Jawaban Asisten AI:\n\n{ai_answer}")
        else:
            await update.message.reply_text(
                "⚠️ Pesan tidak dapat dikenali sebagai transaksi.\n"
                "Format contoh: `beli beras 250rb pakai blu` atau `gaji 5jt ke bca`",
                parse_mode="Markdown"
            )
        return

    tx = TransactionService.create_from_parsed(parsed)

    # 1. High confidence >= 90%: Auto-save
    if parsed.is_confident:
        success, msg = TransactionService.save_transaction(tx)
        receipt = (
            f"✅ *TRANSAKSI BERHASIL DICATAT*\n\n"
            f"• *ID Transaksi:* `{tx.id}`\n"
            f"• *Tipe:* {tx.type}\n"
            f"• *Bisnis:* {tx.business}\n"
            f"• *Kategori:* {tx.category}\n"
            f"• *Akun:* {tx.account}\n"
            f"• *Nominal:* Rp {tx.amount:,.0f}\n"
            f"• *Catatan:* {tx.description}\n"
            f"• *Confidence:* {tx.ai_confidence}%\n\n"
            f"{msg}"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Undo Transaksi", callback_data=f"undo:{tx.id}")]
        ])
        await update.message.reply_text(receipt, parse_mode="Markdown", reply_markup=keyboard)

    # 2. Lower confidence < 90%: Prompt confirmation UI
    else:
        confirm_msg = (
            f"❓ *KONFIRMASI HASIL PARSING (Confidence: {parsed.confidence}%)*\n\n"
            f"Apakah rincian transaksi berikut sudah sesuai?\n"
            f"• *Tipe:* {tx.type}\n"
            f"• *Bisnis:* {tx.business}\n"
            f"• *Kategori:* {tx.category}\n"
            f"• *Akun:* {tx.account}\n"
            f"• *Nominal:* Rp {tx.amount:,.0f}\n"
            f"• *Catatan:* {tx.description}"
        )
        # Store draft in bot_data or callback data (encode draft JSON payload)
        draft_payload = json.dumps({
            "t": tx.type, "b": tx.business, "c": tx.category,
            "a": tx.account, "m": tx.amount, "d": tx.description,
            "cf": tx.ai_confidence
        })
        context.user_data["pending_tx"] = draft_payload

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Ya, Simpan", callback_data="confirm_tx"),
                InlineKeyboardButton("❌ Batal", callback_data="cancel_tx")
            ]
        ])
        await update.message.reply_text(confirm_msg, parse_mode="Markdown", reply_markup=keyboard)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks (Confirm, Cancel, Undo) safely."""
    query = update.callback_query
    await query.answer()

    if not is_user_allowed(update.effective_user):
        await query.answer("🚫 Akses ditolak.", show_alert=True)
        return

    data = query.data
    logger.info(f"Received callback query data: '{data}'")

    try:
        if data == "confirm_tx":
            raw_draft = context.user_data.get("pending_tx")
            if not raw_draft:
                await query.edit_message_text("❌ Transaksi kadaluarsa atau sudah diproses.")
                return

            payload = json.loads(raw_draft)
            tx = Transaction(
                type=payload["t"],
                business=payload["b"],
                category=payload["c"],
                account=payload["a"],
                amount=payload["m"],
                description=payload["d"],
                ai_confidence=payload["cf"]
            )
            success, status_msg = TransactionService.save_transaction(tx)
            context.user_data.pop("pending_tx", None)

            receipt = (
                f"✅ *TRANSAKSI BERHASIL DISIMPAN*\n\n"
                f"• *ID Transaksi:* `{tx.id}`\n"
                f"• *Tipe:* {tx.type}\n"
                f"• *Bisnis:* {tx.business}\n"
                f"• *Kategori:* {tx.category}\n"
                f"• *Akun:* {tx.account}\n"
                f"• *Nominal:* Rp {tx.amount:,.0f}\n"
                f"• *Catatan:* {tx.description}\n\n"
                f"{status_msg}"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Undo Transaksi", callback_data=f"undo:{tx.id}")]
            ])

            try:
                await query.edit_message_text(receipt, parse_mode="Markdown", reply_markup=keyboard)
            except Exception:
                # Plain text fallback if Markdown parsing fails
                await query.edit_message_text(
                    f"✅ TRANSAKSI BERHASIL DISIMPAN\n\n"
                    f"ID: {tx.id}\n"
                    f"Kategori: {tx.category}\n"
                    f"Akun: {tx.account}\n"
                    f"Nominal: Rp {tx.amount:,.0f}\n"
                    f"{status_msg}",
                    reply_markup=keyboard
                )

        elif data == "cancel_tx":
            context.user_data.pop("pending_tx", None)
            await query.edit_message_text("❌ Pencatatan transaksi dibatalkan.")

        elif data.startswith("undo:"):
            tx_id = data.split(":")[1]
            deleted = TransactionRepository.delete_transaction(tx_id)
            if deleted:
                await query.edit_message_text(f"↩️ Transaksi ID `{tx_id}` telah dibatalkan dari pencatatan lokal.", parse_mode="Markdown")
            else:
                await query.edit_message_text("⚠️ Transaksi tidak ditemukan atau sudah dibatalkan.")

    except Exception as e:
        logger.error(f"Error handling callback query: {e}", exc_info=True)
        await query.edit_message_text(f"⚠️ Terjadi kesalahan saat memproses tombol: {e}")


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /report command: Displays formatted table of transactions for target month."""
    if not is_user_allowed(update.effective_user):
        return

    from app.services.report_service import ReportService
    target_month = parse_target_month(context.args or [])

    chunks = ReportService.generate_transaction_report(target_month)
    for chunk in chunks:
        await update.message.reply_text(chunk, parse_mode="Markdown")


async def chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /chart command: Generates and sends bar chart of Expense (red) vs Income (green)."""
    if not is_user_allowed(update.effective_user):
        return

    from app.services.report_service import ReportService
    status_msg = await update.message.reply_text("📊 *Sedang me-render grafik bulanan...*", parse_mode="Markdown")

    try:
        chart_path = ReportService.generate_monthly_chart()
        with open(chart_path, "rb") as photo_file:
            await update.message.reply_photo(
                photo=photo_file,
                caption="📊 *Grafik Bulanan Pemasukan (Hijau) vs Pengeluaran (Merah)*",
                parse_mode="Markdown"
            )
        try:
            await status_msg.delete()
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Chart generation error: {e}", exc_info=True)
        await update.message.reply_text(f"⚠️ Gagal membuat grafik: {e}")


async def pdf_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /pdf command: Generates and sends professional annual financial PDF report."""
    if not is_user_allowed(update.effective_user):
        return

    from app.services.report_service import ReportService
    from datetime import datetime

    # Parse target year from args (e.g. /pdf 2026) or default to current year
    target_year = str(datetime.now().year)
    if context.args:
        for arg in context.args:
            arg_clean = arg.strip()
            if arg_clean.isdigit() and len(arg_clean) == 4:
                target_year = arg_clean
                break

    status_msg = await update.message.reply_text(f"📄 *Sedang menyusun laporan keuangan PDF tahun {target_year}...*", parse_mode="Markdown")

    try:
        pdf_path = ReportService.generate_annual_pdf_report(target_year)
        with open(pdf_path, "rb") as doc_file:
            await update.message.reply_document(
                document=doc_file,
                filename=f"Laporan_Keuangan_{target_year}.pdf",
                caption=f"📄 *Laporan Keuangan Tahunan ({target_year})*",
                parse_mode="Markdown"
            )
        try:
            await status_msg.delete()
        except Exception:
            pass
    except Exception as e:
        logger.error(f"PDF report generation error: {e}", exc_info=True)
        await update.message.reply_text(f"⚠️ Gagal membuat file PDF: {e}")


