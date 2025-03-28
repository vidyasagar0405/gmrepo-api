import requests

bioproject = "PRJEB6070"
mesh_id = "D006262"

all_runs_in_project_url = f"https://gmrepo.humangut.info/Downloads/RunsByProjectID/all_runs_in_project_{bioproject}.tsv.gz"
all_runs_in_phenotype_url = f"https://gmrepo.humangut.info/Downloads/RunsByPhenotypeID/all_runs_associated_with_{mesh_id}.tsv.gz"
species_ass_with_phenotype = f"https://gmrepo.humangut.info/Downloads/SpeciesAndGeneraAssociatedWithPhenotypeID/species_associated_with_{mesh_id}.tsv.gz"
genus_ass_with_phenotype = f"https://gmrepo.humangut.info/Downloads/SpeciesAndGeneraAssociatedWithPhenotypeID/genus_associated_with_{mesh_id}.tsv.gz"


def download_file(url: str, file_name: str | None = None) -> None:
    """
    Download the file from `url` and save the file to `file_name`
    `file_name` is optional,
    if not provided the base of the url will be used as the file name
    """
    if file_name is None:
        file_name = url.split("/")[-1]  # Extracts the base name from the URL
    with requests.get(url, stream=True) as response:
        response.raise_for_status()  # Check for HTTP errors
        with open(file_name, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
    print(f"Downloaded file saved as {file_name}")


if __name__ == "__main__":
    download_file(all_runs_in_project_url)
    download_file(all_runs_in_phenotype_url)
    download_file(species_ass_with_phenotype)
    download_file(genus_ass_with_phenotype)
