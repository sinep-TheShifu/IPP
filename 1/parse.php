<?php
// Import knihovien .
include_once "src/library.php";
include_once "src/functions.php";

// Vypis varovania na stderr 
//ini_set('display_errors', 'stderr');

// Kontrola argumentov programu 
// Ziskam pole objektov pokial su zadefinovane argumenty statistik
control_arguments();

// Citanie vstupu
while(!feof(STDIN))
{
    // Nacitanie 1 riadku
    $line = fgets(STDIN); 

    // Uprava riadku - odstranenie komentarov, bielych znakov...
    $line = parse_line($line); 

    // Dany riadok je bud prazdny alebo komentar -> preskoci sa
    if($line == null)
        continue;

    // Kontrola existujucej hlavicky kodu IPPcode2021
    if($language_identified == false)
    {
        if(control_header($line) == OK)
        {
            $language_identified = true;
            continue;
        }
        else
        {
            fwrite(STDERR, "Missing or wrong language identifier!\n");
            exit(ERR_HEADER_MISSING);
        }
    }

    // Kontrola syntaxu
    control_syntax_and_outputXML($line);
}

// Vypis celej struktury XML dokumentu na STDOUT
$xml->write_XML();

return OK;
?>