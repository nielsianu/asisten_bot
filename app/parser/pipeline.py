import logging
from app.parser.base import ParsedResult
from app.parser.rule import RuleParser
from app.parser.regex import RegexParser
from app.parser.synonym import SynonymParser
from app.ai.client import NineRouterClient

logger = logging.getLogger(__name__)


class ParserPipeline:
    """Multi-layered transaction parser engine following PRD & geminirules.
    Priority: Rule Engine -> Regex Parser -> Synonym Matcher -> 9Router AI Fallback.
    """

    @classmethod
    def parse(cls, text: str) -> ParsedResult:
        logger.info(f"Parsing input text: '{text}'")

        # 1. Rule Engine
        rule_res = RuleParser.parse(text)
        if rule_res.success:
            logger.info("RuleParser succeeded with 100% confidence.")
            return rule_res

        # 2. Regex Parser
        regex_res = RegexParser.parse(text)
        if regex_res.success:
            # 3. Synonym Enrichment
            enriched_res = SynonymParser.enrich(regex_res)
            logger.info(f"RegexParser + SynonymParser result: category='{enriched_res.category}', confidence={enriched_res.confidence}")
            return enriched_res

        # 4. 9Router AI Fallback for ambiguous text
        logger.info("Deterministic parsers failed. Attempting 9Router AI fallback...")
        ai_client = NineRouterClient()
        ai_res = ai_client.parse_ambiguous_text(text)
        if ai_res.success:
            logger.info(f"9Router AI succeeded with {ai_res.confidence}% confidence.")
            return ai_res

        logger.info("All parsers failed to extract valid transaction.")
        return ParsedResult(success=False, raw_text=text, parser_name="PipelineFallback")
