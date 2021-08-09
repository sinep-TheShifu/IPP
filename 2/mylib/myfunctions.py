import sys
import argparse
import fileinput
import xml.etree.ElementTree as ET
import re

# Trieda chybovych stavov
class Errors:
    script_params = 10
    input_file = 11
    output_file = 12
    internal = 99
    xml_format = 31
    xml_struct = 32

    semantics = 52 
    operand_types = 53
    var_nondefined = 54
    frame_nondefined = 55
    val_missing = 56
    operand_wrong_val = 57
    string = 58

# Trieda pre instrukciu
class Instruction:
    # Inicializacia 
    def __init__(self, order, opcode, arguments = None):
        self.order = order
        self.opcode = opcode
        self.arguments = arguments

# Trieda pre argument v instrukcii
class Argument:
    # Inicializacia 
    def __init__(self, atype, value, order):
        self.atype = atype
        self.value = value
        self.order = order

# Funkcia pre ukoncenie programu v pripade chyby
def errorOccured(exit_number, message = "Error"):
    print(message)
    sys.exit(exit_number)

# Parsovanie argumentov
def parse_arguments():
    parser = argparse.ArgumentParser(description='Interpret of code in IPP2021 language. At least one of the arguments --source or --input are mandatory! If one of them is not given, it will be loaded from standard input.')

    parser.add_argument('--source', help='File with the XML representation of the source code')
    parser.add_argument('--input', help='File with the inputs for the interpretation')

    args = parser.parse_args()

    if not args.source and not args.input:
        parser.error('At least one of the arguments --source or --input is mandatory!')
    
    return args

# Zisk suborov pre interpretaciu
def get_files(args):
    source_file = args.source
    input_file = args.input
    source_lines = ""
    input_lines = ""

    # Source sa nacita zo STDIN
    if source_file == None:
        with fileinput.input(files="-") as f:
            for line in f:
                source_lines = source_lines + line.strip() + "\n"
            
            source_file = source_lines
    # Source sa nacita zo suboru
    else:
        try:
            f = open(source_file, 'r')
        except OSError:
            errorOccured(Errors.input_file, 'Could not open file: ' + source_file) 

        with f:
            source_file = f.read()       
        f.close()
    
    # Input sa nacita zo STDIN
    if input_file == None:
        with fileinput.input(files="-") as f:
            for line in f:
                input_lines = input_lines + line.strip() + "\n"
            
            input_file = input_lines    
    # Input sa nacita zo suboru
    else:
        try:
            f = open(input_file, 'r')
        except OSError:
            errorOccured(Errors.input_file, 'Could not open a file: ' + input_file) 

        with f:
            input_file = f.read()
        f.close()

    return source_file, input_file

# Ziska XML strukturu
def get_xml_structure(file):
    try:
        root = ET.fromstring(file)
    except:
        errorOccured(Errors.xml_format, 'XML is not well-formed.')
    
    return root

# Kontrola vstupneho kodu IPPcode21 v XML formate 
def control(xml):

    # Skontroluje spravnost hlavicky 
    control_header(xml)

    # Skontroluje spravnost instrukcii
    control_instruction(xml)

# Kontrola hlavicky
def control_header(xml):
    if xml.tag != "program":
        errorOccured(Errors.xml_struct, 'Wrong XML structure. Missing main program element.')

    language_def = False
    for attr in xml.attrib:
        if attr == "language":
            language_def = True
        if attr != "language" and attr != "name" and attr != "description":
            errorOccured(Errors.xml_struct, "Unknown attribute in element program.")

    if language_def == False:
        errorOccured(Errors.xml_struct, "Missing language identifier.")

