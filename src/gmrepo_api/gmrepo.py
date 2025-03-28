"""
GMRepo Python Library

A clean, efficient interface to the GMRepo RESTful API.

Example Usage:

# Get all the microbes in GMrepo
all_microbes = gmrepo.get_all_gut_microbes()
print(all_microbes.keys())
all_microbes["all_species"].to_csv("./all_species.csv", index=False)
all_microbes["all_genus"].to_csv("./all_genus.csv", index=False)
print(all_microbes["metadata"])

# Get phenotypes associated with a taxon (species/genus)
taxon_phenotype_summary = gmrepo.get_taxon_phenotype_summary(40520)
taxon_phenotype_summary.to_csv("associateed_phenotypes.csv")

"""

from enum import StrEnum
import pandas as pd
import requests
from functools import lru_cache


class PhenotypeEndpoint(StrEnum):
    """Endpoints related to phenotype operations."""

    ALL_PHENOTYPES = "get_all_phenotypes"
    STATS_BY_MESH_ID = "getStatisticsByProjectsByMeshID"
    ASSOCIATED_SPECIES = "getAssociatedSpeciesByMeshID"
    ASSOCIATED_GENERA = "getAssociatedGeneraByMeshID"
    ASSOCIATED_PROJECTS = "getAssociatedProjectsByMeshID"
    COUNT_RUNS = "countAssociatedRunsByPhenotypeMeshID"
    ASSOCIATED_RUNS = "getAssociatedRunsByPhenotypeMeshIDLimit"
    MICROBE_ABUNDANCES = "getMicrobeAbundancesByPhenotypeMeshIDAndNCBITaxonID"


class TaxonEndpoint(StrEnum):
    """Endpoints related to taxon operations."""

    ALL_GUT_MICROBES = "get_all_gut_microbes"
    PHENOTYPES_SUMMARY = "getPhenotypesAndAbundanceSummaryOfAAssociatedTaxon"
    ASSOCIATED_PHENOTYPES = "getAssociatedPhenotypesAndAbundancesOfATaxon"
    RUN_DETAILS = "getRunDetailsByRunID"
    FULL_TAXONOMIC_PROFILE = "getFullTaxonomicProfileByRunID"


class ProjectEndpoint(StrEnum):
    """Endpoints related to project operations."""

    CURATED_PROJECTS = "getCuratedProjectsList"
    MICROBE_ABUNDANCES = "getMicrobeAbundancesByPhenotypeMeshIDAndProjectID"


