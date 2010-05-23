#define PY_SSIZE_T_CLEAN
#define SIZEINC 80
#define MAXDEPTH 10
#include <Python.h>

typedef struct tagRuleReturn
{
    Py_ssize_t pos;
    Py_ssize_t len;
    Py_UNICODE *text;
} RuleReturn;

typedef struct tagAutoConvertReturn
{
    Py_ssize_t len;
    Py_UNICODE *text;
} AutoConvertReturn;

typedef struct tagHooks
{
    PyObject *depth_exceed_msg;
    PyObject *rule_parser;
} Hooks;

typedef struct tagTables
{
    PyObject *conv_table;
    PyObject *quick_table;
}Tables;

const Py_UNICODE TOKEN_A = (Py_UNICODE)('-');
const Py_UNICODE TOKEN_B = (Py_UNICODE)('{');
const Py_UNICODE TOKEN_C = (Py_UNICODE)('}');

static Hooks hooks;
static Tables tables;
static Py_ssize_t maxlen;

/*static UNISIZE parse_rule(Py_UNICODE *text);*/
static RuleReturn recursive_convert_rule (Py_UNICODE *text, Py_ssize_t pos,
                                          Py_ssize_t len, int depth);
static AutoConvertReturn auto_convert(Py_UNICODE *input, Py_ssize_t inputlen, int parserules);
static PyObject *convert (PyObject *self, PyObject *args);

static RuleReturn recursive_convert_rule (Py_UNICODE *text, Py_ssize_t pos,
                                          Py_ssize_t len, int depth)
{
    Py_ssize_t retlen; // the real length (allocated size) of the ret.text
    int exceedtime = 0; // count exceed time
    Py_UNICODE *texttemp;
    RuleReturn ret; // the return structure
    AutoConvertReturn aret;
    
    ret.pos = pos;
    ret.len = 0;
    ret.text = PyMem_NEW(Py_UNICODE, SIZEINC);
    retlen = SIZEINC;
    
    
    while (ret.pos < len) {
        if (ret.pos + 1 < len) {
            if (text[ret.pos] == TOKEN_A && text[ret.pos + 1] == TOKEN_B) { // begins with "-{"
                if (depth < MAXDEPTH) {
                    RuleReturn ret2 = recursive_convert_rule(text, ret.pos + 2, len, depth + 1);
                    
                    if (ret.len + ret2.len >= retlen) { // resize memory
                        retlen += (ret2.len / SIZEINC + 1) * SIZEINC;
                        PyMem_RESIZE(ret.text, Py_UNICODE, retlen);
                    }
                    
                    memcpy(ret.text + ret.len, ret2.text, ret2.len * sizeof(Py_UNICODE));
                    ret.pos = ret2.pos;
                    ret.len += ret2.len;
                    PyMem_DEL(ret2.text);
                    continue;
                }
                else {
                    if (!exceedtime && hooks.depth_exceed_msg != NULL) {
                        PyObject *depthobj = PyInt_FromLong(depth);
                        PyObject *msg = PyObject_CallFunctionObjArgs(hooks.depth_exceed_msg, depthobj, NULL);
                        Py_XDECREF(depthobj);
                        if (msg != NULL) {
	                        Py_ssize_t msglen = PyUnicode_GET_SIZE(msg);
	                        Py_UNICODE *msgtext = PyUnicode_AS_UNICODE(msg);
	                        if (ret.len + msglen >= retlen) {
	                            retlen += (msglen / SIZEINC + 1) * SIZEINC;
	                            PyMem_RESIZE(ret.text, Py_UNICODE, retlen);
	                        }
	                        memcpy(ret.text + ret.len, msgtext, msglen * sizeof(Py_UNICODE));
	                        ret.len += msglen;
                    	}
                    	Py_XDECREF(msg);
                    }
                    exceedtime ++;
                }
            }
            else if (text[ret.pos] == TOKEN_C && text[ret.pos + 1] == TOKEN_A) { // ends with "}-"
                if (depth >= MAXDEPTH && exceedtime) {
                    exceedtime --;
                }
                else if (hooks.rule_parser != NULL) {
                    PyObject *textobj;
                    PyObject *oldtextobj = PyUnicode_FromUnicode(ret.text, ret.len);
                    textobj = PyObject_CallFunctionObjArgs(hooks.rule_parser, oldtextobj, NULL);
                    Py_XDECREF(oldtextobj);
                    ret.pos += 2; // "}-"
                    if (textobj != NULL) {
                        ret.len = PyUnicode_GET_SIZE(textobj);
                        PyMem_RESIZE(ret.text, Py_UNICODE, ret.len);
                        memcpy(ret.text, PyUnicode_AS_UNICODE(textobj), ret.len * sizeof(Py_UNICODE));
                    }
                    Py_XDECREF(textobj);
                    return ret;
                }
                else {
                    ret.pos += 2;
                    return ret;
                }
            }
        }
        if (ret.len + 1 >= retlen) {
            retlen += SIZEINC;
            PyMem_RESIZE(ret.text, Py_UNICODE, retlen);
        }
        ret.text[ret.len ++] = text[ret.pos ++];
    }
    // unclosed rule
    if (ret.len + 2 >= retlen) {
        retlen += SIZEINC;
    }
    texttemp = PyMem_NEW(Py_UNICODE, retlen);
    texttemp[0] = TOKEN_A;
    texttemp[1] = TOKEN_B;
    memcpy(texttemp + 2, ret.text, ret.len * sizeof(Py_UNICODE));
    PyMem_DEL(ret.text);
    ret.len += 2;
    aret = auto_convert(texttemp, ret.len, 0);
    PyMem_DEL(texttemp);
    ret.text = aret.text;
    ret.len = aret.len;
    return ret;
}