# Kontrola instrukcii
def control_instruction(xml):
    # Pomocne premenne
    order = 0  

    # Prechadzaju sa instrukcie
    for instruction in xml:
        # Pomocne premenne 
        order_def = False
        opcode_def = False

        # Kontrola nazvu elementu pre instrukciu
        if instruction.tag != "instruction":
            errorOccured(Errors.xml_struct, "Wrong element on place of instruction.")

        # Prechadzaju sa atributy 
        for attr in instruction.attrib:
            # Kontrola atributu order
            if attr == "order":
                # Duplicitne zadanie argumentu order
                if order_def == True:
                    errorOccured(Errors.xml_struct, "Order of instruction was already defined.")

                try:
                    attr = int(instruction.attrib[attr])    # Pretypovanie na integer
                except:
                    errorOccured(Errors.xml_struct, "Order has wrong type")

                if attr <= order:                       # Pokial je order <= predchodzemu, zaroven pre prvu kontrolu > 0
                    errorOccured(Errors.xml_struct, "Wrong instruction order: " + str(attr)) 
                order = attr
                order_def = True
            elif attr == "opcode":
                if opcode_def == True:
                    errorOccured(Errors.xml_struct, "Opcode of instruction was already defined.")
                opcode_def = True
            else:                
                errorOccured(Errors.xml_struct, "Unknown attribute: " + attr)

        # Kontrola argumentov instrukcie
        counter = 1
        for arg in instruction:
            if counter == 1:
                if arg.tag != "arg1":
                    errorOccured(Errors.xml_struct, "Wrong instruction argument.")
            elif counter == 2:
                if arg.tag != "arg2":
                    errorOccured(Errors.xml_struct, "Wrong instruction argument.")
            elif counter == 3:
                if arg.tag != "arg3":
                    errorOccured(Errors.xml_struct, "Wrong instruction argument.")
            else:
                errorOccured(Errors.xml_struct, "Too many instruction arguments.")
            counter = counter + 1
            # Kontrola typu 
            control_argument_type(arg)
            
        # Kontrola definicie atributov
        if order_def == False:
            errorOccured(Errors.xml_struct, "Attribute order not defined in istruction with order: " + str(order))
        if opcode_def == False:
            errorOccured(Errors.xml_struct, "Attribute opcode not defined in istruction with order: " + str(order))

# Skontroluje spravnost typu argumentu
def control_argument_type(arg):
    type_def = False
    arg_type = ""

    for attr in arg.attrib:
        if attr != "type" or type_def == True:
            errorOccured(Errors.xml_struct, "Argument type error.")
        elif attr == "type":
            type_def = True
            arg_type = arg.attrib[attr]
        else:
            errorOccured(Errors.xml_struct, "Unknown argument type: " + attr)

    # Kontrola spravnosti typov pomocou regexu
    if arg_type == "int":
        if re.match(r'^[-\+]?[0-9]+$', arg.text) == None:
            errorOccured(Errors.xml_struct, "Argument of type int has wrong value.")    
    elif arg_type == "bool":
        if re.match(r'^(bool@false|bool@true)$', arg.text) == None:
            errorOccured(Errors.xml_struct, "Argument of type bool has wrong value.")
    elif arg_type == "string":
        if re.match(r'^([^\s\#\\]|\\[0-9]{3})*$', arg.text) == None:
            errorOccured(Errors.xml_struct, "Argument of type string has wrong value.")
    elif arg_type == "var":
        if re.match(r'^(GF|LF|TF)@([a-z]|[A-Z]|[\_\-\$\&\%\*\?\!])(\w|[\_\-\$\&\%\*\?\!])*$', arg.text) == None:
            errorOccured(Errors.xml_struct, "Argument of type var has wrong value.")
    elif arg_type == "label":
        if re.match(r'^([a-z]|[A-Z]|[\_\-\$\&\%\*\?\!])(\w|[\_\-\$\&\%\*\?\!])*$', arg.text) == None:
            errorOccured(Errors.xml_struct, "Argument of type label has wrong value.")
    elif arg_type == "nil":
        if re.match(r'^nil$', arg.text) == None:
            errorOccured(Errors.xml_struct, "Argument of type nil has wrong value.")
    elif arg_type == "type":
        if re.match(r'^(int|string|bool)$', arg.text) == None:
            errorOccured(Errors.xml_struct, "Argument of type type has wrong value.")
    else:
        errorOccured(Errors.xml_struct, "Unknown argument type: " + arg_type)

