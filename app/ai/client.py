import json
import logging
import requests
from typing import Optional, Dict, Any
from app.config.settings import settings
from app.parser.base import ParsedResult

logger = logging.getLogger(__name__)


class NineRouterClient:
    """Client for 9Router OpenAI-compatible AI gateway."""

    def __init__(self):
        self.base_url = settings.ninerouter_base_url.rstrip("/")
        self.api_key = settings.ninerouter_api_key
        self.model = settings.ninerouter_model or "ag/gemini-3.6-flash-high"

    @staticmethod
    def _extract_content(response: requests.Response) -> str:
        """Extract content string from standard JSON or SSE stream response."""
        # 1. Try standard JSON
        try:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"] or ""
                if "text" in choice:
                    return choice["text"] or ""
        except Exception:
            pass

        # 2. Fallback to SSE Stream parsing (lines starting with 'data:')
        full_content = []
        for line in response.text.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    choices = chunk.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            full_content.append(content)
                        # Also check message.content if present in non-delta chunk
                        msg = choices[0].get("message", {})
                        if "content" in msg and msg["content"]:
                            full_content.append(msg["content"])
                except Exception:
                    continue

        return "".join(full_content).strip()

    def parse_ambiguous_text(self, text: str) -> ParsedResult:
        """Call 9Router LLM for natural language ambiguous parsing into structured JSON."""
        if not self.api_key:
            logger.warning("NINEROUTER_API_KEY is not set. Skipping AI fallback.")
            return ParsedResult(success=False, raw_text=text, parser_name="9RouterAI")

        system_prompt = (
            "You are a precise financial transaction parser for an Indonesian personal finance bot.\n"
            "Extract details from the user text and reply ONLY with a valid raw JSON object (no markdown, no backticks):\n"
            "{\n"
            '  "type": "Expense" | "Income" | "Transfer",\n'
            '  "business": "Household" | "Catering",\n'
            '  "category": string (e.g. Belanja Dapur, Tagihan, Transport, Jajan, Penjualan, Bahan Baku, Kemasan, Gas, Lainnya),\n'
            '  "account": string (e.g. Cash, Blu BCA, BCA, Mandiri, QRIS, E-Wallet),\n'
            '  "amount": number (numeric amount in IDR),\n'
            '  "description": string\n'
            "}\n"
            "Rules for category:\n"
            "- For groceries, food ingredients, vegetables ('sayuran', 'sayur'), spices, meats: use 'Belanja Dapur' if business is Household, or 'Bahan Baku' if business is Catering.\n"
            "- Avoid defaulting to 'Lainnya' unless no specific category fits."
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "temperature": 0.1,
            "max_tokens": 150
        }

        try:
            url = f"{self.base_url}/chat/completions"
            response = requests.post(url, json=payload, headers=headers, timeout=25)
            response.raise_for_status()

            content = self._extract_content(response)

            # Clean JSON formatting if enclosed in code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            parsed_data = json.loads(content)

            # Strict validation
            tx_type = parsed_data.get("type", "Expense")
            business = parsed_data.get("business", "Household")
            category = parsed_data.get("category", "Lainnya")
            account = parsed_data.get("account", "Cash")
            amount = float(parsed_data.get("amount", 0))
            description = parsed_data.get("description", text)

            if amount <= 0:
                return ParsedResult(success=False, raw_text=text, parser_name="9RouterAI")

            return ParsedResult(
                success=True,
                type=tx_type,
                business=business,
                category=category,
                account=account,
                amount=amount,
                description=description,
                confidence=85,  # AI parsed confidence
                raw_text=text,
                parser_name="9RouterAI"
            )

        except Exception as e:
            logger.error(f"9Router AI parse failed: {e}", exc_info=True)
            return ParsedResult(success=False, raw_text=text, parser_name="9RouterAI")

    def answer_financial_question(self, question: str, summary_data: Dict[str, Any]) -> Optional[str]:
        """Answer natural language financial questions using 9Router AI & financial context."""
        if not self.api_key:
            logger.warning("NINEROUTER_API_KEY is not set. Skipping AI Q&A.")
            return None

        accounts_list = summary_data.get("accounts", [])
        accounts_str = ", ".join([f"{a.account_name}: Rp {a.current_balance:,.0f}" for a in accounts_list]) if accounts_list else "Belum ada saldo"
        
        top_list = summary_data.get("top_expenses", [])
        top_exp_str = ", ".join([f"{cat}: Rp {amt:,.0f}" for cat, amt in top_list]) if top_list else "Belum ada pengeluaran"

        context_prompt = (
            f"Data Keuangan Pengguna Periode ({summary_data.get('month_label', 'Bulan Ini')}):\n"
            f"- Total Pemasukan: Rp {summary_data.get('total_income', 0):,.0f}\n"
            f"- Total Pengeluaran: Rp {summary_data.get('total_expense', 0):,.0f}\n"
            f"- Net Cash Flow: Rp {summary_data.get('net_cash_flow', 0):,.0f}\n"
            f"- Omset Usaha Katering: Rp {summary_data.get('catering_income', 0):,.0f}\n"
            f"- Laba Bersih Usaha Katering: Rp {summary_data.get('catering_profit', 0):,.0f}\n"
            f"- Saldo Akun: {accounts_str}\n"
            f"- Top Pengeluaran Kategori: {top_exp_str}\n"
        )

        system_prompt = (
            "Anda adalah Asisten Keuangan cerdas berbasis Bahasa Indonesia.\n"
            "Jawab pertanyaan pengguna tentang keuangannya secara ramah, singkat, jelas, dan akurat berdasarkan data berikut.\n"
            "Gunakan format penulisan angka Rupiah yang rapi (contoh: Rp 250.000).\n\n"
            f"{context_prompt}"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            "temperature": 0.3,
            "max_tokens": 250
        }

        try:
            url = f"{self.base_url}/chat/completions"
            response = requests.post(url, json=payload, headers=headers, timeout=25)
            response.raise_for_status()

            answer = self._extract_content(response)
            return answer if answer else None
        except Exception as e:
            logger.error(f"9Router AI Q&A failed: {e}", exc_info=True)
            return None
