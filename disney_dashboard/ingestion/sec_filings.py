"""SEC EDGAR connector — fetches Disney's latest SEC filings."""

from __future__ import annotations

from datetime import datetime
from typing import List

from disney_dashboard.config.settings import SEC_CIK
from disney_dashboard.ingestion.base import BaseConnector
from disney_dashboard.models.schemas import Signal, SourceType


class SECEdgarConnector(BaseConnector):
    source_type = SourceType.SEC_FILING
    source_name = "sec_edgar"

    SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
    FILING_TYPES = {"10-K", "10-Q", "8-K", "DEF 14A", "4"}

    def __init__(self, **kwargs) -> None:
        super().__init__(rate_limit=0.1, **kwargs)

    async def fetch(self) -> List[Signal]:
        cik_padded = SEC_CIK.zfill(10)
        url = self.SUBMISSIONS_URL.format(cik=cik_padded)

        data = await self._request(
            url,
            headers={
                "User-Agent": "DisneyDashboard research@example.com",
                "Accept": "application/json",
            },
        )

        signals: List[Signal] = []
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        descriptions = recent.get("primaryDocDescription", [])

        for i, form_type in enumerate(forms):
            if form_type not in self.FILING_TYPES:
                continue
            if i >= len(dates):
                break

            filing_date = dates[i]
            accession = accessions[i] if i < len(accessions) else ""
            description = descriptions[i] if i < len(descriptions) else ""
            accession_clean = accession.replace("-", "")
            filing_url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{SEC_CIK}/{accession_clean}/{accession}-index.htm"
            )

            try:
                pub_dt = datetime.strptime(filing_date, "%Y-%m-%d")
            except (ValueError, TypeError):
                pub_dt = datetime.utcnow()

            signals.append(
                Signal(
                    source_type=self.source_type,
                    source_name=self.source_name,
                    source_url=filing_url,
                    title=f"Disney SEC Filing: {form_type} — {description}",
                    body=f"Form {form_type} filed on {filing_date}. {description}",
                    published_at=pub_dt,
                    raw_payload={
                        "form_type": form_type,
                        "accession_number": accession,
                        "filing_date": filing_date,
                        "description": description,
                    },
                )
            )

        self.logger.info("SEC EDGAR returned %d filings", len(signals))
        return signals