# Vrati pole instrukcii z XML struktury
def get_instructions(xml):
    instructionsList = []    
    

    # Prechadzanie vsetkymi instrukciami 
    for instruction in xml:

        # Prechadzanie atributmi instrukcie -> zisk order a opcode
        for attr in instruction.attrib:
            if attr == "order":
                order = int(instruction.attrib[attr])
            else:
                opcode = instruction.attrib[attr]
                opcode.upper()

        arguments = []
        value = None
        atype = None
        aorder = 1
        # Prechadzanie argumentmi instrukcie
        for arg in instruction:
            value = arg.text    # Hodnota argumentu

            # Prechadzanie atributov argumentu
            for attr in arg.attrib:
                atype = arg.attrib[attr]    # Typ argumentu  

            # Nahradenie escape sekvencii
            if atype == "string":
                escapedList = re.findall(r'(\\[0-9]{3})+', value)
                for escapedUnicode in escapedList:
                    unicodeAsChar = chr(int(escapedUnicode[1:]))
                    value = value.replace(escapedUnicode, unicodeAsChar)

            argument = Argument(atype, value, aorder)
            arguments.append(argument)

            aorder += 1

        # Vytvorenie instrukcie a pridanie do pola
        instr = Instruction(order, opcode, arguments)
        instructionsList.append(instr)

    return instructionsList

