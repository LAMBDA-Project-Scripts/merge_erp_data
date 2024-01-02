import os
import re
from dataclasses import dataclass
from gpt2_tools import LLM_Tool
from openpyxl import load_workbook


# Class representing all the information we want to collect
@dataclass
class Record:
    text : str
    lex : str
    condition : str
    animacy : str
    surprisal : float
    group : str
    ambiguity : str


if __name__ == '__main__':
	# Data that will be put together from multiple sources
	worksheet_data = []
	# GPT-2 measures
	llmtool = LLM_Tool()

	# First, read data from the worksheet.
	source_excel = os.path.join('src', 'Items_final_all_22_11_2022.xlsx')
	workbook = load_workbook(filename=source_excel)
	worksheet = workbook['Items_all_corrct']

	# We hard-code the number of rows for now, but hopefully we can
	# detect that automatically in the future.
	for row in range(1, 481):
		item_read = worksheet.cell(row=row, column=4).value
		code = str(worksheet.cell(row=row, column=2).value)
		if item_read is not None:
			# First, process the text in column D.
			# We start by removing everything after the last "und ..."
			elements = item_read.split(' und')
			surprisal_text = ' '.join(elements[:-1])
			# Next, remove special characters used to mark parts of the
			# sentence
			for character in ['§', '!', '*', '`', '&', '_']:
				surprisal_text = surprisal_text.replace(character, ' ')
			# Finally, collapse all multiple spaces into a single one
			surprisal_text = ' '.join(surprisal_text.split())

			# Now, the codes in column B
			lex = code[0:-5]
			second_code = code[-5]
			cond_pos = code[-4:-1]
			fourth_code = code[-1:]
			
			# Finally, surprisal for the input text
			tokens = llmtool.get_tokenizer().encode(surprisal_text, return_tensors='pt')
			surprisal = llmtool.get_text_surprisal(tokens)

			worksheet_data.append(Record(text=surprisal_text,
			                             lex=lex,
			                             condition=cond_pos,
			                             animacy=None,
			                             surprisal=surprisal,
			                             group=None,
			                             ambiguity=None
			                             ))
	assert len(worksheet_data) == 480, "Not enough data was read properly"

	# We now read the animacy data and put it together with the data
	# we collected from the spreadsheet
	animacy_filename = os.path.join('src',
									'information__factor_coding',
									'proref_condition_coding_itemlist_fixed.txt')
	with open(animacy_filename, 'r') as fp:
		# Skip the header
		next(fp)
		for idx, line in enumerate(fp):
			# Read the animacy data from the animacy text file,
			# performing first some data quality checks
			fields = re.split(' |\t', line.strip())
			assert fields[0] == worksheet_data[idx].lex, \
			       "Data field 'lex' is not properly paired"
			assert fields[1] == worksheet_data[idx].condition, \
			       "Data field 'condition' is not properly paired"
			# Update the value of the 'animacy' field
			worksheet_data[idx].animacy = fields[2]

	# Next is the data regarding ambiguity and subgroups
	structure_pattern_filename = os.path.join('src',
									          'information__factor_coding',
									          'structure_pattern_lex_condition.txt')
	with open(structure_pattern_filename, 'r') as fp:
		# Skip the header
		next(fp)
		for idx, line in enumerate(fp):
			fields = re.split(' |\t', line.strip())
			assert fields[1] == worksheet_data[idx].lex, \
			       "Data field 'lex' is not properly paired"
			group = '_'.join(fields[0:-2])
			ambig = fields[0].split('_')[-2]
			worksheet_data[idx].group = group
			# We convert 'amb/unamb' into 'ambig/unambig'
			worksheet_data[idx].ambiguity = ambig + 'ig'
