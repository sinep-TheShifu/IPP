import mylib.myfunctions as mf

def main():
    # Parsovanie argumentov
    args = mf.parse_arguments()

    # Zisk suborov pre interpretaciu
    source_file, input_file = mf.get_files(args)

    # Zisk XML struktury zo suboru source
    xml_structure = mf.get_xml_structure(source_file)

    # Skontroluje spravnost vstupneho kodu IPPcode21
    mf.control(xml_structure)

    # Vytvorenie pola instrukcii
    instructions_list = mf.get_instructions(xml_structure)

    # Skontroluje syntax instrukcii
    mf.check_instructions_syntax(instructions_list)

    # Interpretacia kodu
    mf.interpret_code(instructions_list, input_file)


if __name__== "__main__":
	main()