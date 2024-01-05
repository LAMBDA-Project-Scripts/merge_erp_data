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
    ref_judgement : str


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
			behavioral_response = code[-1:]
			
			# Finally, surprisal for the input text
			tokens = llmtool.get_tokenizer().encode(surprisal_text, return_tensors='pt')
			surprisal = llmtool.get_text_surprisal(tokens)

			worksheet_data.append(Record(text=surprisal_text,
			                             lex=lex,
			                             condition=cond_pos,
			                             animacy=None,
			                             surprisal=surprisal,
			                             group=None,
			                             ambiguity=None,
			                             ref_judgement=behavioral_response  # <- Is this correct?
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
			cond_data = fields[0].split('_')
			group = '_'.join(cond_data[0:-2])
			ambig = cond_data[-2]
			worksheet_data[idx].group = group
			# We convert 'amb/unamb' into 'ambig/unambig'
			worksheet_data[idx].ambiguity = ambig + 'ig'

	# Final check: all data has been filled for all fields
	keys_to_record = dict()
	for record in worksheet_data:
		assert record.text is not None and len(record.text) > 0, "Text is missing"
		assert record.lex is not None and len(record.lex) > 0, "Lex is missing"
		assert record.condition is not None and len(record.condition) > 0, "Condition is missing"
		assert record.animacy is not None and len(record.animacy) > 0, "Animacy is missing"
		assert record.surprisal is not None and record.surprisal > 0, "Surprisal is missing"
		assert record.group is not None and len(record.group) > 0, "Group is missing"
		assert record.ambiguity is not None and len(record.ambiguity) > 0, "Ambiguity is missing"
		assert record.ref_judgement is not None and len(record.ref_judgement) > 0, "Ambiguity is missing"
		# The key is (subject, group, ambiguity)
		key = ('S' + record.lex, record.group, record.ambiguity)
		keys_to_record[key] = (record.animacy, record.surprisal, record.ref_judgement)
	# Unify all data
	proref_data_filename = os.path.join('src', 
	                                    'information__factor_coding',
	                                    'proref_erp_data_structure_example.txt')
	outfile = 'output.txt'
	first = True
	with open(proref_data_filename, 'r') as in_fp:
		with open(outfile, 'w') as out_fp:
			for line in in_fp:
				if first:
					print(line, file=out_fp)
					first = False
				else:
					fields = line.split('\t')
					# The key is (subject, group, ambiguity)
					key = (fields[4], fields[5], fields[6])
					record = keys_to_record[key]
					print('\t'.join([line.strip(), record[0], str(record[1]), record[2]]), file=out_fp)
