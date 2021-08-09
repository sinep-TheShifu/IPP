<?php
$args = new ProgramArguments();         // Objekt pre ukladanie argumentov

parse_arguments($argc, $argv);   // Spracovanie argumentov
control_arguments();               // Kontrola argumentov

$html = new HTMLDocument();             // Vytvorenie dokumente pre vysledkov

get_files($args->directory);            // Hladanie suborov a spustenie testovania

$html->RenderHTML();                    // Vygenerovanie HTML kodu

// Ziskam vsetky subory/priecinky v zadanej ceste, zavola sa testovanie
function get_files($directory)
{
    global $args;

    $files = scandir($directory); // Vsetky subory v zadanej ceste

    if(isset($args->recursive))
    {
        foreach($files as $file)
        {   // Prechadzam kazdy subor
            if($file == "." || $file == "..")
            {   // Preskocenie ciest -> zabrani nekonecnemu cyklu
                continue;
            }
            if(is_dir($directory . "/" . $file))
            {   // Najdena cesta -> rekurzia
                get_files($directory . "/" . "$file");
            }
        }
    }

    start_test($directory); // Testovanie
}

// Testovanie ziskanych suborov
function start_test($dir)
{
    // Statistiky pre danu cestu
    $yea_count = 0;
    $nay_count = 0;

    $files = glob($dir . "/*.src");

    if($files == false)
    {   // Nenasli sa ziadne subory s priponou .src
        return;
    }

    foreach($files as $file)
    {   // Kontrola vyskytu suborov: .rc, .in, .out
        check_files($file);
    }

    
    global $html, $args;    // Globalne premenne

    $html->start_dir($dir); // Vypise start testovania cesty

    // Prechadzanie .src subormy adresara
    foreach($files as $file)
    {
        $html->all_count++;             // Inkrementacia celkoveho poctu testov

        $rc = get_rc($file);            // Ocakavany navratovy kod
        $out_file = get_out($file);     // Subor .out
        $in_file = get_in($file);       // Subor .in

        // TESTOVANIE PARSE.PHP
        if($args->parse_only || (!$args->parse_only && !$args->int_only))
        {   // Pokial sa testuje iba parser alebo oba
            // Spustenie testu
            exec("timeout 3 php7.4 -f \"$args->parse_script\" < \"$file\" 2> /dev/null > tmp_pars.out ",
            $output, $retval);

            if($retval === 124)
            {   // Program trval dlhzsiu dobu ako 3
                $nay_count++;
                $html->test_failed(str_replace($dir, "", $file), $retval, $rc);
                del_files();    // Odstranenie pomocnych suborov
                continue;       // Zly test -> netestovat interpret
            }
            elseif($retval !== $rc)
            {   // Navratove kody sa nezhoduju
                $nay_count++;
                $html->test_failed(str_replace($dir, "", $file), $retval, $rc);
                del_files();
                continue;
            }
            elseif($retval !== 0)
            {   // Navratove kody sa rovnaju a niesu 0 -> nekontroluje sa obsah
                if($args->parse_only)
                {   // Test presiel
                    $yea_count++;
                    $html->test_passed(str_replace($dir, "", $file), $retval, $rc);
                }
            }
            else
            {   // Navratove kody su spravne -> kontrola obsahu
                // Porovnanie s A7Soft JExamXML pri parse-only argumente ?
                exec("java -jar \"$args->jexamxml\" \"$out_file\" \"tmp_pars.out\" ", $out, $retval);

                if($retval !== 0)
                {   // Nebola zhoda
                    $nay_count++;
                    $html->test_failed(str_replace($dir, "", $file), $retval, $rc);
                    del_files();
                    continue;
                }
                else
                {   // Obsah spravny
                    if($args->parse_only)
                    {   // Test presiel
                        $yea_count++;
                        $html->test_passed(str_replace($dir, "", $file), $retval, $rc);
                    }                    
                }
            }
        }

        // TESTOVANIE INTERPRET.PY
        if($args->int_only || (!$args->int_only && !$args->parse_only))
        {   // Pokial sa testuje iba interpret alebo oba
            if($args->int_only)
            {   // Vstupny subor pre interpret
                $src_file = $file;
            }
            else
            {   // Vygenerovany cez parse.php
                $src_file = "./tmp_pars.out";
            }

            // Spustenie testu
            exec("timeout 3 python3.8 \"$args->int_script\" --source=$src_file --input=$in_file 1> \"tmp_int.out\" 2> /dev/null", $out, $retval);

            if($retval === 124)
            {   // Timetout bol prekroceny
                $nay_count++;
                $html->test_failed(str_replace($dir, "", $file), $retval, $rc);
            }
            elseif($retval !== $rc)
            {   // Navratove kody sa nerovnaju
                $nay_count++;
                $html->test_failed(str_replace($dir, "", $file), $retval, $rc);
            }
            else
            {   // Navratove kody su zhodne
                if($retval !== 0)
                {   // Nenulovy navratovy kod -> netreba kontrolovat vystup
                    $yea_count++;
                    $html->test_passed(str_replace($dir, "", $file), $retval, $rc);
                }
                else
                {   // Porovnanie vystupu pomocou diff
                    exec("diff tmp_int.out $out_file > /dev/null 2>&1", $outp, $retval);

                    if($retval !== 0)
                    {   // Nezhoduje sa
                        $nay_count++;
                        $html->test_failed(str_replace($dir, "", $file), $retval, $rc);
                    }
                    else
                    {   // Zhoduje sa
                        $yea_count++;
                        $html->test_passed(str_replace($dir, "", $file), $retval, $rc);
                    }
                }
            }
        }
    }    

    // Odstranenie pomocnych suborov
    del_files();

    // Vypis statistik adresara
    $html->end_dir($yea_count, $nay_count);
}

