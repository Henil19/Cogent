"""
Sub-Module 4.4: Strategy Manager
Research basis: Adaptive-RAG (NAACL 2024), RealRoute (2026), Zhao et al. (2024)

Translates Layer 2 SourceTarget routing directives into concrete index partitions:
- LOCAL_DOCS -> searches local document partition
- LIVE_WEB -> searches live web partition
- HYBRID -> queries unified corpus
Includes intelligent fallback if targeted partition has no indexed documents.
"""

import logging
from typing import Optional, Tuple
from app.schemas.layer2 import SourceTarget

logger = logging.getLogger(__name__)


class StrategyManager:
    """
    Translates Layer 2 source routing into index partition constraints.
    """

    @staticmethod
    def resolve_partition(
        target_source: SourceTarget,
        local_count: int,
        web_count: int
    ) -> Tuple[str, Optional[str]]:
        """
        Determine target index partition and note any fallback warning.
        
        Returns:
            Tuple of (partition_name, warning_message_or_None)
        """
        warning = None

        if target_source == SourceTarget.LOCAL_DOCS:
            if local_count > 0:
                return "LOCAL_DOCS", None
            else:
                warning = f"LOCAL_DOCS partition empty ({local_count} docs). Falling back to ALL ({web_count} web docs)."
                logger.warning(warning)
                return "ALL", warning

        elif target_source == SourceTarget.LIVE_WEB:
            if web_count > 0:
                return "LIVE_WEB", None
            else:
                warning = f"LIVE_WEB partition empty ({web_count} docs). Falling back to ALL ({local_count} local docs)."
                logger.warning(warning)
                return "ALL", warning

        else:  # SourceTarget.HYBRID or unknown
            return "ALL", None
