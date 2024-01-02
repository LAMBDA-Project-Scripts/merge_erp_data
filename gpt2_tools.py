import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel, set_seed


class LLM_Tool:
	def __init__(self, model='gpt2', seed=-1):
		self.model = GPT2LMHeadModel.from_pretrained(model)
		self.tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
		self.device =  "cuda:0" if torch.cuda.is_available() else "cpu"
		self.model.to(self.device)

		if seed >= 0:
			set_seed(seed)

	def get_tokenizer(self):
		return self.tokenizer

	def get_text_perplexity(self, tokens):
		""" Given a text, returns the perplexity for each of its
		individual tokens.

		Parameters
		----------
		tokens : torch.tensor
			Tensor containing the tokens for the given input sentence.

		Returns
		-------
		list(dict())
			A list of all tokens, their conversion to word, and their
			model generation probability.

		Notes
		-----
		Code inspired by https://huggingface.co/docs/transformers/perplexity
		"""
		max_length = self.model.config.n_positions
		# The lower, the better. But it's also slower.
		stride = 4
		#seq_len = sentence.input_ids.size(1)
		seq_len = tokens.size(1)
		nlls = []
		prev_end_loc = 0
		for begin_loc in range(0, seq_len, stride):
			end_loc = min(begin_loc + max_length, seq_len)
			trg_len = end_loc - prev_end_loc  # may be different from stride on last loop
			#input_ids = encodings.input_ids[:, begin_loc:end_loc].to(device)
			input_ids = tokens[:, begin_loc:end_loc].to(self.device)
			target_ids = input_ids.clone()
			target_ids[:, :-trg_len] = -100

			with torch.no_grad():
				outputs = self.model(input_ids, labels=target_ids)
				# loss is calculated using CrossEntropyLoss which averages over valid labels
				# N.B. the model only calculates loss over trg_len - 1 labels, because it internally shifts the labels
				# to the left by 1.
				neg_log_likelihood = outputs.loss
			nlls.append(neg_log_likelihood)
			prev_end_loc = end_loc
			if end_loc == seq_len:
				break
		return torch.exp(torch.stack(nlls).mean()).item()

	def get_text_surprisal(self, tokens):
		""" Given a text, returns the surprisal for each of its
		individual tokens.

		Parameters
		----------
		sentence : torch.tensor
			Tensor containing the tokens for the given input sentence.

		Returns
		-------
		list(dict())
			A list of all tokens, their conversion to word, and their
			model generation probability.

		Notes
		-----
		For more details see 'get_text_perplexity'.
		Formula: https://www.surgehq.ai/blog/how-good-is-your-chatbot-an-introduction-to-perplexity-in-nlp
		"""
		max_length = self.model.config.n_positions
		stride = 4
		seq_len = tokens.size(1)
		nlls = []
		prev_end_loc = 0
		for begin_loc in range(0, seq_len, stride):
			end_loc = min(begin_loc + max_length, seq_len)
			trg_len = end_loc - prev_end_loc 
			input_ids = tokens[:, begin_loc:end_loc].to(self.device)
			target_ids = input_ids.clone()
			target_ids[:, :-trg_len] = -100

			with torch.no_grad():
				outputs = self.model(input_ids, labels=target_ids)
				# loss is calculated using CrossEntropyLoss which averages over valid labels
				# N.B. the model only calculates loss over trg_len - 1 labels, because it internally shifts the labels
				# to the left by 1.
				neg_log_likelihood = outputs.loss
			nlls.append(neg_log_likelihood)
			prev_end_loc = end_loc
			if end_loc == seq_len:
				break
		return torch.exp(torch.stack(nlls).mean()).item()


if __name__ == '__main__':
	tool = LLM_Tool()
	text = "This is a text."
	tokens = tool.get_tokenizer().encode(text, return_tensors='pt')
	print(tool.get_text_surprisal(tokens))
	text = "This is a short text."
	tokens = tool.get_tokenizer().encode(text, return_tensors='pt')
	print(tool.get_text_surprisal(tokens))
	text = "This is a short banana."
	tokens = tool.get_tokenizer().encode(text, return_tensors='pt')
	print(tool.get_text_surprisal(tokens))
	text = "This long text is completely standard and has no redeeming features."
	tokens = tool.get_tokenizer().encode(text, return_tensors='pt')
	print(tool.get_text_surprisal(tokens))
	text = "This pen eats clouds."
	tokens = tool.get_tokenizer().encode(text, return_tensors='pt')
	print(tool.get_text_surprisal(tokens))
