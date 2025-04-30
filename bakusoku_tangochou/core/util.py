def ask_yes_no(question:str,yes_detail:str,no_detail:str):
	while (ans := input(f"{question}？([Y]es/[N]o): ")) not in {"Y","N","y","n","Yes","No"}:
		print(f"{yes_detail}場合は「Yes」か「Y」、「y」と、{no_detail}場合は「No」か「N」、「n」と入力し、エンターを押してください。")
	return ans in {"Y","y","Yes"}