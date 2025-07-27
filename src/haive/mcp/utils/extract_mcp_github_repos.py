#!/usr/bin/env python3
"""Enhanced MCP Repository Extractor with README Processing

This script:
1. Extracts repository URLs from awesome-mcp-servers
2. Downloads and processes README files
3. Converts to LangChain Documents with metadata
4. Organizes resources for agent access
"""

import asyncio
import hashlib
import json
import os
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import aiohttp
import yaml
from langchain_core.documents import Document
from pydantic import BaseModel, ConfigDict, Field, field_validator
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()


class MCPCategory(str, Enum):
    """MCP Server Categories"""

    FILE_SYSTEMS = "File Systems"
    SANDBOX_VIRTUALIZATION = "Sandbox & Virtualization"
    VERSION_CONTROL = "Version Control"
    CLOUD_STORAGE = "Cloud Storage"
    DATABASES = "Databases"
    COMMUNICATION = "Communication"
    MONITORING = "Monitoring"
    SEARCH_WEB = "Search & Web"
    LOCATION_SERVICES = "Location Services"
    MARKETING = "Marketing"
    NOTE_TAKING = "Note Taking"
    CLOUD_PLATFORMS = "Cloud Platforms"
    WORKFLOW_AUTOMATION = "Workflow Automation"
    SYSTEM_AUTOMATION = "System Automation"
    SOCIAL_MEDIA = "Social Media"
    GAMING = "Gaming"
    FINANCE = "Finance"
    RESEARCH_DATA = "Research & Data"
    AI_SERVICES = "AI Services"
    DEVELOPMENT_TOOLS = "Development Tools"
    DATA_VISUALIZATION = "Data Visualization"
    IDENTITY = "Identity"
    AGGREGATORS = "Aggregators"
    LANGUAGE_TRANSLATION = "Language & Translation"
    SECURITY = "Security"
    IOT = "IoT"
    ART_LITERATURE = "Art & Literature"
    OTHER = "Other"


class MCPLanguage(str, Enum):
    """Programming Languages"""

    PYTHON = "Python"
    TYPESCRIPT_JAVASCRIPT = "TypeScript/JavaScript"
    GO = "Go"
    RUST = "Rust"
    CSHARP = "C#"
    JAVA = "Java"
    C_CPP = "C/C++"
    OTHER = "Other"


class MCPPlatform(str, Enum):
    """Supported Platforms"""

    MACOS = "macOS"
    WINDOWS = "Windows"
    LINUX = "Linux"
    CROSS_PLATFORM = "Cross-Platform"


class MCPScope(str, Enum):
    """Server Scope"""

    CLOUD = "cloud"
    LOCAL = "local"
    EMBEDDED = "embedded"


class MCPServerMetadata(BaseModel):
    """Metadata for an MCP Server"""

    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, use_enum_values=True
    )

    name: str = Field(..., description="Server name")
    owner: str = Field(..., description="GitHub owner/organization")
    repo_name: str = Field(..., description="Repository name")
    repo_url: str = Field(..., description="Full GitHub repository URL")
    description: str | None = Field(None, description="Server description")
    category: MCPCategory = Field(MCPCategory.OTHER, description="Server category")
    languages: list[MCPLanguage] = Field(
        default_factory=list, description="Programming languages used"
    )
    is_official: bool = Field(
        False, description="Whether this is an official implementation"
    )
    platforms: list[MCPPlatform] = Field(
        default_factory=list, description="Supported platforms"
    )
    scopes: list[MCPScope] = Field(
        default_factory=list, description="Server scopes (cloud/local/embedded)"
    )
    stars: int | None = Field(None, description="GitHub stars count")
    last_updated: datetime | None = Field(None, description="Last update timestamp")
    license: str | None = Field(None, description="License type")
    readme_url: str | None = Field(None, description="README URL")
    api_base_url: str | None = Field(None, description="GitHub API base URL")

    @field_validator("repo_url")
    @classmethod
    def validate_repo_url(cls, v: str) -> str:
        """Validate GitHub repository URL"""
        if not v.startswith(("https://github.com/", "http://github.com/")):
            raise ValueError("Invalid GitHub repository URL")
        return v

    def get_unique_id(self) -> str:
        """Generate unique ID for this server"""
        return f"{self.owner}/{self.repo_name}"

    def to_langchain_metadata(self) -> dict[str, Any]:
        """Convert to LangChain Document metadata format"""
        return {
            "source": self.repo_url,
            "server_name": self.name,
            "owner": self.owner,
            "repo_name": self.repo_name,
            "category": self.category,
            "languages": [lang for lang in self.languages],
            "is_official": self.is_official,
            "platforms": [platform for platform in self.platforms],
            "scopes": [scope for scope in self.scopes],
            "stars": self.stars,
            "last_updated": (
                self.last_updated.isoformat() if self.last_updated else None
            ),
            "license": self.license,
            "description": self.description,
        }