static AutoConvertReturn auto_convert(Py_UNICODE *input, Py_ssize_t inputlen, int parserules)
{
    // Input string
    Py_ssize_t inputpos = 0; // input string position
    
    // Output string
    Py_ssize_t outputlen; // output string length
    Py_ssize_t outputlentest; // output length test, equals maxlen at first
    Py_ssize_t outputpos = 0; // output string position
    Py_UNICODE *output; // output string

    AutoConvertReturn ret;

    // Temp use
    int found; // a flag
    Py_ssize_t count_i;
    PyObject *single;
    PyObject *wordlens;
    Py_ssize_t lengthofwordlens;
    Py_ssize_t oriwordlen;
    PyObject *oriwordobj;
    PyObject *convwordobj;
    Py_UNICODE *convword;
    Py_ssize_t convwordlen;
    RuleReturn parsedtext;
    
    outputlentest = maxlen;

    // initiate output string
    output = PyMem_NEW(Py_UNICODE, inputlen);
    outputlen = inputlen;

    while (inputpos < inputlen) {
        // Parse rules
        if (parserules && inputpos + 1 < inputlen) {
            if (input[inputpos] == TOKEN_A && input[inputpos + 1] == TOKEN_B) {
                // token found
                parsedtext = recursive_convert_rule(input, inputpos + 2, inputlen, 1);
                inputpos = parsedtext.pos;
                outputlentest += parsedtext.len;
                if (outputlentest >= outputlen) {
                    outputlen += (parsedtext.len / SIZEINC + 1) * SIZEINC;
                    PyMem_RESIZE(output, Py_UNICODE, outputlen);
                }
                memcpy(output + outputpos, parsedtext.text, parsedtext.len * sizeof(Py_UNICODE));
                outputpos += parsedtext.len;
                PyMem_DEL(parsedtext.text);
                continue;
            }
        }
        // Check if current outputlen will be exceeded or not
        // if it will be, let's resize it to prevent this happen.
        if (outputlentest >= outputlen) {
            outputlen += SIZEINC;
            PyMem_RESIZE(output, Py_UNICODE, outputlen);
        }
        
        // retrieve a character from input for test
        single = PyUnicode_FromUnicode(input + inputpos, 1);
        wordlens = PyDict_GetItem(tables.quick_table, single); // check quicktable
        Py_XDECREF(single); // release single
        Py_XINCREF(wordlens);
        
        if (wordlens == NULL) {
            // find nothing in quicktable, just append the character to output
            
            output[outputpos ++] = input[inputpos ++];
            outputlentest ++;
        }
        
        else {
            lengthofwordlens = PyList_Size(wordlens);
            found = 0;
            
            // let's test words from longest to shortest (quicktable is sorted)
            for (count_i = 0; count_i < lengthofwordlens; count_i ++) {
                PyObject *wordlenobj = PyList_GetItem(wordlens, count_i);
                Py_XINCREF(wordlenobj);
                oriwordlen = PyInt_AsSsize_t(wordlenobj);
                Py_XDECREF(wordlenobj);
                oriwordobj = PyUnicode_FromUnicode(input + inputpos, (Py_ssize_t) oriwordlen);
                convwordobj = PyDict_GetItem(tables.conv_table, oriwordobj); // check convtable
                Py_XINCREF(convwordobj);
                Py_XDECREF(oriwordobj); // release oriwordobj
                if (convwordobj != NULL) {
                    if (PyUnicode_Check(convwordobj)) {
                        // find one! now append it to output
                        convword = PyUnicode_AS_UNICODE(convwordobj);
                        convwordlen = PyUnicode_GET_SIZE(convwordobj);
                        memcpy(output + outputpos, convword, convwordlen * sizeof(Py_UNICODE));
                        outputpos += convwordlen;
                        outputlentest += convwordlen;
                        inputpos += oriwordlen;
                        found = 1; // mark as found
                        break;
                    }
                }
                Py_XDECREF(convwordobj);
            }
            if (found == 0) {
                // find nothing, just append the character to output
                output[outputpos ++] = input[inputpos ++];
                outputlentest ++;
            }
        }
        Py_XDECREF(wordlens);
    }

    ret.text = output;
    ret.len = outputpos;
    return ret;
}

