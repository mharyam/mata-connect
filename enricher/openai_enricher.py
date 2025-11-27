"""
OpenAI enricher for community data enhancement.

Basic setup for using OpenAI's chat API to enrich community information.
"""

import os
import sys
import requests
from enum import Enum
from typing import Dict, Optional, List, Any
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool
from agents.agent_output import AgentOutputSchema
from pydantic import BaseModel


load_dotenv()


class CommunityInfo(BaseModel):
    name: str
    description: str
    short_description: str
    tags: List[str]
    website: str
    country: Optional[str]
    city: Optional[str]
    language: Optional[List[str]]
    contact_email: Optional[str]
    social_links: Dict[str, str]
    community_info: Dict[str, Any]
    member_count: Optional[int]
    pricing_model: Optional[str]
    focus_areas: Optional[str]


class CommunityTags(Enum):
    Tech = "Tech"
    Career = "Career"
    Community = "Community"
    Health = "Health"
    Finance = "Finance"
    Business = "Business"
    Parenting = "Parenting"
    Arts = "Arts"
    Education = "Education"
    Science = "Science"
    Engineering = "Engineering"
    Fitness = "Fitness"
    Wellness = "Wellness"


class OpenAIEnricher:
    """
    Basic OpenAI enricher for community data.
    """

    def __init__(self):
        """
        Initialize the OpenAI enricher.

        Args:
            api_key: OpenAI API key. If not provided, will use OPENAI_API_KEY env var.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required")

    @function_tool
    def fetch_url(community_url: str) -> str:
        """Fetch raw HTML of a URL and return cleaned visible text."""
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(community_url, headers=headers)
        response.raise_for_status()
        return response.text

    def enrich_community(
        self, community_url: str, data_source: str = "maryam_notes"
    ) -> CommunityInfo:
        """
        Enrich community data using OpenAI Chat Completions API.

        Args:
            community_url: URL of the community to enrich
            data_source: The source of the data

        Returns:
            Dictionary with enriched community data
        """

        available_tags = [
            "Tech",
            "Career",
            "Community",
            "Health",
            "Finance",
            "Business",
            "Parenting",
            "Arts",
            "Education",
            "Science",
            "Engineering",
            "Fitness",
            "Wellness",
        ]

        agent = Agent(
            name="Community Enricher",
            instructions=f"""
                You are a specialized community enrichment agent.
                Your task is to extract and structure comprehensive community information
                from the provided URL: {community_url}.
                Call the fetch_url tool to get the page content if needed.
                After analyzing the content, output a strict JSON object with the following
                fields and their corresponding data extracted from the website:
                - `name`: The full name of the community.
                - `description`: A descriptive paragraph about what the community is and does.
                - `short_description`: A single, concise sentence summarizing the community's purpose.
                - `website`: The official website URL of the community.
                - `tags`: An array of 1-3 relevant tags that best describe the community's focus.
                Pick ONLY the most accurate tags from this exact list: {available_tags}.
                Use 1 tag if that's the best fit, 2 if two are most relevant,
                or 3 if three are most appropriate. Do not create custom tags or use any other values.
                - `country`: The primary country where the community is based or focused.
                If a community has more than one country focus,
                choose the most relevant one or use Global where appropriate.
                Set to Global if it's a virtual-only community.
                - `city`: The primary city where the community is based or focused.
                Set to null if it's a virtual-only community.
                - `language`: An array of languages spoken or supported by the community.
                - `contact_email`: The primary email address for contacting the community.
                - `social_links`: A JSON object where keys are social media platform names
                (e.g., 'twitter', 'linkedin', 'facebook', 'youtube', 'github')
                and values are the URLs to the community's profiles.
                - `community_info`: Extract the best 3 key achievements, statistics, or unique features.
                Return as a JSON object with 0-3 items maximum.
                If you find 3 clear highlights, use all 3.
                If you find only 1-2 clear highlights, use only those.
                If no specific highlights are found, return an empty object {{}}.
                Number formatting rules:
                - If a number is 10,000 or above, round and convert it to a short form:
                    10,000 → "10K"
                    258,191 → "250K"
                    2,735,902 → "2.7M"
                - Round to 1 significant digit unless the number rounds cleanly
                    Examples:
                    12,345 → "12K"
                    248,999 → "250K"
                    3,400,000 → "3.4M"
                Use these formats:
                - Numbers/stats: {{"90%": "graduation rate", "75K": "members"}}
                - Features: {{"Global Reach": null, "Resource Library": null}}
                - Mixed: {{"179": "countries", "remote-first": null}}
                Only include information clearly stated on the website. Do not make up statistics.
                - `member_count`: The number of members in the community,
                if explicitly mentioned on the site. Extract the numeric value only.
                - `pricing_model`: The pricing model, if specified (e.g., 'free', 'freemium', 'paid').
                 - `data_source`: Pick this only from {data_source}.
                 - `focus_areas`: A comprehensive paragraph describing the specific areas, services,
                 and specializations this community focuses on.
                 Include key programs, target demographics,
                 main offerings, and unique features that make this community distinctive.
                 Write 2-4 sentences that capture the essence of what members can expect
                 and what problems the community solves.
                 Example: "financial literacy education for women entrepreneurs,
                 investment strategy workshops, retirement planning guidance,
                 debt management coaching, business funding resources,
                 networking events for female founders,
                 mentorship programs connecting experienced investors with newcomers".
                 Make it detailed enough for semantic search while keeping
                 it concise and focused on the community's core value propositions.
                Be thorough and return a value for every field. If a piece of information is not found,
                use a value of `null` for strings and numbers, and `[]` or {{}} for arrays and objects,
                respectively, to maintain the strict JSON structure.
            """,
            # model_settings=(temperature=0.3),
            tools=[self.fetch_url],
            output_type=AgentOutputSchema(CommunityInfo, strict_json_schema=False),
        )

        result = Runner.run_sync(
            agent,
            f"Enrich this community site: {community_url}",
        )

        data = result.final_output_as(CommunityInfo)
        return data


if __name__ == "__main__":
    enricher = OpenAIEnricher()
    # Use sys.argv to get command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python3 openai_enricher.py <url1> [<url2> ...]")
        sys.exit(1)

    # sys.argv[0] is the script name; slice from 1 to get the URLs
    community_sites = sys.argv[1:]

    for site in community_sites:
        print(f"Url No: {community_sites.index(site) + 1}/{len(community_sites)}")
        print(f"--- Enriching community site: {site} ---")
        try:
            # 1. Enrich the data
            enriched_data = enricher.enrich_community(site)

            # 2. Print the enriched data as clean, indented JSON
            print(enriched_data.model_dump_json(indent=2))

        except Exception as e:
            print(f"❌ Failed to process {site}: {e}")

        print("-" * 50)
