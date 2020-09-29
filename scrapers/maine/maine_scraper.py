import pandas as pd

t_file = (
    "https://www.maine.gov/tools/whatsnew/index.php?topic=cec_clerks_registrars&v=text"
)

url_data = pd.read_table(t_file, sep="|")

county_info = pd.DataFrame(url_data)

init_info = county_info.columns.tolist()
new_init_info = []

for string in init_info:
    new_string = string.replace("<plaintext>Abbot", "Abbot")
    new_init_info.append(new_string)

phone = county_info["(207) 876-3198"].tolist()
county = county_info["<plaintext>Abbot"].tolist()
add1 = county_info["133 Main Road"].tolist()
add2 = county_info["Abbot, ME  04406"].tolist()

county.insert(0, "Abbot")
add1.insert(0, "133 Main Road")
add2.insert(0, "Abbot, ME 04406")
phone.insert(0, "(207) 876-3340")

address = [i + " " + j for i, j in zip(add1, add2)]