static PyObject *convert(PyObject *self, PyObject *args)
{
    // Input string
    Py_ssize_t inputlen; // input string length
    Py_UNICODE *input; // input string
    
    // Output string
    PyObject *ret; // output PyObject
    AutoConvertReturn out;
    
    // langconv.Converter instance
    PyObject *converter;
    
    // Hooks
    PyObject *hooksobj;
    
    //Parse rules?
    int parserules = 1;

    // Temp use
    PyObject *maxlenobj;
    
    // retrieve arguments from Python
    if (!PyArg_ParseTuple(args, "Ou#|i", &converter, &input, &inputlen, &parserules))
        return NULL;
    
    // retrieve arguments from converter instance
    Py_XINCREF(converter);
    tables.conv_table = PyObject_GetAttrString(converter, "convtable");
    tables.quick_table = PyObject_GetAttrString(converter, "quicktable");
    maxlenobj = PyObject_GetAttrString(converter, "maxlen");
    maxlen = PyInt_AsSsize_t(maxlenobj);
    Py_XDECREF(maxlenobj);

    // get hooks
    hooksobj = PyObject_GetAttrString(converter, "hooks");
    hooks.depth_exceed_msg = PyDict_GetItemString(hooksobj, "depth_exceed_msg");
    Py_XINCREF(hooks.depth_exceed_msg);
    hooks.rule_parser = PyDict_GetItemString(hooksobj, "rule_parser");
    Py_XINCREF(hooks.rule_parser);
    if (!PyCallable_Check(hooks.depth_exceed_msg)) {
        Py_XDECREF(hooks.depth_exceed_msg);
        hooks.depth_exceed_msg = NULL;
    }
    if (!PyCallable_Check(hooks.rule_parser)) {
        Py_XDECREF(hooks.rule_parser);
        hooks.rule_parser = NULL;
    }

    // call auto_convert()
    out = auto_convert(input, inputlen, parserules);

    ret = PyUnicode_FromUnicode(out.text, out.len);
    PyMem_DEL(out.text);
    Py_XDECREF(tables.conv_table);
    Py_XDECREF(tables.quick_table);
    Py_XDECREF(hooks.depth_exceed_msg);
    Py_XDECREF(hooks.rule_parser);
    Py_XDECREF(hooksobj);
    Py_XDECREF(converter);
    return ret;
}

static PyMethodDef converterMethods[] =
{
    {"convert", (PyCFunction) convert, METH_VARARGS, 
     "Use the specified variant to convert the content."},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC initconverter(void)
{
    Py_InitModule("converter", converterMethods);
}