# Skontroluje syntax instrukcii pre IPPcode21
def check_instructions_syntax(instructionsList):
    for instruction in instructionsList:

        arg1 = None
        arg2 = None
        arg3 = None

        opcode = str(instruction.opcode).upper()
        
        for arg in instruction.arguments:
            if arg.order == 1:
                arg1 = arg.atype
            elif arg.order == 2:
                arg2 = arg.atype
            elif arg.order == 3:
                arg3 = arg.atype

        if opcode == "MOVE":
            if arg1 != "var" or arg2 not in ("int", "bool", "string", "var", "nil") or arg3 != None:
                errorOccured(Errors.xml_struct, "MOVE wrong arguments")

        elif opcode == "CREATEFRAME":
            if arg1 != None or arg2 != None or arg3 != None:
                errorOccured(Errors.xml_struct, "CREATEFRAME wrong arguments")

        elif opcode == "PUSHFRAME":
            if arg1 != None or arg2 != None or arg3 != None:
                errorOccured(Errors.xml_struct, "PUSHFRAME wrong arguments")

        elif opcode == "POPFRAME":
            if arg1 != None or arg2 != None or arg3 != None:
                errorOccured(Errors.xml_struct, "POPFRAME wrong arguments")

        elif opcode == "DEFVAR":
            if arg1 != "var" or arg2 != None or arg3 != None:
                errorOccured(Errors.xml_struct, "DEFVAR wrong arguments")

        elif opcode == "CALL":
            if arg1 != "label" or arg2 != None or arg3 != None:
                errorOccured(Errors.xml_struct, "CALL wrong arguments")

        elif opcode == "RETURN":
            if arg1 != None or arg2 != None or arg3 != None:
                errorOccured(Errors.xml_struct, "RETURN wrong arguments")

        elif opcode == "PUSHS":
            if arg1 not in ("int", "bool", "string", "var", "nil") or arg2 != None or arg3 != None:
                errorOccured(Errors.xml_struct, "PUSHS wrong arguments")

        elif opcode == "POPS":
            if arg1 != "var" or arg2 != None or arg3 != None:
                errorOccured(Errors.xml_struct, "POPS wrong arguments")

        elif opcode == "ADD":
            if arg1 != "var" or arg2 not in ("int", "bool", "string", "var", "nil") or arg3 not in ("int", "bool", "string", "var", "nil"):
                errorOccured(Errors.xml_struct, "ADD wrong arguments")

        elif opcode == "SUB":
            if arg1 != "var" or arg2 not in ("int", "bool", "string", "var", "nil") or arg3 not in ("int", "bool", "string", "var", "nil"):
                errorOccured(Errors.xml_struct, "SUB wrong arguments")
        
        elif opcode == "MUL":
            if arg1 != "var" or arg2 not in ("int", "bool", "string", "var", "nil") or arg3 not in ("int", "bool", "string", "var", "nil"):
                errorOccured(Errors.xml_struct, "MUL wrong arguments")

        elif opcode == "IDIV":
            if arg1 != "var" or arg2 not in ("int", "bool", "string", "var", "nil") or arg3 not in ("int", "bool", "string", "var", "nil"):
                errorOccured(Errors.xml_struct, "IDIV wrong arguments")

        elif opcode == "LT":
            if arg1 != "var" or arg2 not in ("int", "bool", "string", "var", "nil") or arg3 not in ("int", "bool", "string", "var", "nil"):
                errorOccured(Errors.xml_struct, "LT wrong arguments")

        elif opcode == "GT":
            if arg1 != "var" or arg2 not in ("int", "bool", "string", "var", "nil") or arg3 not in ("int", "bool", "string", "var", "nil"):
                errorOccured(Errors.xml_struct, "GT wrong arguments")

        elif opcode == "EQ":
            if arg1 != "var" or arg2 not in ("int", "bool", "string", "var", "nil") or arg3 not in ("int", "bool", "string", "var", "nil"):
                errorOccured(Errors.xml_struct, "EQ wrong arguments")

        elif opcode == "AND":
            if arg1 != "var" or arg2 not in ("int", "bool", "string", "var", "nil") or arg3 not in ("int", "bool", "string", "var", "nil"):
                errorOccured(Errors.xml_struct, "AND wrong arguments")

        elif opcode == "OR":
            if arg1 != "var" or arg2 not in ("int", "bool", "string", "var", "nil") or arg3 not in ("int", "bool", "string", "var", "nil"):
                errorOccured(Errors.xml_struct, "OR wrong arguments")

        elif opcode == "NOT":
            if arg1 != "var" or arg2 not in ("int", "bool", "string", "var", "nil") or arg3 != None:
                errorOccured(Errors.xml_struct, "NOT wrong arguments")

        elif opcode == "INT2CHAR":
            if arg1 != "var" or arg2 not in ("int", "bool", "string", "var", "nil") or arg3 != None:
                errorOccured(Errors.xml_struct, "INT2CHAR wrong arguments")

        elif opcode == "STRI2INT":
            if arg1 != "var" or arg2 not in ("int", "bool", "string", "var", "nil") or arg3 != None:
                errorOccured(Errors.xml_struct, "STRI2INT wrong arguments")

        elif opcode == "READ":
            if arg1 != "var" or arg2 != "type" or arg3 != None:
                errorOccured(Errors.xml_struct, "READ wrong arguments")

        elif opcode == "WRITE":
            if arg1 not in ("int", "bool", "string", "var", "nil") or arg2 != None or arg3 != None:
                print(arg1)
                print(arg2)
                print(arg3)
                errorOccured(Errors.xml_struct, "WRITE wrong arguments")
        
        elif opcode == "CONCAT":
            if arg1 != "var" or arg2 not in ("int", "bool", "string", "var", "nil") or arg3 not in ("int", "bool", "string", "var", "nil"):
                errorOccured(Errors.xml_struct, "CONCAT wrong arguments")

        elif opcode == "STRLEN":
            if arg1 != "var" or arg2 not in ("int", "bool", "string", "var", "nil") or arg3 != None:
                errorOccured(Errors.xml_struct, "STRLEN wrong arguments")

        elif opcode == "GETCHAR":
            if arg1 != "var" or arg2 not in ("int", "bool", "string", "var", "nil") or arg3 not in ("int", "bool", "string", "var", "nil"):
                errorOccured(Errors.xml_struct, "GETCHAR wrong arguments")

        elif opcode == "SETCHAR":
            if arg1 != "var" or arg2 not in ("int", "bool", "string", "var", "nil") or arg3 not in ("int", "bool", "string", "var", "nil"):
                errorOccured(Errors.xml_struct, "SETCHAR wrong arguments")

        elif opcode == "TYPE":
            if arg1 != "var" or arg2 not in ("int", "bool", "string", "var", "nil") or arg3 != None:
                errorOccured(Errors.xml_struct, "TYPE wrong arguments")
        
        elif opcode == "LABEL":
            if arg1 != "label" or arg2 != None or arg3 != None:
                errorOccured(Errors.xml_struct, "LABEL wrong arguments")

        elif opcode == "JUMP":
            if arg1 != "label" or arg2 != None or arg3 != None:
                errorOccured(Errors.xml_struct, "JUMP wrong arguments")

        elif opcode == "JUMPIFEQ":
            if arg1 != "label" or arg2 not in ("int", "bool", "string", "var", "nil") or arg3 not in ("int", "bool", "string", "var", "nil"):
                errorOccured(Errors.xml_struct, "JUMPIFEQ wrong arguments")

        elif opcode == "JUMPIFNEQ":
            if arg1 != "label" or arg2 not in ("int", "bool", "string", "var", "nil") or arg3 not in ("int", "bool", "string", "var", "nil"):
                errorOccured(Errors.xml_struct, "JUMPIFNEQ wrong arguments")

        elif opcode == "EXIT":
            if arg1 not in ("int", "bool", "string", "var", "nil") or arg2 != None or arg3 != None:
                errorOccured(Errors.xml_struct, "EXIT wrong arguments")

        elif opcode == "DPRINT":
            if arg1 not in ("int", "bool", "string", "var", "nil") or arg2 != None or arg3 != None:
                errorOccured(Errors.xml_struct, "DPRINT wrong arguments")

        elif opcode == "BREAK":
            if arg1 != None or arg2 != None or arg3 != None:
                errorOccured(Errors.xml_struct, "BREAK wrong arguments")

        else:
            errorOccured(Errors.xml_struct, "Unknown instruction opcode")

