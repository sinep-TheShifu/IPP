<?php
/** Import kniznic */
require_once "library.php";

/** Napoveda */
function help()
{
    fwrite(STDOUT, "------------ HELP ------------\n
Skrypt typu filter nacita zo STDIN zdrojovy\n
kod v jazyku IPPcode21, skontroluje lexikalnu\n
a syntakticku spravnost a nastnedne vypise na STDOUT\n
    vystup XML reprezentacie programu.\n");
}

/** Kontrola argumentov programu */
function control_arguments()
{
    global $argc;
    global $argv;
    global $programm_arguments;
    
    // Spustene bez argumentov
    if($argc == 1)    
        return;
    
    // Zadanie help
    if($argc == 2 && $argv[1] == '--help')
    {
        help();
        exit(OK);
    }    

    // Prechadzanie vsetkymi argumentami
    foreach($argv as $arg)
    {
        // Kontrola vyskytu moznych argumentov - rozsirenia STATI
        if(array_key_exists($arg, $programm_arguments) === false && substr($arg, 0, 8) != "--stats=")
        {
            fwrite(STDERR, "Wrong programm arguments!\n");
            exit(ERR_PARAM);
        }
    }  
}

/** Parsovanie riadku - odstranenie komentarov, prazdnych riadkov, bielych znakov*/
function parse_line($line)
{
    // Vymaze biele znaky zo zaciatku a konca riadku
    $line = trim($line);    

    // Odstranenie komentara
    $comm_pos = strpos($line, "#", 0);
    if($comm_pos !== false)
    {
        $line = trim(substr($line, 0, $comm_pos));
    } 
    
    // Nahradenie viacerych za sebou iducich bielych znakov za 1 medzeru
    $line = preg_replace("/\s+/", " ", $line);

    // Prazdny riadok 
    if($line == "") return null; 
    
    return $line;
}

/** Kontrola hlavicky */
function control_header($line)
{
    $line = strtoupper($line);

    if($line == ".IPPCODE21") return OK;
    
    return ERR;
}

/** Kontrola syntaxu a zapis do XML*/
function control_syntax_and_outputXML($line)
{
    // Globalne premenne
    global $xml;
    global $ListOfInstructions; 

    // Rozdelenie vety na pole slov
    $line = explode(" ", $line);

    // Pri operacnom kode nezalezi na velkosti pismen
    $line[0] = strtoupper($line[0]);

    // Kontrola existencie operacneho kodu
    if(array_key_exists($line[0], $ListOfInstructions) === false)
    {
        fwrite(STDERR, "Missing or wrong operation code of an instruction!\n");
        exit(ERR_OPCODE);
    }

    // Kontrola spravneho poctu operandov
    $numOfOperandsOfInstruction = $ListOfInstructions[$line[0]];
    $numOfOperandsInLine = count($line) - 1;
    if($numOfOperandsInLine != $numOfOperandsOfInstruction)
    {
        fwrite(STDERR, "Operation code has a wrong number of operands!\n");
        exit(ERR_LEX_OR_SYN);
    }

    // Zapis instrukcie do instancie XML objektu
    $xml->write_instruction($line[0]);

    // Instrukcie bez operandov
    if($line[0] == "CREATEFRAME" ||
       $line[0] == "PUSHFRAME"   ||
       $line[0] == "POPFRAME"    ||
       $line[0] == "RETURN"      ||
       $line[0] == "BREAK")
    {
        // Ukoncim instrukciu
        $xml->end_instruction();
        return;
    }
    // Instrukcie s operandom <var>
    elseif($line[0] == "DEFVAR" ||
           $line[0] == "POPS")
    {
        // Kontrola a zapis operandu var do XML
        operand_var($line[1]); 
        $xml->write_operand(1, "var", $line[1]);
    }
    // Instrukcie s operandom <label>
    elseif($line[0] == "CALL"   ||
           $line[0] == "LABEL"  ||
           $line[0] == "JUMP")
    {
        // Kontrola a zapis operandu label do XML
        operand_label($line[1]);   
        $xml->write_operand(1, "label", $line[1]);
    }
    // Instrukcie s operandom <symb>
    elseif($line[0] == "PUSHS" || 
           $line[0] == "WRITE" ||
           $line[0] == "EXIT"  ||
           $line[0] == "DPRINT")
    {
        // Kontrola a zapis operandu symb do XML
        $value = operand_symb($line[1]);
        $xml->write_operand(1, $value[0], $value[1]);
    }
    // Instrukcie s operandami <var> <symb>
    elseif($line[0] == "MOVE"       ||
           $line[0] == "NOT"        ||
           $line[0] == "INT2CHAR"   ||
           $line[0] == "STRLEN"     ||
           $line[0] == "TYPE")
    {
        // Kontrola a zapis operandu var do XML
        operand_var($line[1]);
        $xml->write_operand(1, "var", $line[1]);

        // Kontrola a zapis operandu symb do XML
        $values = operand_symb($line[2]);
        $xml->write_operand(2, $values[0], $values[1]);
    }
    // Instrukcie s operandami <var> <type>
    elseif($line[0] == "READ")
    {
        // Kontrola a zapis operandu var do XML
        operand_var($line[1]);
        $xml->write_operand(1, "var", $line[1]);

        // Kontrola a zapis operandu type do XML
        operand_type($line[2]);
        $xml->write_operand(2, "type", $line[2]);
    }
    // Instrukcie s operandami <var> <symb> <symb>
    elseif($line[0] == "ADD"        ||
           $line[0] == "SUB"        ||
           $line[0] == "MUL"        ||
           $line[0] == "IDIV"       ||
           $line[0] == "LT"         ||
           $line[0] == "GT"         ||
           $line[0] == "EQ"         ||
           $line[0] == "AND"        ||
           $line[0] == "OR"         ||
           $line[0] == "STRI2INT"   ||
           $line[0] == "CONCAT"     ||
           $line[0] == "GETCHAR"    ||
           $line[0] == "SETCHAR")
    {
        // Kontrola a zapis operandu var do XML
        operand_var($line[1]);      
        $xml->write_operand(1, "var", $line[1]);

        // Kontrola a zapis operandu symb do XML
        $values = operand_symb($line[2]);
        $xml->write_operand(2, $values[0], $values[1]);

        // Kontrola a zapis oparandu symb do XML
        $values2 = operand_symb($line[3]);
        $xml->write_operand(3, $values2[0], $values2[1]);
    }
    // Instrukcie s operandami <label> <symb> <symb>
    elseif($line[0] == "JUMPIFEQ"   ||
           $line[0] == "JUMPIFNEQ")
    {
        // Kontrola a zapis operandu label do XML
        operand_label($line[1]);
        $xml->write_operand(1, "label", $line[1]);

        // Kontrola a zapis operandu symb do XML
        $values = operand_symb($line[2]);
        $xml->write_operand(2, $values[0], $values[1]);

        // Kontrola a zapis operandu symb do XML
        $values2 = operand_symb($line[3]);
        $xml->write_operand(3, $values2[0], $values2[1]);
    }

    // Ukoncim instrukciu
    $xml->end_instruction();
}

// Skontroluje spravnost operandu <var>
function operand_var($operand)
{
    // Premenna sa sklada z dvoch casti oddelenych @
    // Staci skontrolovat spravnu strukturu operandu
    if(preg_match('/LF@[a-zA-Z_\-\$\&\%\*\!\?][0-9a-zA-Z_\-\$\&\%\*\!\?]*|GF@[a-zA-Z_\-\$\&\%\*\!\?][0-9a-zA-Z_\-\$\&\%\*\!\?]*|TF@[a-zA-Z_\-\$\&\%\*\!\?][0-9a-zA-Z_\-\$\&\%\*\!\?]*/', $operand, $matches))
    {
        if($operand != $matches[0])
        {
            fwrite(STDERR, "Operation code has a wrong operand <var>!\n");
            exit(ERR_LEX_OR_SYN);
        }
    }
    else
    {
        fwrite(STDERR, "Operation code has a wrong operand <var>!\n");
        exit(ERR_LEX_OR_SYN);
    }    
}

// Skontroluje spravnost operandu <label>
function operand_label($operand)
{
    // Navestie ma rovnake pravidla ako meno premennej
    // Staci skontrolovat jeho strukturu
    if(preg_match('/[a-zA-Z_\-\$\&\%\*\!\?][0-9a-zA-Z_\-\$\&\%\*\!\?]*/', $operand, $matches))
    {
        if($operand != $matches[0])
        {
            fwrite(STDERR, "Operation code has a wrong operand <label>!\n");
            exit(ERR_LEX_OR_SYN);
        }
    }
    else
    {
        fwrite(STDERR, "Operation code has a wrong operand <label>!\n");
        exit(ERR_LEX_OR_SYN);
    }
}

// Skontroluje spravnost operandu <type>
function operand_type($operand)
{
    if(preg_match('/int|string|bool/', $operand, $matches))
    {
        if($operand != $matches[0])
        {
            fwrite(STDERR, "Operation code has wrong operand <type>!\n");
            exit(ERR_LEX_OR_SYN);
        }
    }
    else
    {
        fwrite(STDERR, "Operation code has wrong operand <type>!\n");
        exit(ERR_LEX_OR_SYN);
    }
}

// Skontroluje spravnost oprandu <symb> a vrati jeho typ a hodnotu
function operand_symb($operand)
{
    // <symb> moze nadobudat konstantu alebo premennu
    // Premenna je typu <var>
    // Konstanty mozu byt typu: int, bool, string, nil
    // @ oddeluje typ a hodnotu konstant
    // Vraciam typ a hodnotu premennej
    
    // Regex pre string
    if(preg_match("/string@(?:[^\#\ ]*)/", $operand, $matches))
    {
        if($operand != $matches[0])
        {
            fwrite(STDERR, "Operation code has wrong operand <symb>!\n");
            exit(ERR_LEX_OR_SYN);
        }

        // Kontrola escape sekvencie
        for($i = 0; $i < strlen($operand); $i++)
        {
            // Operand obsahuje escape sekvenciu
            if($operand[$i] == "\\")
            {
                // Ziskam jej ciselnu cast
                $number = substr($operand, $i + 1, 3);
                // Prevediem numeric string na int
                $int_val = intval($number);
                // Kontrola 
                if(is_numeric($number) === false || $int_val < 0)
                {
                    fwrite(STDERR, "Operation code has wrong operand <symb>!\n");
                    exit(ERR_LEX_OR_SYN);
                }
            }
        }

        $values[0] = "string";
        $values[1] = substr($operand, 7);
        return $values;
    }
    // Regex pre premennu
    elseif(preg_match('/LF@[a-zA-Z_\-\$\&\%\*\!\?][0-9a-zA-Z_\-\$\&\%\*\!\?]*|GF@[a-zA-Z_\-\$\&\%\*\!\?][0-9a-zA-Z_\-\$\&\%\*\!\?]*|TF@[a-zA-Z_\-\$\&\%\*\!\?][0-9a-zA-Z_\-\$\&\%\*\!\?]*/', $operand, $matches))
    {
        if($operand != $matches[0])
        {
            fwrite(STDERR, "Operation code has a wrong operand <symb>!\n");
            exit(ERR_LEX_OR_SYN);
        }

        $values[0] = "var";
        $values[1] = $operand;
        return $values;
    }
    // Regex pre nil
    elseif(preg_match('/nil@nil/', $operand, $matches))
    {
        if($operand != $matches[0])
        {
            fwrite(STDERR, "Operation code has a wrong operand <symb>!\n");
            exit(ERR_LEX_OR_SYN);
        }

        $values[0] = "nil";
        $values[1] = "nil";
        return $values;
    }
    // Regex pre int
    elseif(preg_match('/int@(?:\+)?(?:\-)?[0-9]+/', $operand, $matches))
    {
        if($operand != $matches[0])
        {
            fwrite(STDERR, "Operation code has a wrong operand <symb>!\n");
            exit(ERR_LEX_OR_SYN);
        }

        $values[0] = "int";
        $values[1] = substr($operand, 4);
        return $values;
    }
    // Regex pre bool
    elseif(substr($operand, 0, 5) == "bool@")
    {
        // Zadanie - zapisovat malymi pismenami
        $operand = strtolower($operand);

        if(preg_match("/(?:bool@true)|(?:(?:bool\@false))/", $operand, $matches))
        {
            if($operand != $matches[0])
            {
                fwrite(STDERR, "Operation code has wrong operand <symb>!\n");
                exit(ERR_LEX_OR_SYN);
            }

            $values[0] = "bool";
            $values[1] = substr($operand, 5);
            return $values;
        }
        else
        {
            fwrite(STDERR, "Operation code has wrong operand <symb>!\n");
            exit(ERR_LEX_OR_SYN);
        }
    }
    // Ak sa nic nenaslo
    else
    {
        fwrite(STDERR, "Operation code has wrong operand <symb>!\n");
        exit(ERR_LEX_OR_SYN);
    }
}
?>