class GMRepo:
    """
    Client for interacting with the GMRepo RESTful API.

    Example Usage:

    # Get all the microbes in GMrepo
    all_microbes = gmrepo.get_all_gut_microbes()
    print(all_microbes.keys())
    all_microbes["all_species"].to_csv("./all_species.csv", index=False)
    all_microbes["all_genus"].to_csv("./all_genus.csv", index=False)
    print(all_microbes["metadata"])

    # Get phenotypes associated with a taxon (species/genus)
    taxon_phenotype_summary = gmrepo.get_taxon_phenotype_summary(40520)
    taxon_phenotype_summary.to_csv("associateed_phenotypes.csv")

    """

    BASE_URL = "https://gmrepo.humangut.info/api/"

    def __init__(self):
        """Initialize the GMRepo client."""
        self.session = requests.Session()

    @lru_cache(maxsize=None)
    def _clean_str(self, s: str) -> str:
        """Efficiently remove `\r` and `\n` from strings using memoization."""
        return s.replace("\r", "").replace("\n", "").strip()

    def _clean_dict(self, obj):
        """Process only affected strings using a cached function."""
        if isinstance(obj, dict):
            return {k: self._clean_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_dict(v) for v in obj]
        elif isinstance(obj, str):
            return self._clean_str(obj)
        return obj

    def _request(self, endpoint: str, data: dict | None = None) -> dict:
        url = f"{self.BASE_URL}{endpoint}"
        response = self.session.post(url, json=data or {})
        response.raise_for_status()

        response_data = response.json()
        return self._clean_dict(response_data)  # Only cleans affected fields

    # === Phenotype Methods ===

    def get_all_phenotypes(self) -> pd.DataFrame:
        """Get all phenotypes and their statistics.

        Returns:
            DataFrame containing phenotype information.
        """
        response = self._request(PhenotypeEndpoint.ALL_PHENOTYPES.value)
        return pd.DataFrame(response.get("phenotypes", []))

    def get_phenotype_statistics(self, mesh_id: str) -> pd.DataFrame:
        """Get statistics on a phenotype.

        Args:
            mesh_id: The MeSH ID of the phenotype.

        Returns:
            DataFrame containing phenotype statistics.
        """
        data = {"mesh_id": mesh_id}
        response = self._request(PhenotypeEndpoint.STATS_BY_MESH_ID.value, data)
        return pd.DataFrame(response)

    def get_associated_species(self, mesh_id: str) -> pd.DataFrame:
        """Get species associated with a phenotype.

        Args:
            mesh_id: The MeSH ID of the phenotype.

        Returns:
            DataFrame containing associated species.
        """
        data = {"mesh_id": mesh_id}
        response = self._request(PhenotypeEndpoint.ASSOCIATED_SPECIES.value, data)
        return pd.DataFrame(response)

    def get_associated_genera(self, mesh_id: str) -> pd.DataFrame:
        """Get genera associated with a phenotype.

        Args:
            mesh_id: The MeSH ID of the phenotype.

        Returns:
            DataFrame containing associated genera.
        """
        data = {"mesh_id": mesh_id}
        response = self._request(PhenotypeEndpoint.ASSOCIATED_GENERA.value, data)
        return pd.DataFrame(response)

    def calculate_prevalence(
        self, species_data: pd.DataFrame, stats_data: pd.DataFrame
    ) -> pd.Series:
        """Calculate species/genera prevalence.

        Args:
            species_data: DataFrame containing species or genera data.
            stats_data: DataFrame containing phenotype statistics.

        Returns:
            Series containing prevalence percentages.
        """
        return species_data["samples"] / stats_data.stats["nr_valid_samples"] * 100

    def get_associated_projects(self, mesh_id: str) -> pd.DataFrame:
        """Get projects associated with a phenotype.

        Args:
            mesh_id: The MeSH ID of the phenotype.

        Returns:
            DataFrame containing associated projects.
        """
        data = {"mesh_id": mesh_id}
        response = self._request(PhenotypeEndpoint.ASSOCIATED_PROJECTS.value, data)
        return pd.DataFrame(response)

    def count_associated_runs(self, mesh_id: str) -> int:
        """Count the number of runs associated with a phenotype.

        Args:
            mesh_id: The MeSH ID of the phenotype.

        Returns:
            Count of associated runs.
        """
        data = {"mesh_id": mesh_id}
        response = self._request(PhenotypeEndpoint.COUNT_RUNS.value, data)
        return pd.DataFrame(response).iloc[0, 0]

    def get_associated_runs(
        self, mesh_id: str, skip: int = 0, limit: int = 100
    ) -> pd.DataFrame:
        """Get runs associated with a phenotype.

        Args:
            mesh_id: The MeSH ID of the phenotype.
            skip: Number of records to skip.
            limit: Number of records to retrieve.

        Returns:
            DataFrame containing associated runs.
        """
        data = {"mesh_id": mesh_id, "skip": skip, "limit": limit}
        response = self._request(PhenotypeEndpoint.ASSOCIATED_RUNS.value, data)
        return pd.DataFrame(response)

    def get_all_associated_runs(
        self, mesh_id: str, batch_size: int = 100
    ) -> pd.DataFrame:
        """Get all runs associated with a phenotype, handling pagination.

        Args:
            mesh_id: The MeSH ID of the phenotype.
            batch_size: Number of records to retrieve per request.

        Returns:
            DataFrame containing all associated runs.
        """
        total_runs = self.count_associated_runs(mesh_id)
        all_runs = []

        for skip in range(0, total_runs, batch_size):
            batch = skip + batch_size
            print(f"Fetching runs from {skip} to {batch}")
            batch = self.get_associated_runs(mesh_id, skip, batch)
            all_runs.append(batch)

        return pd.concat(all_runs) if all_runs else pd.DataFrame()

    def get_microbe_abundances_by_phenotype(
        self, mesh_id: str, ncbi_taxon_id: str
    ) -> dict:
        """Get relative abundances of a species/genus in samples of a phenotype.

        Args:
            mesh_id: The MeSH ID of the phenotype.
            ncbi_taxon_id: The NCBI taxonomy ID of the species/genus.

        Returns:
            dictionary containing abundance information.
        """
        data = {"mesh_id": mesh_id, "ncbi_taxon_id": ncbi_taxon_id}
        return self._request(PhenotypeEndpoint.MICROBE_ABUNDANCES.value, data)

    # === Taxon Methods ===

    def get_all_gut_microbes(self) -> dict[str, pd.DataFrame]:
        """Get an overview of all species and genera.

        Returns:
            dictionary containing DataFrames for species and genera.
        """
        response = self._request(TaxonEndpoint.ALL_GUT_MICROBES.value)

        result = {
            "all_species": pd.DataFrame(response.get("all_species", [])),
            "all_genus": pd.DataFrame(response.get("all_genus", [])),
            "metadata": response.get("metadata", {}),
        }

        return result

    def get_taxon_phenotype_summary(self, ncbi_taxon_id: int) -> pd.DataFrame:
        """Get summary of a taxon's prevalence and abundance across phenotypes.

        Args:
            ncbi_taxon_id: The NCBI taxonomy ID of the species/genus.

        Returns:
            DataFrame containing summary information.
        """
        data = {"ncbi_taxon_id": ncbi_taxon_id}
        response = self._request(TaxonEndpoint.PHENOTYPES_SUMMARY.value, data)
        return pd.DataFrame(response.get("phenotypes_associated_with_taxon", []))

    def get_taxon_phenotype_details(self, ncbi_taxon_id: int) -> dict:
        """Get detailed information about a taxon across phenotypes.

        Args:
            ncbi_taxon_id: The NCBI taxonomy ID of the species/genus.

        Returns:
            dictionary containing detailed information.
        """
        data = {"ncbi_taxon_id": ncbi_taxon_id}
        return self._request(TaxonEndpoint.ASSOCIATED_PHENOTYPES.value, data)

    def get_run_details(self, run_id: str, full_profile: bool = False) -> dict:
        """Get relative abundances for a run.

        Args:
            run_id: The ID of the run.
            full_profile: Whether to get the full taxonomic profile.

        Returns:
            dictionary containing run data.
        """
        data = {"run_id": run_id}
        endpoint = (
            TaxonEndpoint.FULL_TAXONOMIC_PROFILE.value
            if full_profile
            else TaxonEndpoint.RUN_DETAILS.value
        )

        return self._request(endpoint, data)

    # === Project Methods ===

    def get_curated_projects(self) -> pd.DataFrame:
        """Get all curated projects.

        Returns:
            DataFrame containing curated projects.
        """
        response = self._request(ProjectEndpoint.CURATED_PROJECTS.value)
        return pd.DataFrame(response)

    def get_project_microbe_abundances(
        self, project_id: str, mesh_id: str = ""
    ) -> dict:
        """Get relative abundances for a project.

        Args:
            project_id: The ID of the project.
            mesh_id: Optional MeSH ID to filter by phenotype.

        Returns:
            dictionary containing abundance data.
        """
        data = {"project_id": project_id, "mesh_id": mesh_id}
        return self._request(ProjectEndpoint.MICROBE_ABUNDANCES.value, data)


if __name__ == "__main__":
    gmrepo = GMRepo()
    # all_microbes = gmrepo.get_all_gut_microbes()
    # print(all_microbes.keys())
    # all_microbes["all_species"].to_csv("./all_species.csv", index=False)
    # all_microbes["all_genus"].to_csv("./all_genus.csv", index=False)
    # print(all_microbes["metadata"])
    # taxon_phenotype_summary = gmrepo.get_taxon_phenotype_summary(40520)
    # taxon_phenotype_summary.to_csv("associateed_phenotypes.csv")