// Odstranenie pomocnych suborov
function del_files()
{
    exec("rm -f tmp_pars.out");
    exec("rm -f tmp_int.out");
}

// Vrati kod z .rc suboru
function get_rc($file)
{
    $tmp = fopen(str_replace(".src", ".rc", $file), "r");
    $rc = fgets($tmp);
    fclose($tmp);
    return (int)$rc;
}

// Vrati .in nazov suboru
function get_in($file)
{
    return str_replace(".src", ".in", $file);
}

// Vrati .out nazov suboru
function get_out($file)
{
    return str_replace(".src", ".out", $file);
}

// Kontrola vyskytu suborov, ich pripadne vytvorenie
function check_files($file)
{
    if(!file_exists(str_replace(".src", ".in", $file)))
    {   // .in
        $in_file = fopen(str_replace(".src", ".in", $file), "w");
        if($in_file === false)
        {   // Subor sa nedal otvorit
            fwrite(STDERR, "Coldnt open file: $in_file\n");
            exit(11);
        }
        fclose($in_file);   // Zatvorenie subory
    }

    if(!file_exists(str_replace(".src", ".out", $file)))
    {   // .out
        $out_file = fopen(str_replace(".src", ".out", $file), "w");
        if($out_file === false)
        {   // Subor sa nedal otvorit
            fwrite(STDERR, "Couldnt open file: $out_file");
            exit(11);
        }
        fclose($out_file);  // Zatvorenie suboru
    }

    if(!file_exists(str_replace(".src", ".rc", $file)))
    {   // .rc
        $rc_file = fopen(str_replace(".src", ".rc", $file), "w");
        if($rc_file === false)
        {   // Subor sa nedal otvorit
            fwrite(STDERR, "Couldnt open file: $rc_file\n");
            exit(11);
        }
        fwrite($rc_file, "0");  // Implicitna hodnota 0
        fclose($rc_file);       // Zatvorenie suboru
    }
}

