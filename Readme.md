# ERP Data analysis - data postprocessing

This code brings several data sources together to combine information
about an ERP experiment.

## Installation

It is highly recommended to first create either
a [virtual environment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)
or [conda and its variants](https://github.com/conda/conda).

The following commands create a virtual environment and run this code using
the command-line:

```
# Clone this repo
git clone <repo_url>
cd <dir>

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip3 install -r requirements.txt

# Run the code
python3 combine_files.py
```

See the `Usage` section for more details.

## Usage

This code depends on a series of files that are not included in the
repository due to data protection issues:

  * `Items_final_all_22_11_2022.xlsx`: Excel spreadsheet with the
    sentences used in the ERP experiment.
  * `proref_condition_coding_itemlist_fixed.txt`: A variant of a file
    originally called `proref_condition_coding_itemlist.txt` fixed to
    have its data (condition, lex number and animacy) in three neat
    columns.
  * `structure_pattern_lex_condition.txt`: File used to obtain condition
    information for every item in the Excel spreadsheet.
  * `proref_erp_data_structure_example.txt`: File containing the format
    of the final output where we are to add extra columns with
    information about every item presented in the experiment.
  * `Proref_Questionnaire_Data_2023-10-27.xlsx`: Excel spreadsheet
    containing information about the referential judgement of every
    item presented to every participant.

These files should be added to the `data` directory.

Once these files are in place, running the script `python3 combine_files.py`
generates an output file `results.csv` which combines all data sources
into a single CSV file.

## Workflow

The script combines data in the following way:
  
  1. We use the first spreadsheet `Items_final_all_22_11_2022.xlsx`
     to obtain information about every experimental item. From this file
     we extract lex number and condition, and calculate the surprisal
     value of the input text using GPT-2. The text is not used in its
     entirety as we remove everything after the last "und ...". Also
     note that we only look at the first 480 records.
  2. We read the file `proref_condition_coding_itemlist_fixed.txt` to
     extract data about animacy for every item. This file contains 480
     records that are paired 1-to-1 with the previous spreadsheet.
  3. We obtain group and ambiguity information about every item from the
     file `structure_pattern_lex_condition.txt`. This file also contains
     480 records paired 1-to-1 with those in the first spreadsheet.
  4. We obtain referential judgement information from the second
     spreadsheet `Proref_Questionnaire_Data_2023-10-27.xlsx`.