class MCPServerDocument(BaseModel):
    """Complete MCP Server Document"""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    metadata: MCPServerMetadata = Field(..., description="Server metadata")
    readme_content: str | None = Field(None, description="README content")
    extracted_at: datetime = Field(
        default_factory=datetime.now, description="Extraction timestamp"
    )
    content_hash: str | None = Field(None, description="SHA256 hash of README content")

    def compute_content_hash(self) -> str:
        """Compute SHA256 hash of README content"""
        if self.readme_content:
            return hashlib.sha256(self.readme_content.encode()).hexdigest()
        return ""

    def to_langchain_document(self) -> Document:
        """Convert to LangChain Document"""
        metadata = self.metadata.to_langchain_metadata()
        metadata.update(
            {
                "extracted_at": self.extracted_at.isoformat(),
                "content_hash": self.content_hash or self.compute_content_hash(),
                "document_type": "mcp_server_readme",
            }
        )

        return Document(
            page_content=self.readme_content
            or f"# {self.metadata.name}\n\nNo README content available.",
            metadata=metadata,
        )


class ExtractionStats(BaseModel):
    """Statistics for extraction process"""

    total_found: int = 0
    successfully_extracted: int = 0
    failed_extractions: int = 0
    categories: dict[str, int] = Field(default_factory=dict)
    languages: dict[str, int] = Field(default_factory=dict)
    extraction_duration: float | None = None


