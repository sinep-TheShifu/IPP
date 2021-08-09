<?php
/** Premenne */
$language_identified = false;   // Overenie hlavicky
$xml = new XMLOutput();         // XML vystup

/** Definicie navratovych hodnot kodu */
// Preddefinovane errory
const ERR_PARAM = 10;
const ERR_FOPEN_INPUT = 11;
const ERR_FOPEN_OUTPUT = 12;

const ERR_HEADER_MISSING = 21;
const ERR_OPCODE = 22;
const ERR_LEX_OR_SYN = 23;

const ERR_INTERNAL = 99;

const ERR_MULTI_FILE = 12;

// Vlastne navratove hodnoty
const OK = 0;
const ERR = 1;
const NO_ARGS = 2;

/** Struktury */
// Objekt pre vypis XML
class XMLOutput
{
    private $xml;
    private $numOfInstruction;

    // Konstruktor
    public function __construct()
    {
        // Instancia objektu XMLWriter pre vypis XML
        $this->xml = new XMLWriter();
        $this->xml->openMemory();
        $this->xml->setIndent(1);

        // Inicializacia poradia instrukcii
        $this->numOfInstruction = 0;

        // XML hlavicka
        $this->xml->startDocument("1.0", "UTF-8");
        $this->xml->startElement("program");
        $this->xml->writeAttribute("language", "IPPcode21");
    }

    // Zapis instrukcie
    public function write_instruction($op_code)
    {
        $this->xml->startElement("instruction");                        // Zaciatok instrukcie
        $this->xml->writeAttribute("order", ++$this->numOfInstruction);   // Poradie instrukcie
        $this->xml->writeAttribute("opcode", $op_code);                 // Operacny kod instrukcie
    }

    // Ukonci element instrukcie 
    public function end_instruction()
    {
        $this->xml->endElement();
    }

    // Zapis operandu 
    public function write_operand($num, $type, $value)
    {
        $this->xml->startElement("arg".$num);       // Zaciatok elementu
        $this->xml->writeAttribute("type", $type);  // Typ operandu
        $this->xml->text($value);                   // Hodnota operandu
        $this->xml->endElement();                   // Koniec elementu
    }

    // Vypis XML na STDOUT
    public function write_XML()
    {
        $this->xml->endDocument();
        echo $this->xml->outputMemory();
    }
}

/** Polia */
// Pole vsektych instrukcii
$ListOfInstructions = array(
    // Praca s ramcami, volanie funkcii
    "MOVE"          => 2,
    "CREATEFRAME"   => 0,
    "PUSHFRAME"     => 0,
    "POPFRAME"      => 0,
    "DEFVAR"        => 1,
    "CALL"          => 1,
    "RETURN"        => 0,

    // Praca s datovym zasobnikom
    "PUSHS"         => 1,
    "POPS"          => 1,

    // Aritmeticke, relacne, boolovske a konverzne instrukcie
    "ADD"           => 3,
    "SUB"           => 3,
    "MUL"           => 3,
    "IDIV"          => 3,
    "LT"            => 3,
    "GT"            => 3,
    "EQ"            => 3,
    "AND"           => 3,
    "OR"            => 3,
    "NOT"           => 2,
    "INT2CHAR"      => 2,
    "STRI2INT"       => 3,

    // Vstupno-vystupne instrukcie
    "READ"          => 2,
    "WRITE"         => 1,

    // Praca s retazcami
    "CONCAT"        => 3,
    "STRLEN"        => 2,
    "GETCHAR"       => 3,
    "SETCHAR"       => 3,

    // Praca s typami
    "TYPE"          => 2,

    // Pre riadenie toku programu
    "LABEL"         => 1,
    "JUMP"          => 1,
    "JUMPIFEQ"      => 3,
    "JUMPIFNEQ"     => 3,
    "EXIT"          => 1,

    // Ladiace instrukcie
    "DPRINT"        => 1,
    "BREAK"         => 0
);


// Mozne argumenty programu
$programm_arguments = array(
    "--loc" => 0,
    "--comments" => 1,
    "--lables" => 2,
    "--jumps" => 3,
    "--fwjumps" => 4,
    "--backjumps" => 5,
    "--badjumps" => 6,
    "parse.php" => 7
)
?>
