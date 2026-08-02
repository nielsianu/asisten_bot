import re
from app.parser.base import ParsedResult


class RuleParser:
    """Explicit rule-based parser for structured commands."""

    @staticmethod
    def parse(text: str) -> ParsedResult:
        clean_text = text.strip()

        # Match /add <type> <amount> <category> <account> [description]
        # Example: /add expense 25000 jajan cash kopi sore
        add_match = re.match(
            r"^(?:/add\s+)?(expense|income|transfer)\s+(\d+(?:\.\d+)?)\s+([a-zA-Z0-9_\-]+)\s+([a-zA-Z0-9_\-]+)(?:\s+(.+))?$",
            clean_text, re.IGNORECASE
        )
        if add_match:
            tx_type = add_match.group(1).capitalize()
            amount = float(add_match.group(2))
            category = add_match.group(3).title()
            account = add_match.group(4).title()
            desc = add_match.group(5) or clean_text

            business = "Catering" if "katering" in desc.lower() or "catering" in desc.lower() else "Household"

            return ParsedResult(
                success=True,
                type=tx_type,
                business=business,
                category=category,
                account=account,
                amount=amount,
                description=desc,
                confidence=100,
                raw_text=text,
                parser_name="RuleParser"
            )

        return ParsedResult(success=False, raw_text=text, parser_name="RuleParser")