// Parsovanie argumentov
function parse_arguments($argc, $argv)
{
    global $args;   // Globalna premenna

    if($argc == 1) return;
    
    if($argc == 2)
    {
        if($argv[1] == "--help")
        {
            help();
            exit(0);
        }    
    }

    foreach($argv as $arg)
    {
        if($arg == "test.php")
        {
            continue;
        }
        elseif(substr($arg, 0, 12) == "--directory=")
        {
            $args->directory = substr($arg, 12);
        }            
        elseif($arg == "--recursive")
        {
            $args->recursive = true;
        }            
        elseif(substr($arg, 0, 15) == "--parse-script=")
        {
            $args->parse_script = substr($arg, 15);
        }
        elseif(substr($arg, 0, 13) == "--int-script=")
        {
            $args->int_script = substr($arg, 13);
        }
        elseif($arg == "--parse-only")
        {
            $args->parse_only = true;
        }
        elseif($arg == "--int-only")
        {
            $args->int_only = true;
        }
        elseif(substr($arg, 0, 11) == "--jexamxml=")
        {
            $args->jexamxml = substr($arg, 11);
        }
        elseif(substr($arg, 0, 11) == "--jexamcfg=")
        {
            $args->jexamcfg = substr($arg, 11);
        }
        else
        {
            fwrite(STDERR, "Wrong arguments\n");
            exit(10);
        }
    }
}

// Kontrola zadanych argumentov
function control_arguments()
{
    global $args; // Globalna premenna

    if(isset($args->parse_only) && (isset($args->int_only) || isset($args->int_file)))
    {   // Argument parse-only nieje kombinovatelny s int-only a int-file
        fwrite(STDERR, "Wrong arguments\n");
        exit(10);
    }

    if(isset($args->int_only) && (isset($args->parse_only) || isset($args->parse_file)))
    {   // Argument int-only nieje kombinovatelny s parse-only a parse-file
        fwrite(STDERR, "Wrong arguments\n");
        exit(10);
    }

    if(!isset($args->directory))
    {   // Implicitne aktualna cesta
        $args->directory = getcwd();
    }

    if(!is_dir($args->directory))
    {   // Zadana cesta nieje cesta alebo niesu dostatocne prava
        fwrite(STDERR, "Not a directory: $args->directory\n");
        exit(41);
    }

    if(!isset($args->parse_script))
    {   // Implicitne subor parse.php v aktualnej ceste
        $args->parse_script = getcwd() . "/parse.php";
    }

    if(!isset($args->int_only) && !file_exists($args->parse_script))
    {   // Kontrola existenciu suboru
        fwrite(STDERR, "File doesnt exist: $args->parse_script\n");
        exit(41);
    }

    if(!isset($args->int_script))
    {   // Implicitne subor interpret.py v aktualnej ceste
        $args->int_script = getcwd() . "/interpret.py";
    }

    if(!isset($args->parse_only) && !file_exists($args->int_script))
    {   // Kontrola existencie suboru
        fwrite(STDERR, "File doesnt exist: $args->int_script\n");
        exit(41);
    }

    if(!isset($args->jexamxml))
    {   // Implicitna cesta k balicku jar
        $args->jexamxml = "/pub/courses/ipp/jexamxml/jexamxml.jar";
    }

    if(isset($args->parse_only) && !file_exists($args->jexamxml))
    {   // Kontrola existencie suboru
        fwrite(STDERR, "File does not exist: $args->jexamxml\n");
        exit(41);
    }

    if(!isset($args->jexamcfg))
    {   // Implicitna cesta k konfiguracnemu suboru 
        $args->jexamcfg = "/pub/courses/ipp/jexamxml/options";
    }

    if(isset($args->parse_only) && !file_exists($args->jexamxml))
    {   // Kontrola existencie subory
        fwrite(STDERR, "File does not exist: $args->jexamcfg\n");
        exit(41);  
    }
}