# Ziska hodnotu premennej z ramca
def get_var_val(arg, GF, LF, TF):
    frame = arg.value.split("@", 1)[0]
    var = arg.value.split("@", 1)[1]

    if frame == "GF":	
        if var not in GF:
            errorOccured(Errors.var_nondefined, "Var: " + var + " not defined")
        val = GF[var]
    if frame == "LF":
        if len(LF) <= 0:
            errorOccured(Errors.frame_nondefined, "Local frame not defined")
        if var not in LF[-1]:
            errorOccured(Errors.var_nondefined, "Var: " + var + " not defined")
        val = LF[-1][var]
    if frame == "TF":
        if TF == None:
            errorOccured(Errors.frame_undefined, "Temporary frame is undefined")
        if var not in TF:
            errorOccured(Errors.var_nondefined, "Var: " + var + " not defined")
        val = TF[var]
    return val

# Ziska hodnotu z argumentu ktory nieje var
def get_val(arg):

    if arg.atype == "int":
        return int(arg.value)
    elif arg.atype == "bool":
        if arg.value == "true":
            return True
        else:
            return False
    else:
        return arg.value

# Vratim dict labelov a ich umiestneni s polom vsetkych labelov
def	get_labels_index(instructionsList):

    labelsList = []
    labelsDict = {}
    
    for i, instruction in enumerate(instructionsList):
        if instruction.opcode == "LABEL":
            label = instruction.arguments[0].value 
            if label in labelsList:
                errorOccured(Errors.semantics, "LABEL redefinition of label")
            
            labelsList.append(label)
            labelsDict[label] = i
    
    return labelsList, labelsDict

