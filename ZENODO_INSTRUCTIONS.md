# How to mint the Zenodo DOI (needs your accounts)

The editor requires the code in a DOI-assigning repository. The package in this
folder is ready to deposit. Minting the DOI needs your GitHub and Zenodo logins, so
it cannot be automated here. Two options:

## Option A — GitHub + Zenodo (recommended, gives a versioned DOI)

1. Create a new public GitHub repository, e.g. `global-urban-flood-risk`.
2. From this `code_deposit/` folder:
   ```
   git init
   git add .
   git commit -m "Code and summary data for Height-Aware and Protection-Informed Flood Assessment"
   git branch -M main
   git remote add origin https://github.com/<you>/global-urban-flood-risk.git
   git push -u origin main
   ```
3. Go to https://zenodo.org, log in, open **Account → GitHub**, and flip the switch
   **On** for the new repository.
4. On GitHub, create a **Release** (e.g. tag `v1.0`). Zenodo archives it automatically
   and assigns a DOI.
5. Copy the DOI badge/link from the Zenodo record.

## Option B — direct upload to Zenodo (fastest)

1. Zip this folder (a ready-made `code_deposit.zip` is in the project root).
2. Go to https://zenodo.org → **New upload**, drag in the zip, fill title/authors, set
   the license to MIT, and **Publish**. Zenodo assigns the DOI on publish.

## After you have the DOI

Tell me the DOI (e.g. `10.5281/zenodo.1234567`) and I will insert the Code Availability
section into the manuscript as the final tracked change:

> **Code availability.** The Google Earth Engine scripts and figure-generation code
> underlying this study are archived on Zenodo at https://doi.org/10.5281/zenodo.XXXXXXX.
> The analysis can also be explored interactively in the Earth Engine Code Editor at
> https://code.earthengine.google.com/?scriptPath=users%2FJiayong_Liang%2Fpublic%3Aglobal_flood_risk.
