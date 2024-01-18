import os
import re
import statistics
from collections import defaultdict
from dataclasses import dataclass
from gpt2_tools import LLM_Tool
from openpyxl import load_workbook


# Class representing all the information we want to collect
@dataclass
class Record:
    text : str
    full_id : str
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
	# All sources of data
	source_excel = os.path.join('data', 'Items_final_all_22_11_2022.xlsx')
	animacy_filename = os.path.join('data',
									'proref_condition_coding_itemlist_fixed.txt')
	structure_pattern_filename = os.path.join('data',
									          'structure_pattern_lex_condition.txt')
	proref_data_filename = os.path.join('data', 
	                                    'proref_erp_data_structure_example.txt')
	proref_questionnaire_filename = os.path.join('data', 'Proref_Questionnaire_Data_2023-10-27.xlsx')
	outfile = 'results.csv'

	# GPT-2 measures
	llmtool = LLM_Tool()

	# First, read data from the Items worksheet.
	workbook = load_workbook(filename=source_excel)
	worksheet = workbook['Items_all_corrct']

	# We hard-code the number of rows for now, but hopefully we can
	# detect that automatically in the future.
	for row in range(1, 481):
		item_read = worksheet.cell(row=row, column=3).value + ' ' + worksheet.cell(row=row, column=4).value
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
			# We are currently not using this one
			behavioral_response = code[-1:]
			
			# Finally, surprisal for the input text
			tokens = llmtool.get_tokenizer().encode(surprisal_text, return_tensors='pt')
			surprisal = llmtool.get_text_surprisal(tokens)

			worksheet_data.append(Record(text=surprisal_text,
			                             full_id=code,
			                             lex=lex,
			                             condition=cond_pos,
			                             animacy=None,
			                             surprisal=surprisal,
			                             group=None,
			                             ambiguity=None,
			                             ref_judgement=None
			                             ))
	assert len(worksheet_data) == 480, "Not enough data was read properly"

	# We now read the animacy data and put it together with the data
	# we collected from the spreadsheet
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
			assert fields[2] in {'i', 'a'}, \
					"Data field 'animacy' has an invalid value"
			worksheet_data[idx].animacy = 1 if fields[2] == 'a' else 0

	# Next is the data regarding ambiguity and subgroups
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

	# Next step: collect referential judgements for *some* fields
	proref_item_to_rating = defaultdict(list)
	workbook = load_workbook(filename=proref_questionnaire_filename)
	for list_num in range(1, 5):
		worksheet = workbook[f'list_{list_num}']
		row = 2
		done = False
		while not done:
			try:
				item_num = worksheet.cell(row=row, column=6).value
				rating1 = int(worksheet.cell(row=row, column=10).value)
				rating2 = int(worksheet.cell(row=row, column=11).value)
				proref_item_to_rating[(item_num, 1)].append(rating1)
				proref_item_to_rating[(item_num, 2)].append(rating2)
			except TypeError:
				# Done iterating this workbook
				done = True
			except ValueError:
				# Some records just say "N/A" instead of a rating
				pass
			row += 1
	for record in worksheet_data:
		try:
			mean_rating1 = statistics.mean(proref_item_to_rating[(int(record.full_id[:-1]), 1)])
			mean_rating2 = statistics.mean(proref_item_to_rating[(int(record.full_id[:-1]), 2)])
			record.ref_judgement = mean_rating1 + mean_rating2
		except statistics.StatisticsError:
			pass

	# Final check: all data has been filled for all fields
	keys_to_record = dict()
	for record in worksheet_data:
		assert record.text is not None and len(record.text) > 0, "Text is missing"
		assert record.full_id is not None and len(record.full_id) > 0, "Full_id is missing"
		assert record.lex is not None and len(record.lex) > 0, "Lex is missing"
		assert record.condition is not None and len(record.condition) > 0, "Condition is missing"
		assert record.animacy is not None and record.animacy < 2, "Animacy is missing"
		assert record.surprisal is not None and record.surprisal > 0, "Surprisal is missing"
		assert record.group is not None and len(record.group) > 0, "Group is missing"
		assert record.ambiguity is not None and len(record.ambiguity) > 0, "Ambiguity is missing"
		# The key is (subject, group, ambiguity)
		key = ('S' + record.lex, record.group, record.ambiguity)
		try:
			assert record.ref_judgement is not None and record.ref_judgement > 0, "Referential judgement is missing"
			keys_to_record[key] = (record.animacy, record.surprisal, record.ref_judgement)
		except AssertionError:
			keys_to_record[key] = (record.animacy, record.surprisal, 'N/A')
		
	# Unify all data
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
					print('\t'.join([line.strip(), str(record[0]), str(record[1]), str(record[2])]), file=out_fp)