# Interpretacia IPPcode21 
def interpret_code(instructions, input_file):
    
    GF = {} 
    LF = []
    TF = None   

    arg1 = None
    arg2data = None
    arg3data = None

    frame = None
    var = None
    destination = None
    dataToWrite = None

    label = None
    labelsList, labelsIndex = get_labels_index(instructions)    # Ziskam labely

    stackForSymb = []

    stackForCallReturn = []

    current_instruction = 0
    processed_instruction = 0

    # Prechadzanie vsetkymi instrukciami
    while current_instruction < len(instructions):

        instruction = instructions[current_instruction]
        # Inkrementacia statistik
        current_instruction += 1
        processed_instruction += 1

        # OPCODE <var> <symb1> <symb2>
        if instruction.opcode in ("ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "NOT", "INT2CHAR", "STRI2INT", "CONCAT", "STRLEN", "MOVE", "GETCHAR", "SETCHAR", "TYPE"):
            # Argumenty instrukcie
            for arg in instruction.arguments:
                # 1. argument <var>
                if arg.order == 1:
                    destination = get_var_val(arg, GF, LF, TF)
                
                # 2. argument <symb>
                if arg.order == 2:
                    # je var
                    if arg.atype == "var":
                        arg2data = get_var_val(arg, GF, LF, TF)
                    # nieje var
                    else:
                        arg2data = get_val(arg)
                # 3. argument <symb>
                if arg.order == 3:
                    # je var
                    if arg.atype == "var":
                        arg3data = get_var_val(arg, GF, LF, TF)
                    # nieje var
                    else:
                        arg3data = get_val(arg)

        elif instruction.opcode in ("EXIT", "DPRINT"):
            if instruction.arguments[0].atype == "var":
                arg2data = get_var_val(instruction.arguments[0], GF, LF, TF)
            else:
                arg2data = get_val(instruction.arguments[0])
        
        elif instruction.opcode in ("LABEL", "JUMP", "JUMPIFEQ", "JUMPIFNEQ", "CALL"):
            for arg in instruction.arguments:
                if arg.order == 1:
                    label = arg.value
                if arg.order == 2:
                    if arg.atype == "var":
                        arg2data = get_var_val(arg, GF, LF, TF)
                    else:
                        arg2data = get_val(arg)
                if arg.order == 3:
                    if arg.atype == "var":
                        arg3data = get_var_val(arg, GF, LF, TF)
                    else:
                        arg3data = get_val(arg)
        
        elif instruction.opcode in ("READ"):
            for arg in instruction.arguments:
                if arg.order == 1:
                    arg1data = get_var_val(arg, GF, LF, TF)
                if arg.order == 2:
                    arg2data = arg.value

        elif instruction.opcode in ("SETCHAR"):
            for arg in instruction.arguments:
                if arg.order == 1:
                    if arg.atype != "var":
                        errorOccured(Errors.operand_types, "SETCHAR first argument not var")
                    arg1data = get_var_val(arg, GF, LF, TF)
                if arg.order == 2:
                    if arg.atype == "var":
                        arg2data = get_var_val(arg, GF, LF, TF)
                    else:
                        arg2data = get_val(arg)
                    if type(arg2data) != int:
                        errorOccured(Errors.operand_types, "SETCHAR second argument not int")

                if arg.order == 3:
                    if arg.atype == "var":
                        arg3data = get_var_val(arg, GF, LF, TF)
                    else:
                        arg3data = get_val(arg) 
                    if type(arg3data) != int:
                        errorOccured(Errors.operand_types, "SETCHAR third argument not int")       

        # Praca s ramcami, volanie funkcii
        if instruction.opcode == "MOVE":               
            dataToWrite = arg2data
            
        elif instruction.opcode == "CREATEFRAME":
            TF = {}

        elif instruction.opcode == "PUSHFRAME":
            if TF == None:
                errorOccured(Errors.frame_nondefined, "Temporary frame is undefined.")
            LF.append(TF)
            TF = None

        elif instruction.opcode == "POPFRAME":
            if len(LF) == 0:
                errorOccured(Errors.frame_nondefined, "There are no frames in LF stack.")
            TF = LF.pop()

        elif instruction.opcode == "DEFVAR":
            frame = instruction.arguments[0].value.split("@", 1)[0]
            var = instruction.arguments[0].value.split("@", 1)[1]

            if frame == "GF":
                if var in GF:
                    errorOccured(Errors.semantics, "Variable already defined in global scope")
                GF[var] = None
            if frame == "LF":
                if len(LF) <= 0:
                    errorOccured(Errors.frame_nondefined, "Local frame not defined")
                if var in LF[-1]:
                    errorOccured(Errors.semantics, "Variable already defined in local scope")
                LF[-1][var] = None                
            if frame == "TF":
                if TF == None:
                    errorOccured(Errors.frame_nondefined, "Temporary frame not defined")
                if var in TF:
                    errorOccured(Errors.semantics, "Variable already defined in temporary scope")
                TF[var] = None
            
            
        elif instruction.opcode == "CALL":
            if label not in labelsList:
                errorOccured(Errors.semantics, "JUMP label not defined")
            stackForCallReturn.append(current_instruction)
            current_instruction = labelsIndex[label]

        elif instruction.opcode == "RETURN":
            if len(stackForCallReturn) == 0:
                errorOccured(Errors.val_missing, "RETURN stack is empty")
            current_instruction = stackForCallReturn.pop()

        # Praca s datovym zasobnikom
        elif instruction.opcode == "PUSHS":
            symb = instruction.arguments[0]

            if symb.atype == "var":
                stackForSymb.append(get_var_val(symb, GF, LF, TF))
            else:
                stackForSymb.append(get_val(symb))

        elif instruction.opcode == "POPS":            
            if len(stackForSymb) == 0:
                errorOccured(Errors.val_missing, "POPS stack is empty")

            tmp = instruction.arguments[0]
            frame = tmp.value.split("@", 1)[0]
            var = tmp.value.split("@", 1)[1]

            if frame == "GF":
                if var not in GF:
                    errorOccured(Errors.var_nondefined, "POPS var undefined in Global frame")
                GF[var] = stackForSymb.pop()
            elif frame == "LF":
                if len(LF) <= 0:
                        errorOccured(Errors.frame_nondefined, "POPS Local frame not defined")
                LF[-1][var] = stackForSymb.pop()
            elif frame == "TF":
                if TF == None:
                        errorOccured(Errors.frame_nondefined, "POPS Temporary frame not defined")
                TF[var] = stackForSymb.pop()

        # Aritmeticke, relacne, boolovske a konverzne instrukcie
        elif instruction.opcode == "ADD":
            if type(arg2data) != int or type(arg3data) != int:
                errorOccured(Errors.operand_types, "Operands are not of type int")
            dataToWrite = arg2data + arg3data

        elif instruction.opcode == "SUB":
            if type(arg2data) != int or type(arg3data) != int:
                errorOccured(Errors.operand_types, "Operands are not of type int")
            dataToWrite = arg2data - arg3data

        elif instruction.opcode == "MUL":
            if type(arg2data) != int or type(arg3data) != int:
                errorOccured(Errors.operand_types, "Operands are not of type int")
            dataToWrite = arg2data * arg3data

        elif instruction.opcode == "IDIV":
            if type(arg2data) != int or type(arg3data) != int:
                errorOccured(Errors.operand_types, "Operands are not of type int")
            if arg3data == 0:
                errorOccured(Errors.operand_wrong_val, "Dividing by zero")
            dataToWrite = int(arg2data / arg3data)

        elif instruction.opcode == "LT":
            if type(arg2data) != type(arg3data) or arg2data == "nil" or arg3data == "nil":
                errorOccured(Errors.operand_types, "Arguments: " + arg2data + ", " + arg3data + "have different data types")
            dataToWrite = arg2data < arg3data

        elif instruction.opcode == "GT":
            if type(arg2data) != type(arg3data) or arg2data == "nil" or arg3data == "nil":
                errorOccured(Errors.operand_types, "Arguments: " + arg2data + ", " + arg3data + "have different data types")
            dataToWrite = arg2data > arg3data

        elif instruction.opcode == "EQ":
            if type(arg2data) != type(arg3data):
                errorOccured(Errors.operand_types, "Arguments: " + arg2data + ", " + arg3data + "have different data types")
            dataToWrite = arg2data == arg3data

        elif instruction.opcode == "AND":
            if type(arg2data) != bool or type(arg3data) != bool:
                errorOccured(Errors.operand_types, "Arguments are not of type bool")
            dataToWrite = arg2data and arg3data

        elif instruction.opcode == "OR":
            if type(arg2data) != bool or type(arg3data) != bool:
                errorOccured(Errors.operand_types, "Arguments are not of type bool")
            dataToWrite = arg2data or arg3data

        elif instruction.opcode == "NOT":
            if type(arg2data) != bool:
                errorOccured(Errors.operand_types, "Arguments are not of type bool")
            dataToWrite = not arg2data

        elif instruction.opcode == "INT2CHAR":
            if type(arg2data) != int:
                errorOccured(Errors.operand_types, "Argument is not int")
            try:
                dataToWrite = str(chr(arg2data))
            except:
                errorOccured(Errors.string, "INT2CHAR error, cant make unicode from int")

        elif instruction.opcode == "STRI2INT":
            if type(arg2data) != str or type(arg3data) != int:
                errorOccured(Errors.operand_types, "STR2INT wrong operand types")
            try:
                dataToWrite = ord(arg2data[arg3data])
            except:
                errorOccured(Errors.string, "STR2INT could not be done")

        # Vstupno vystupne instrukcie
        elif instruction.opcode == "READ": 
            count = 0   
            tmp = ""        
            for char in input_file:
                count += 1
                if char == "\n":
                    break
                else:
                    tmp = tmp + char

            input_file = input_file[count:]

            if arg2data == "int":
                try:
                    dataToWrite = int(tmp)
                except:
                    dataToWrite = "nil"

            elif arg2data == "bool":
                tmp = str(tmp).lower()
                if tmp == "true":
                    dataToWrite = "true"
                else:
                    dataToWrite = "false"

            elif arg2data == "string":
                dataToWrite = tmp

        elif instruction.opcode == "WRITE":
            if instruction.arguments[0].atype == "var":
                frame = instruction.arguments[0].value.split("@", 1)[0]
                var = instruction.arguments[0].value.split("@", 1)[1]

                if frame == "GF":
                    if var not in GF:
                        errorOccured(Errors.var_undefined, "WRITE var undefined in global frame")
                    print(GF[var], end="")
                if frame == "LF":
                    if len(LF) <= 0:
                        errorOccured(Errors.frame_nondefined, "WRITE Local frame not defined")
                    print(LF[-1][var], end="")                
                if frame == "TF":
                    if TF == None:
                        errorOccured(Errors.frame_nondefined, "WRITE Temporary frame not defined")
                    print(TF[var], end="")
            else:
                print(instruction.arguments[0].value, end="")
            
        # Praca s retazcami
        elif instruction.opcode == "CONCAT":
            if type(arg2data) != str or type(arg3data) != str:
                errorOccured(Errors.operand_types, "CONCAT wrong operant types")
            dataToWrite = arg2data + arg3data

        elif instruction.opcode == "STRLEN":
            if type(arg2data) != str:
                errorOccured(Errors.operand_types, "STRLEN wrong operand")
            dataToWrite = len(arg2data)

        elif instruction.opcode == "GETCHAR":
            if type(arg2data) != str or type(arg3data) != int:
                errorOccured(Errors.operand_types, "GETCHAR wrong operand types")
            try:
                dataToWrite = arg2data[arg3data]
            except:
                errorOccured(Errors.string, "GETCHAR error")

        elif instruction.opcode == "SETCHAR":
            if arg3data == "":
                errorOccured(Errors.string, "SETCHAR third argument is empty")
            
            try:
                arg1data[arg2data] = arg3data[0]
                dataToWrite = "".join(arg1data)
            except:
                errorOccured(Errors.string, "SETCHAR error")

        # Praca s typmi
        elif instruction.opcode == "TYPE":
            if arg2data == None:
                dataToWrite = ""
            elif type(arg2data) == int:
                dataToWrite = "int"
            elif type(arg2data) == bool:
                dataToWrite = "bool"
            elif type(arg2data) == str:
                dataToWrite = "string"
            else:
                dataToWrite = "nil"

        # Riadenie toku progrmau
        elif instruction.opcode == "LABEL":
            pass

        elif instruction.opcode == "JUMP":
            if label not in labelsList:
                errorOccured(Errors.semantics, "JUMP label not defined")
            current_instruction = labelsIndex[label]
            
        elif instruction.opcode == "JUMPIFEQ":
            if label not in labelsList:
                errorOccured(Errors.semantics, "JUMPIFEQ label not defined")            
            if type(arg2data) != type(arg3data):
                errorOccured(Errors.operand_types, "JUMPIFEQ operand types do not match")

            if arg2data == arg3data:
                current_instruction = labelsIndex[label]        
            
        elif instruction.opcode == "JUMPIFNEQ":
            if label not in labelsList:
                errorOccured(Errors.semantics, "JUMPIFNEQ label not defined")
            if type(arg2data) != type(arg3data):
                errorOccured(Errors.operand_types, "JUMPIFEQ operand types do not match")

            if arg2data != arg3data:
                current_instruction = labelsIndex[label] 

        elif instruction.opcode == "EXIT":
            if type(arg2data) != int:
                errorOccured(Errors.operand_types, "EXIT argument not int")
            if arg2data < 0 or arg2data > 49:
                errorOccured(Errors.operand_wrong_val)
            sys.exit(arg2data)

        # Ladiace instrukcie
        elif instruction.opcode == "DPRINT":
            if type(arg2data) != int and type(arg2data) != bool and type(arg2data) != str:
                print("nil", file=sys.stderr, end="")
            else:
                print(arg2data, file=sys.stderr, end="")

        elif instruction.opcode == "BREAK":
            print("Current number of instruction: " + str(current_instruction), file=sys.stderr)
            print("Count of the processed instructions: " + str(processed_instruction), file=sys.stderr)
            print("GF: ", GF, file=sys.stderr)
            print("LF: ", LF, file=sys.stderr)
            print("TF: ", TF, file=sys.stderr)

        # Zapis vysledku do premennej
        if instruction.opcode in ("READ", "ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "NOT", "INT2CHAR", "STRI2INT", "CONCAT", "STRLEN", "MOVE", "GETCHAR", "SETCHAR", "TYPE"):
            if instruction.arguments[0].atype == "var":
                frame = instruction.arguments[0].value.split("@", 1)[0]
                var = instruction.arguments[0].value.split("@", 1)[1]
                
                if frame == "GF":	
                    GF[var] = dataToWrite
                elif frame == "LF":
                    LF[-1][var] = dataToWrite
                elif frame == "TF":
                    TF[var] = dataToWrite
        