// Vypis napovedy
function help()
{
    print("Tento program testuje skript so zadanou testovacou sadou.\n
    ARGUMENTY:\n
    --help              - vypise napovedu\n
    --directory=path    - path je cesta k zlozke s testami\n
                            - implicitne sa prehladava aktualna zlozka\n
    --recursive         - rekurzivne prehladavanie zadanej zlozky\n
    --parse-script=file - file je cesta ku skriptu parseru\n
    --int-script=file   - file je cesta k skriptu interpreta\n
    --parse-only        - testuje sa iba parser\n
    --int-only          - testuje sa iba interpret\n
    --jexamxml=file     - file je cesta k suboru s JAR balikom s nastrojom A7Soft JExamXML\n
    --jexamcfg=file     - je cesta k suboru s konfiguraciou nastroja A4Soft JExamXML\n");

}

// Trieda pre HTML dokument
class HTMLDocument 
{
    private $html;          // HTML struktura
    public $all_count;      // Pocet vsetkych testov =-> yea + nay?
    private $yea_count;     // Pocet uspesnych testov
    private $nay_count;     // Pocet neuspesnych testov    

    // Vytvori zakladnu strukturu HTML dokumentu
    public function __construct()
    {
        $this->all_count = 0;
        $this->yea_count = 0;
        $this->nay_count = 0;
        $this->html =   "<!DOCTYPE html>\n".
                        "<html>\n".
                        "<head>\n<meta charset=\"utf-8\">\n<title>IPP PROJEKT</title>\n</head>\n".
                        "<body>\n<h1>VUT FIT</h1>\n<h2>Autor: Daniel Andrasko</h2>\n\n".
                        "<style>.fail{color:red;}.pass{color:green;}</style>\n\n";
    }

    // Vypise HTML na STDOUT, prida koniec dokumentu
    public function RenderHTML()
    {
        $result = $this->yea_count / $this->all_count * 100;

        $this->html = $this->html . "<br><br><h2>ALL TESTS RESULT</h2>\n". 
                                    "<h3>Number of tests: $this->all_count\n".
                                    "<h3>Passed: $this->yea_count</h3>\n". 
                                    "<h3>Failed: $this->nay_count</h3>\n".
                                    "<h2>Result is $result% success!\n". 
                                    "</body>\n</html>\n";
        echo $this->html;
    }

    // Vypise zaciatok adresara
    public function start_dir($dir)
    {
        $this->html = $this->html . "<br><br><h3>TESTING DIRECTORY</h3>\n".
                                    "<h3>$dir</h3>\n";
    }

    // Vypise statistiky adresara
    public function end_dir($yea, $nay)
    {
        $all = $yea + $nay;
        $result = $yea / $all * 100;
        $this->html = $this->html . "<h3>Directory Results</h3>\n".
                                    "<h4>All tests: $all</h4>\n". 
                                    "<h4>Tests passed: $yea</h4>\n". 
                                    "<h4>Tests failed: $nay</h4>\n".
                                    "<h3>Result: $result%</h3>\n\n";
    }

    // Uspesny test
    public function test_passed($file, $rc, $exp_rc)
    {
        $this->yea_count++;
        $this->html = $this->html . "$this->all_count. FILE: $file <span class=\"pass\">PASSED </span>".
                                    "expected rc: $exp_rc actual rc: $rc<br>\n";
    }

    // Neuspesny test
    public function test_failed($file, $rc, $exp_rc)
    {
        $this->nay_count++;
        $this->html = $this->html . "$this->all_count. FILE: $file <span class=\"fail\">FAILED </span>".
        "expected rc: $exp_rc actual rc: $rc<br>\n";
    }
}

// Trieda pre argumenty
class ProgramArguments 
{    
    public $directory;
    public $recursive;
    public $parse_script;
    public $int_script;
    public $parse_only;
    public $int_only;
    public $jexamxml;
    public $jexamcfg;
}
?>