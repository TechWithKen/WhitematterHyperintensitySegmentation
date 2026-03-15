from bs4 import BeautifulSoup
import os
import pandas as pd

main_folder = "/Users/alert/Downloads/WMH_EXPERIMENT_UTRECHT/SPM_UTRECHT/FLAIR"

data = []

for subject_folder in os.listdir(main_folder):

    subject_path = os.path.join(main_folder, subject_folder)

    if os.path.isdir(subject_path):

        for file in os.listdir(subject_path):

            if file.endswith(".html"):

                file_path = os.path.join(subject_path, file)

                with open(file_path, "r", encoding="utf-8") as f:
                    soup = BeautifulSoup(f, "html.parser")

                lesion_volume = None
                lesion_number = None

                rows = soup.find_all("tr")

                for row in rows:
                    cols = row.find_all("td")

                    if len(cols) == 2:
                        label = cols[0].text.strip()
                        value = cols[1].text.strip()

                        if "Lesion volume" in label:
                            lesion_volume = value.replace(" ml","")

                        if "Number of lesions" in label:
                            lesion_number = value

                data.append({
                    "Subject": subject_folder,
                    "Lesion Volume (ml)": float(lesion_volume) if lesion_volume else None,
                    "Number of Lesions": int(lesion_number) if lesion_number else None
                })

df = pd.DataFrame(data)

print(df)