class MCPRepositoryExtractor:
    """Enhanced MCP Repository Extractor"""

    def __init__(self, output_dir: str = "agent_resources/mcp_servers"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.docs_dir = self.output_dir / "documents"
        self.metadata_dir = self.output_dir / "metadata"
        self.raw_dir = self.output_dir / "raw_readmes"

        for dir in [self.docs_dir, self.metadata_dir, self.raw_dir]:
            dir.mkdir(exist_ok=True)

        self.source_url = "https://github.com/TensorBlock/awesome-mcp-servers"
        self.session = None

        # Category mappings from emoji to enum
        self.category_mappings = {
            "📂": MCPCategory.FILE_SYSTEMS,
            "📦": MCPCategory.SANDBOX_VIRTUALIZATION,
            "🔄": MCPCategory.VERSION_CONTROL,
            "☁️": MCPCategory.CLOUD_STORAGE,
            "🗄️": MCPCategory.DATABASES,
            "💬": MCPCategory.COMMUNICATION,
            "📈": MCPCategory.MONITORING,
            "🔍": MCPCategory.SEARCH_WEB,
            "🗺️": MCPCategory.LOCATION_SERVICES,
            "🎯": MCPCategory.MARKETING,
            "📝": MCPCategory.NOTE_TAKING,
            "⚡": MCPCategory.CLOUD_PLATFORMS,
            "⚙️": MCPCategory.WORKFLOW_AUTOMATION,
            "🤖": MCPCategory.SYSTEM_AUTOMATION,
            "📱": MCPCategory.SOCIAL_MEDIA,
            "🎮": MCPCategory.GAMING,
            "💹": MCPCategory.FINANCE,
            "🧬": MCPCategory.RESEARCH_DATA,
            "🤝": MCPCategory.AI_SERVICES,
            "💻": MCPCategory.DEVELOPMENT_TOOLS,
            "📊": MCPCategory.DATA_VISUALIZATION,
            "🆔": MCPCategory.IDENTITY,
            "🔗": MCPCategory.AGGREGATORS,
            "💬": MCPCategory.LANGUAGE_TRANSLATION,
            "🔒": MCPCategory.SECURITY,
            "🔌": MCPCategory.IOT,
            "🧑‍🎨": MCPCategory.ART_LITERATURE,
        }

        # Language indicators
        self.language_indicators = {
            "🐍": MCPLanguage.PYTHON,
            "📇": MCPLanguage.TYPESCRIPT_JAVASCRIPT,
            "🏎️": MCPLanguage.GO,
            "🦀": MCPLanguage.RUST,
            "#️⃣": MCPLanguage.CSHARP,
            "☕": MCPLanguage.JAVA,
            "🌊": MCPLanguage.C_CPP,
        }

        # Platform indicators
        self.platform_indicators = {
            "🍎": MCPPlatform.MACOS,
            "🪟": MCPPlatform.WINDOWS,
            "🐧": MCPPlatform.LINUX,
        }

        # Scope indicators
        self.scope_indicators = {
            "☁️": MCPScope.CLOUD,
            "🏠": MCPScope.LOCAL,
            "📟": MCPScope.EMBEDDED,
        }

        self.stats = ExtractionStats()

    async def extract_repositories_from_readme(self) -> list[MCPServerMetadata]:
        """Extract repository information from the awesome-mcp-servers README"""
        try:
            # Fetch the raw README content
            raw_url = "https://raw.githubusercontent.com/TensorBlock/awesome-mcp-servers/main/README.md"
            async with self.session.get(raw_url) as response:
                readme_content = await response.text()

            repositories = []
            current_category = MCPCategory.OTHER

            # Parse line by line
            lines = readme_content.split("\n")

            # Regex patterns
            repo_pattern = re.compile(
                r"\[([^\]]+)\]\(https://github\.com/([^/]+)/([^)]+)\)"
            )
            official_pattern = re.compile(r"⭐|🎖️")

            for line in lines:
                # Check for category headers
                for emoji, category in self.category_mappings.items():
                    if emoji in line and line.strip().startswith(f"{emoji}"):
                        current_category = category
                        break

                # Extract repository links
                repo_matches = repo_pattern.findall(line)
                for match in repo_matches:
                    name, owner, repo_name = match
                    repo_url = f"https://github.com/{owner}/{repo_name}"

                    # Clean repo_name (remove any anchors or query params)
                    repo_name = repo_name.split("#")[0].split("?")[0]

                    # Check if official
                    is_official = bool(official_pattern.search(line))

                    # Extract languages, platforms, and scopes
                    languages = []
                    platforms = []
                    scopes = []

                    for indicator, language in self.language_indicators.items():
                        if indicator in line:
                            languages.append(language)

                    for indicator, platform in self.platform_indicators.items():
                        if indicator in line:
                            platforms.append(platform)

                    for indicator, scope in self.scope_indicators.items():
                        if indicator in line:
                            scopes.append(scope)

                    # Extract description (text after the dash)
                    desc_match = re.search(r"-\s+(.+?)(?:\[|$)", line)
                    description = desc_match.group(1).strip() if desc_match else None

                    # Create metadata object
                    metadata = MCPServerMetadata(
                        name=name.strip(),
                        owner=owner,
                        repo_name=repo_name,
                        repo_url=repo_url,
                        description=description,
                        category=current_category,
                        languages=languages or [MCPLanguage.OTHER],
                        is_official=is_official,
                        platforms=platforms or [MCPPlatform.CROSS_PLATFORM],
                        scopes=scopes or [MCPScope.LOCAL],
                    )

                    repositories.append(metadata)

            self.stats.total_found = len(repositories)
            return repositories

        except Exception as e:
            console.print(f"[red]Error extracting repositories: {e}[/red]")
            return []

    async def fetch_readme_content(self, metadata: MCPServerMetadata) -> str | None:
        """Fetch README content from GitHub"""
        try:
            # Try multiple README file names
            readme_names = ["README.md", "readme.md", "README.MD", "Readme.md"]

            for readme_name in readme_names:
                raw_url = f"https://raw.githubusercontent.com/{metadata.owner}/{metadata.repo_name}/main/{readme_name}"

                async with self.session.get(raw_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        metadata.readme_url = raw_url
                        return content

                # Try master branch
                raw_url = f"https://raw.githubusercontent.com/{metadata.owner}/{metadata.repo_name}/master/{readme_name}"

                async with self.session.get(raw_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        metadata.readme_url = raw_url
                        return content

            return None

        except Exception as e:
            console.print(
                f"[yellow]Error fetching README for {metadata.get_unique_id()}: {e}[/yellow]"
            )
            return None

    async def fetch_github_metadata(self, metadata: MCPServerMetadata) -> None:
        """Fetch additional metadata from GitHub API"""
        try:
            # Use GitHub API to get repo info
            api_url = (
                f"https://api.github.com/repos/{metadata.owner}/{metadata.repo_name}"
            )

            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "MCP-Repository-Extractor",
            }

            # Add GitHub token if available
            github_token = os.getenv("GITHUB_TOKEN")
            if github_token:
                headers["Authorization"] = f"token {github_token}"

            async with self.session.get(api_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()

                    metadata.stars = data.get("stargazers_count")
                    metadata.license = (
                        data.get("license", {}).get("name")
                        if data.get("license")
                        else None
                    )
                    metadata.last_updated = datetime.fromisoformat(
                        data.get("updated_at", "").replace("Z", "+00:00")
                    )
                    metadata.api_base_url = api_url

        except Exception as e:
            console.print(
                f"[yellow]Error fetching GitHub metadata for {metadata.get_unique_id()}: {e}[/yellow]"
            )

    async def process_repository(
        self, metadata: MCPServerMetadata
    ) -> MCPServerDocument | None:
        """Process a single repository"""
        try:
            # Fetch README content
            readme_content = await self.fetch_readme_content(metadata)

            # Fetch additional GitHub metadata
            await self.fetch_github_metadata(metadata)

            # Create document
            document = MCPServerDocument(
                metadata=metadata, readme_content=readme_content
            )

            # Compute content hash
            document.content_hash = document.compute_content_hash()

            return document

        except Exception as e:
            console.print(
                f"[red]Error processing {metadata.get_unique_id()}: {e}[/red]"
            )
            return None

    def save_documents(self, documents: list[MCPServerDocument]) -> None:
        """Save documents in various formats"""
        # Save as LangChain documents
        langchain_docs = []

        for doc in documents:
            # Save raw README
            if doc.readme_content:
                raw_path = (
                    self.raw_dir / f"{doc.metadata.owner}_{doc.metadata.repo_name}.md"
                )
                raw_path.write_text(doc.readme_content, encoding="utf-8")

            # Convert to LangChain document
            langchain_doc = doc.to_langchain_document()
            langchain_docs.append(langchain_doc)

            # Save individual document as JSON
            doc_path = (
                self.docs_dir / f"{doc.metadata.owner}_{doc.metadata.repo_name}.json"
            )
            doc_path.write_text(doc.model_dump_json(indent=2), encoding="utf-8")

        # Save all documents as a single JSON file
        all_docs_path = self.output_dir / "all_mcp_documents.json"
        all_docs_data = [doc.model_dump() for doc in documents]
        all_docs_path.write_text(
            json.dumps(all_docs_data, indent=2, default=str), encoding="utf-8"
        )

        # Save metadata summary
        metadata_summary = {
            "extraction_timestamp": datetime.now().isoformat(),
            "total_documents": len(documents),
            "stats": self.stats.model_dump(),
            "servers": [
                {
                    "id": doc.metadata.get_unique_id(),
                    "name": doc.metadata.name,
                    "category": doc.metadata.category,
                    "languages": doc.metadata.languages,
                    "url": doc.metadata.repo_url,
                }
                for doc in documents
            ],
        }

        summary_path = self.metadata_dir / "extraction_summary.json"
        summary_path.write_text(
            json.dumps(metadata_summary, indent=2, default=str), encoding="utf-8"
        )

        # Save as YAML for easy reading
        yaml_path = self.metadata_dir / "servers_overview.yaml"
        yaml_data = {
            "mcp_servers": [
                {
                    "name": doc.metadata.name,
                    "repo": doc.metadata.get_unique_id(),
                    "category": doc.metadata.category,
                    "description": doc.metadata.description,
                }
                for doc in documents
            ]
        }
        yaml_path.write_text(
            yaml.dump(yaml_data, default_flow_style=False), encoding="utf-8"
        )

    def generate_statistics_report(self, documents: list[MCPServerDocument]) -> None:
        """Generate statistics report"""
        # Update stats
        self.stats.successfully_extracted = len(
            [d for d in documents if d.readme_content]
        )
        self.stats.failed_extractions = (
            len(documents) - self.stats.successfully_extracted
        )

        # Count by category
        for doc in documents:
            category = doc.metadata.category
            self.stats.categories[category] = self.stats.categories.get(category, 0) + 1

        # Count by language
        for doc in documents:
            for lang in doc.metadata.languages:
                self.stats.languages[lang] = self.stats.languages.get(lang, 0) + 1

        # Create report table
        table = Table(title="MCP Repository Extraction Statistics", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Repositories Found", str(self.stats.total_found))
        table.add_row("Successfully Extracted", str(self.stats.successfully_extracted))
        table.add_row("Failed Extractions", str(self.stats.failed_extractions))

        console.print("\n", table)

        # Category breakdown
        cat_table = Table(title="Repositories by Category", show_header=True)
        cat_table.add_column("Category", style="cyan")
        cat_table.add_column("Count", style="green")

        for category, count in sorted(
            self.stats.categories.items(), key=lambda x: x[1], reverse=True
        ):
            cat_table.add_row(category, str(count))

        console.print("\n", cat_table)

        # Language breakdown
        lang_table = Table(title="Repositories by Language", show_header=True)
        lang_table.add_column("Language", style="cyan")
        lang_table.add_column("Count", style="green")

        for language, count in sorted(
            self.stats.languages.items(), key=lambda x: x[1], reverse=True
        ):
            lang_table.add_row(language, str(count))

        console.print("\n", lang_table)

    async def extract_all(self) -> list[MCPServerDocument]:
        """Main extraction method"""
        start_time = datetime.now()

        console.print("[bold blue]MCP Repository Extractor[/bold blue]")
        console.print(f"Output directory: {self.output_dir}")

        async with aiohttp.ClientSession() as session:
            self.session = session

            # Step 1: Extract repository information
            console.print(
                "\n[yellow]Step 1: Extracting repository information...[/yellow]"
            )
            repositories = await self.extract_repositories_from_readme()
            console.print(f"[green]Found {len(repositories)} repositories[/green]")

            # Step 2: Process repositories
            console.print("\n[yellow]Step 2: Processing repositories...[/yellow]")

            documents = []

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "Processing repositories...", total=len(repositories)
                )

                # Process in batches to avoid rate limiting
                batch_size = 10
                for i in range(0, len(repositories), batch_size):
                    batch = repositories[i : i + batch_size]

                    # Process batch concurrently
                    batch_tasks = [self.process_repository(repo) for repo in batch]
                    batch_results = await asyncio.gather(*batch_tasks)

                    # Add successful results
                    for doc in batch_results:
                        if doc:
                            documents.append(doc)

                    progress.update(task, advance=len(batch))

                    # Small delay to avoid rate limiting
                    if i + batch_size < len(repositories):
                        await asyncio.sleep(1)

            # Step 3: Save documents
            console.print("\n[yellow]Step 3: Saving documents...[/yellow]")
            self.save_documents(documents)

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            self.stats.extraction_duration = duration

            # Generate statistics
            self.generate_statistics_report(documents)

            console.print("\n[green]✓ Extraction complete![/green]")
            console.print(f"Duration: {duration:.2f} seconds")
            console.print(f"Output directory: {self.output_dir}")

            return documents


def create_agent_loader(output_dir: str = "agent_resources/mcp_servers") -> callable:
    """Create a loader function for agents to access MCP documents"""

    def load_mcp_documents(
        category: MCPCategory | None = None,
        language: MCPLanguage | None = None,
        search_query: str | None = None,
    ) -> list[Document]:
        """Load MCP server documents with optional filtering"""
        # Load all documents
        all_docs_path = Path(output_dir) / "all_mcp_documents.json"

        if not all_docs_path.exists():
            return []

        with open(all_docs_path, encoding="utf-8") as f:
            docs_data = json.load(f)

        # Convert to MCPServerDocument objects
        documents = []
        for data in docs_data:
            # Handle datetime conversion
            if "extracted_at" in data:
                data["extracted_at"] = datetime.fromisoformat(data["extracted_at"])
            if (
                "metadata" in data
                and "last_updated" in data["metadata"]
                and data["metadata"]["last_updated"]
            ):
                data["metadata"]["last_updated"] = datetime.fromisoformat(
                    data["metadata"]["last_updated"]
                )

            doc = MCPServerDocument(**data)

            # Apply filters
            if category and doc.metadata.category != category:
                continue

            if language and language not in doc.metadata.languages:
                continue

            if search_query:
                search_text = f"{doc.metadata.name} {doc.metadata.description or ''} {doc.readme_content or ''}".lower()
                if search_query.lower() not in search_text:
                    continue

            documents.append(doc.to_langchain_document())

        return documents

    return load_mcp_documents


async def main():
    """Main function"""
    extractor = MCPRepositoryExtractor()
    documents = await extractor.extract_all()

    # Create a loader for agents
    loader = create_agent_loader()

    # Example usage
    console.print("\n[blue]Example usage:[/blue]")
    console.print("Loading all database-related MCP servers:")
    db_docs = loader(category=MCPCategory.DATABASES)
    console.print(f"Found {len(db_docs)} database servers")


if __name__ == "__main__":
    asyncio.run(main())
